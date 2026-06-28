#!/usr/bin/env python3
"""
Boucle LIVE multi-stratégie avec capital progressif.

Stratégies actives (validées — win rate > seuil de rentabilité + 3%) :
  Breakout S/R (RR=2.5, seuil 33%) :
    - BTC/USD  4h  → 33% win rate  ✅
    - SOL/USD  4h  → 36% win rate  ✅
    - ATOM/USD 1h  → 39% win rate  ✅
    - MSFT     1h  → 40% win rate  ✅
    - TSLA     1h  → 36% win rate  ✅
    - AMZN     1h  → 36% win rate  ✅
  Mean Reversion (RR=1.5, seuil 44%) :
    - Or/GC=F  1h  → 53% win rate  ✅

Capital progressif : l'équité réelle du compte Alpaca est récupérée à chaque
cycle — les positions grossissent automatiquement avec les gains.

Modes :
  - Alerte seule (défaut) : affiche les signaux sans envoyer d'ordre.
  - Exécution (--execute)  : ordres bracket sur Alpaca Paper.

Exemples :
    python run_live.py --once
    python run_live.py --execute
"""
from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone

from scalping.config import StrategyConfig, AlpacaConfig
from scalping.data import get_candles_binance, get_candles_alpaca_stocks
from scalping.strategy import prepare, generate_signal
from scalping.risk import build_trade_plan
from scalping.mean_reversion import detect_mr_signal, run_backtest_mr
from scalping.levels import detect_levels
from scalping.indicators import add_indicators
from scalping.notifier import notify_signal, notify_order, notify_error, notify_startup, notify_equity
from scalping.trade_logger import log_signal

# ---------------------------------------------------------------------------
# Définition des stratégies validées en backtest sur 2+ ans
# ---------------------------------------------------------------------------
# source : "binance" | "alpaca_stocks" | "yfinance_mr"
# strategy_type: "breakout" (défaut) | "mr" (Mean Reversion)
# alpaca_sym : None = pas d'exécution Alpaca (alerte seule)
STRATEGIES = [
    # ── Crypto 4h sur Alpaca — tendances longues (BTC/SOL marchent mieux en 4h) ──
    {"source": "binance", "data_sym": "BTCUSDT", "alpaca_sym": "BTC/USD", "interval": "4h", "interval_sec": 4*3600, "limit": 500, "strategy_type": "breakout"},  # 36% WR, +2.6%
    {"source": "binance", "data_sym": "SOLUSDT", "alpaca_sym": "SOL/USD", "interval": "4h", "interval_sec": 4*3600, "limit": 500, "strategy_type": "breakout"},  # 37% WR, +5.3%
    # ── Crypto 2h sur Alpaca — 2x plus de signaux, validés en 2h ─────────
    {"source": "binance", "data_sym": "LINKUSDT", "alpaca_sym": "LINK/USD", "interval": "2h", "interval_sec": 2*3600, "limit": 500, "strategy_type": "breakout"},  # 35% WR, +23%
    {"source": "binance", "data_sym": "AAVEUSDT", "alpaca_sym": "AAVE/USD", "interval": "2h", "interval_sec": 2*3600, "limit": 500, "strategy_type": "breakout"},  # 34% WR, +16%
    # ── Crypto 2h — alerte Telegram seule (pas dispo sur Alpaca) ──────────
    {"source": "binance", "data_sym": "INJUSDT", "alpaca_sym": None, "interval": "2h", "interval_sec": 2*3600, "limit": 500, "strategy_type": "breakout"},  # 32% WR, +5%
    {"source": "binance", "data_sym": "OPUSDT",  "alpaca_sym": None, "interval": "2h", "interval_sec": 2*3600, "limit": 500, "strategy_type": "breakout"},  # 37% WR, +39%
    {"source": "binance", "data_sym": "SUIUSDT", "alpaca_sym": None, "interval": "4h", "interval_sec": 4*3600, "limit": 500, "strategy_type": "breakout"},  # 34% WR, +14% (4h validé)
    # ── Stocks US 1h (marché ouvert 09:30-16:00 ET) ───────────────────────
    {"source": "alpaca_stocks", "data_sym": "MSFT", "alpaca_sym": "MSFT", "interval": "1Hour", "interval_sec": 3600, "limit": 500, "strategy_type": "breakout"},
    {"source": "alpaca_stocks", "data_sym": "TSLA", "alpaca_sym": "TSLA", "interval": "1Hour", "interval_sec": 3600, "limit": 500, "strategy_type": "breakout"},
    {"source": "alpaca_stocks", "data_sym": "AMZN", "alpaca_sym": "AMZN", "interval": "1Hour", "interval_sec": 3600, "limit": 500, "strategy_type": "breakout"},
    # ── Or 1h — Mean Reversion (53% WR ✅, alerte seule) ──────────────────
    {"source": "yfinance_mr", "data_sym": "GC=F", "alpaca_sym": None, "interval": "1h", "interval_sec": 3600, "limit": 500, "strategy_type": "mr", "mr_rr": 1.5},
]


