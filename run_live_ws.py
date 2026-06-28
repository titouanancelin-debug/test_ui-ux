#!/usr/bin/env python3
"""
Bot live TEMPS RÉEL via websocket Binance.

Au lieu de poller l'API toutes les heures, on reçoit chaque chandelier
clôturé instantanément via le stream kline Binance.

Avantages vs run_live.py (polling) :
  - Signal déclenché dans la seconde qui suit la clôture de la bougie
  - Aucun signal raté entre deux cycles
  - Moins d'appels API → pas de rate limit

Usage :
    python run_live_ws.py                  # alertes Telegram uniquement
    python run_live_ws.py --execute        # + ordres Alpaca Paper
    python run_live_ws.py --symbols BTCUSDT LINKUSDT --intervals 4h 2h
"""
from __future__ import annotations

import argparse
import json
import threading
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone

import websocket
import pandas as pd

from scalping.config import StrategyConfig, AlpacaConfig
from scalping.data import get_candles_binance
from scalping.strategy import prepare, generate_signal
from scalping.risk import build_trade_plan
from scalping.mean_reversion import detect_mr_signal
from scalping.levels import detect_levels
from scalping.indicators import add_indicators
from scalping.notifier import notify_signal, notify_order, notify_error, notify_startup
from scalping.trade_logger import log_signal
from scalping.market_regime import funding_signal_adjustment, CorrelationManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stratégies surveillées en websocket (crypto Binance uniquement)
# ---------------------------------------------------------------------------
WS_STRATEGIES = [
    {"data_sym": "BTCUSDT",  "alpaca_sym": "BTC/USD",  "interval": "4h"},
    {"data_sym": "SOLUSDT",  "alpaca_sym": "SOL/USD",  "interval": "4h"},
    {"data_sym": "SOLUSDT",  "alpaca_sym": "SOL/USD",  "interval": "1h"},
    {"data_sym": "LINKUSDT", "alpaca_sym": "LINK/USD", "interval": "2h"},
    {"data_sym": "AAVEUSDT", "alpaca_sym": "AAVE/USD", "interval": "2h"},
    {"data_sym": "ARBUSDT",  "alpaca_sym": "ARB/USD",  "interval": "1h"},
    {"data_sym": "INJUSDT",  "alpaca_sym": None,        "interval": "2h"},
    {"data_sym": "OPUSDT",   "alpaca_sym": None,        "interval": "2h"},
    {"data_sym": "SUIUSDT",  "alpaca_sym": None,        "interval": "4h"},
]


def make_cfg(capital: float) -> StrategyConfig:
    cfg = StrategyConfig()
    cfg.capital          = capital
    cfg.use_mtf          = True
    cfg.use_candle_patterns  = False
    cfg.use_chart_patterns   = False
    cfg.use_ma200_filter     = False
    cfg.require_ema_trend    = False
    cfg.require_macd_confirm = False
    cfg.rr_ratio         = 2.5
    cfg.fee_rate         = 0.0005
    cfg.slippage         = 0.0002
    cfg.min_confidence   = 0.6
    cfg.trailing_pct     = None
    return cfg