def make_cfg(capital: float) -> StrategyConfig:
    """Crée la config stratégie avec le capital courant du compte."""
    cfg = StrategyConfig()
    cfg.capital          = capital
    cfg.use_mtf          = True
    cfg.use_candle_patterns  = False
    cfg.use_chart_patterns   = False
    cfg.use_ma200_filter     = False
    cfg.require_ema_trend    = False
    cfg.require_macd_confirm = False
    cfg.rr_ratio         = 2.5
    cfg.fee_rate         = 0.0005   # ordres maker
    cfg.slippage         = 0.0002
    cfg.min_confidence   = 0.6
    cfg.trailing_pct     = None
    return cfg


def _fetch(strat: dict) -> "pd.DataFrame":
    import pandas as pd
    from scalping.data import get_candles_yf
    src      = strat["source"]
    data_sym = strat["data_sym"]
    interval = strat["interval"]
    limit    = strat["limit"]
    if src == "binance":
        return get_candles_binance(data_sym, interval, limit)
    elif src == "alpaca_stocks":
        df = get_candles_alpaca_stocks(data_sym, interval, limit)
        if df.empty:
            df = get_candles_yf(data_sym, "1h", period="60d")
        return df
    elif src == "yfinance_mr":
        return get_candles_yf(data_sym, interval, period="90d")
    return pd.DataFrame()


def analyze_once(strat: dict, cfg: StrategyConfig, broker=None) -> None:
    data_sym      = strat["data_sym"]
    a_sym         = strat.get("alpaca_sym")
    interval      = strat["interval"]
    strategy_type = strat.get("strategy_type", "breakout")

    df = _fetch(strat)
    if df is None or df.empty or len(df) < 120:
        print(f"  ⚠️  [{data_sym} {interval}] données insuffisantes")
        return

    # Retirer la bougie en cours (non clôturée) — anti-repaint.
    df = df.iloc[:-1].reset_index(drop=True)

    # ------------------------------------------------------------------ #
    #  Branche Mean Reversion (ex : Or GC=F)                              #
    # ------------------------------------------------------------------ #
    if strategy_type == "mr":
        df_ind = add_indicators(df, cfg)
        i      = len(df_ind) - 1
        levels = detect_levels(df_ind, cfg.sr_lookback, cfg.pivot_window, cfg.sr_cluster_atr)
        rr     = strat.get("mr_rr", 1.5)
        sig    = detect_mr_signal(df_ind, i, levels, cfg, rr=rr)

        if sig is None:
            last_c = df["close"].iloc[-1]
            print(f"  🔍 [{data_sym} {interval}] pas de signal MR (clôture {last_c:.2f})")
            return

        print(f"\n  🎯 SIGNAL MR {sig.direction} [{data_sym} {interval}] | confiance {sig.confidence:.0%}")
        print(f"     Niveau S/R : {sig.level:.2f} | Entrée ~{sig.entry:.2f} | SL {sig.stop:.2f} | TP {sig.tp:.2f}")
        risk_amount = cfg.capital * (cfg.risk_percent / 100.0)
        stop_dist   = abs(sig.entry - sig.stop)
        qty = risk_amount / stop_dist if stop_dist > 0 else 0
        print(f"     Risque {risk_amount:.2f}$ | Qty ~{qty:.4f}")
        if a_sym is None:
            print("     ℹ️  Alerte seule (pas d'exécution Alpaca pour cet actif)")

        notify_signal(data_sym, interval, sig.direction, sig.entry, sig.stop, sig.tp,
                      sig.confidence, [f"Niveau {sig.level:.2f}"], strategy="mr")
        log_signal(data_sym, interval, "mr", sig.direction, sig.entry, sig.stop, sig.tp,
                   sig.confidence, executed=False, equity=cfg.capital)
        return

    # ------------------------------------------------------------------ #
    #  Branche Breakout S/R (crypto + stocks)                             #
    # ------------------------------------------------------------------ #
    prep = prepare(df, cfg)
    sig  = generate_signal(prep, len(prep.df) - 1, cfg)

    if sig is None:
        print(f"  🔍 [{data_sym} {interval}] pas de signal (clôture {df['close'].iloc[-1]:.4f})")
        return

    plan = build_trade_plan(sig.direction, sig.entry, sig.stop, cfg, sig.levels, capital=cfg.capital)
    if plan is None:
        print(f"  🔍 [{data_sym} {interval}] signal {sig.direction} rejeté (plan invalide)")
        return

    print(f"\n  🎯 SIGNAL {sig.direction} [{data_sym} {interval}] | confiance {sig.confidence:.0%}")
    print(f"     Entrée ~{plan.entry:.4f} | SL {plan.stop:.4f} | TP {plan.take_profit:.4f}")
    print(f"     Qty {plan.qty:.6f} | Notionnel {plan.notional:.2f}$ | Risque {plan.risk_amount:.2f}$")
    print("     Raisons : " + " ; ".join(sig.reasons))

    executed = False
    if broker is not None and a_sym is not None:
        if broker.has_position(a_sym):
            print(f"     ⏭️  Position déjà ouverte sur {a_sym}, on n'empile pas.")
        else:
            res = broker.submit_bracket(a_sym, sig.direction, plan.qty, plan.stop, plan.take_profit)
            if res.get("ok"):
                executed = True
                kind = "bracket (OCO)" if res.get("bracket") else "marché simple"
                print(f"     ✅ Ordre {kind} envoyé sur {a_sym}")
                notify_order(a_sym, sig.direction, plan.qty, plan.entry, plan.stop, plan.take_profit, kind)
                if res.get("warning"):
                    print(f"     ⚠️  Bracket refusé ({res['warning']}) → surveille SL/TP manuellement")
            else:
                err = res.get("error", "inconnu")
                print(f"     ❌ Ordre refusé : {err}")
                notify_error(a_sym, err)

    notify_signal(data_sym, interval, sig.direction, plan.entry, plan.stop, plan.take_profit,
                  sig.confidence, sig.reasons, strategy="breakout")
    log_signal(data_sym, interval, "breakout", sig.direction, plan.entry, plan.stop,
               plan.take_profit, sig.confidence, executed=executed, equity=cfg.capital)