class BinanceWSBot:
    """Bot temps réel sur websocket Binance kline."""

    def __init__(self, execute: bool = False):
        self.execute   = execute
        self.broker    = None
        self.capital   = 200.0
        self.corr_mgr  = CorrelationManager()
        self.lock      = threading.Lock()

        # Buffers de chandeliers par (symbol, interval)
        self._buffers: dict[tuple, pd.DataFrame] = {}
        self._ws: websocket.WebSocketApp | None = None

        if execute:
            from scalping.broker_alpaca import AlpacaClient
            acfg = AlpacaConfig()
            if acfg.configured:
                self.broker  = AlpacaClient(acfg)
                self.capital = self.broker.get_equity()
                logger.info(f"Alpaca connecté — équité : {self.capital:,.2f}$")
            else:
                logger.warning("Clés Alpaca absentes — mode alerte seule")

    def _preload_buffers(self) -> None:
        """Charge l'historique initial pour que les indicateurs soient disponibles."""
        loaded = set()
        for s in WS_STRATEGIES:
            key = (s["data_sym"], s["interval"])
            if key in loaded:
                continue
            logger.info(f"Pré-chargement {s['data_sym']} {s['interval']}...")
            df = get_candles_binance(s["data_sym"], s["interval"], limit=300)
            if not df.empty:
                self._buffers[key] = df
            loaded.add(key)

    def _on_kline_closed(self, symbol: str, interval: str, kline: dict) -> None:
        """Appelé à chaque clôture de bougie. Thread-safe."""
        key = (symbol, interval)
        new_row = pd.DataFrame([{
            "time":   pd.Timestamp(kline["t"], unit="ms", tz="UTC"),
            "open":   float(kline["o"]),
            "high":   float(kline["h"]),
            "low":    float(kline["l"]),
            "close":  float(kline["c"]),
            "volume": float(kline["v"]),
        }])

        with self.lock:
            if key not in self._buffers:
                return
            df = pd.concat([self._buffers[key], new_row], ignore_index=True).tail(300)
            self._buffers[key] = df

        # Analyser dans un thread séparé pour ne pas bloquer le websocket
        strat = next((s for s in WS_STRATEGIES
                      if s["data_sym"] == symbol and s["interval"] == interval), None)
        if strat:
            threading.Thread(target=self._analyze, args=(strat, df.copy()), daemon=True).start()

    def _analyze(self, strat: dict, df: pd.DataFrame) -> None:
        data_sym = strat["data_sym"]
        a_sym    = strat.get("alpaca_sym")
        interval = strat["interval"]

        if self.broker:
            self.capital = self.broker.get_equity()
        cfg = make_cfg(self.capital)

        df = df.iloc[:-1].reset_index(drop=True)
        if len(df) < 60:
            return

        prep = prepare(df, cfg)
        sig  = generate_signal(prep, len(prep.df) - 1, cfg)
        if sig is None:
            return

        # Funding rate
        fr_mult, fr_msg = funding_signal_adjustment(data_sym, sig.direction)
        adj_conf = sig.confidence * fr_mult
        if adj_conf < cfg.min_confidence:
            logger.info(f"[{data_sym} {interval}] Signal annulé par funding ({adj_conf:.0%})")
            return

        # Corrélation
        adj_risk, corr_msg = self.corr_mgr.adjusted_risk(data_sym, cfg.risk_percent)
        if adj_risk <= 0:
            logger.info(f"[{data_sym} {interval}] Signal annulé par corrélation")
            return
        cfg.risk_percent = adj_risk

        plan = build_trade_plan(sig.direction, sig.entry, sig.stop, cfg, sig.levels, capital=self.capital)
        if plan is None:
            return

        now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        logger.info(f"🎯 SIGNAL {sig.direction} [{data_sym} {interval}] | conf {adj_conf:.0%} | "
                    f"entrée {plan.entry:.4f} SL {plan.stop:.4f} TP {plan.take_profit:.4f}")
        if fr_msg:
            logger.info(f"   💹 {fr_msg}")
        if corr_msg:
            logger.info(f"   📊 {corr_msg}")

        executed = False
        if self.broker and a_sym:
            if not self.broker.has_position(a_sym):
                res = self.broker.submit_bracket(a_sym, sig.direction, plan.qty, plan.stop, plan.take_profit)
                if res.get("ok"):
                    executed = True
                    notify_order(a_sym, sig.direction, plan.qty, plan.entry, plan.stop, plan.take_profit)
                else:
                    notify_error(a_sym, res.get("error", "inconnu"))

        notify_signal(data_sym, interval, sig.direction, plan.entry, plan.stop,
                      plan.take_profit, adj_conf, sig.reasons)
        log_signal(data_sym, interval, "breakout", sig.direction, plan.entry,
                   plan.stop, plan.take_profit, adj_conf, executed, self.capital)

    def _build_ws_url(self) -> str:
        streams = []
        seen = set()
        for s in WS_STRATEGIES:
            sym = s["data_sym"].lower()
            iv  = s["interval"]
            key = f"{sym}@kline_{iv}"
            if key not in seen:
                streams.append(key)
                seen.add(key)
        return "wss://stream.binance.com:9443/stream?streams=" + "/".join(streams)

    def _on_message(self, ws, message: str) -> None:
        try:
            data   = json.loads(message)
            stream = data.get("stream", "")
            kline  = data["data"]["k"]
            if not kline["x"]:   # x=True → bougie clôturée
                return
            # stream = "btcusdt@kline_4h"
            parts    = stream.split("@kline_")
            symbol   = parts[0].upper()
            interval = parts[1]
            self._on_kline_closed(symbol, interval, kline)
        except Exception as e:
            logger.error(f"WS message error: {e}")

    def _on_error(self, ws, error) -> None:
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws, code, msg) -> None:
        logger.warning(f"WebSocket fermé ({code}). Reconnexion dans 10s...")
        time.sleep(10)
        self.run()

    def _on_open(self, ws) -> None:
        logger.info("✅ WebSocket Binance connecté")

    def run(self) -> None:
        self._preload_buffers()
        url = self._build_ws_url()
        logger.info(f"Connexion WS : {len(set(s['data_sym'] for s in WS_STRATEGIES))} paires")

        mode = "EXÉCUTION (paper)" if self.broker else "ALERTE seulement"
        notify_startup(len(WS_STRATEGIES), self.capital, mode + " [WEBSOCKET]")

        self._ws = websocket.WebSocketApp(
            url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )
        self._ws.run_forever(ping_interval=30, ping_timeout=10)


def main():
    p = argparse.ArgumentParser(description="Bot live websocket Binance")
    p.add_argument("--execute", action="store_true", help="Envoyer des ordres Alpaca Paper")
    args = p.parse_args()

    print("=" * 60)
    print("⚡ LIVE WEBSOCKET — Signaux en temps réel")
    print("   Pas de polling — chaque bougie clôturée = analyse immédiate")
    print("=" * 60)

    bot = BinanceWSBot(execute=args.execute)
    bot.run()


if __name__ == "__main__":
    main()