def main():
    p = argparse.ArgumentParser(description="Live multi-stratégie — capital progressif")
    p.add_argument("--once",    action="store_true", help="Une seule passe puis sortie")
    p.add_argument("--execute", action="store_true", help="Envoyer des ordres Alpaca Paper")
    p.add_argument("--loop-interval", type=int, default=3600,
                   help="Secondes entre chaque cycle complet (défaut 3600 = 1h)")
    args = p.parse_args()

    broker  = None
    capital = 200.0   # fallback si pas de broker

    if args.execute:
        from scalping.broker_alpaca import AlpacaClient
        acfg = AlpacaConfig()
        if not acfg.configured:
            print("❌ --execute demandé mais clés Alpaca absentes (voir .env.example).")
            return
        broker  = AlpacaClient(acfg)
        capital = broker.get_equity()
        print(f"✅ Alpaca connecté | équité : {capital:,.2f}$")

    mode = "EXÉCUTION (paper)" if broker else "ALERTE seulement"
    print("=" * 60)
    print(f"🚀 LIVE SCALPING MULTI-STRATÉGIE — {mode}")
    print(f"   BTC | SOL | LINK | INJ | OP | SUI (4h) | MSFT/TSLA/AMZN (1h) | Or MR (1h)")
    print(f"   Capital initial : {capital:,.2f}$")
    print("=" * 60)
    notify_startup(len(STRATEGIES), capital, mode)

    # Timestamp du dernier passage par stratégie (index).
    last_run: dict[int, float] = {}

    while True:
        now_ts  = time.time()
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        # Mise à jour de l'équité réelle à chaque cycle.
        if broker is not None:
            capital = broker.get_equity()

        cfg = make_cfg(capital)

        print(f"\n⏰ [{now_str}] capital {capital:,.2f}$ — analyse...")

        for idx, strat in enumerate(STRATEGIES):
            sec  = strat["interval_sec"]
            last = last_run.get(idx, 0)
            # Déclencher si le délai de cet actif est écoulé (±60 s de marge).
            if args.once or now_ts - last >= sec - 60:
                last_run[idx] = now_ts
                try:
                    analyze_once(strat, cfg, broker)
                except Exception as e:
                    print(f"  ⚠️  Erreur [{strat['data_sym']}] : {e}")
                time.sleep(1)

        if args.once:
            break

        print(f"\n💤 prochain cycle dans {args.loop_interval // 60} min...")
        time.sleep(args.loop_interval)


if __name__ == "__main__":
    main()
