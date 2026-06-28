"""
Stratégie RSI Extreme (Mean Reversion court terme).

Logique :
  - RSI < 20 sur N bougies consécutives → BUY (marché survendu, rebond attendu)
  - RSI > 80 sur N bougies consécutives → SELL (marché suracheté, retour attendu)
  - Stop : 1.5 × ATR au-delà du point d'entrée
  - TP   : RR × stop_distance (défaut RR=1.5)
  - Exit anticipée : RSI revient à 50 (neutralité) → on prend les gains partiels

Pourquoi ça marche :
  BTC/ETH sont des actifs très liquides qui reviennent quasi toujours
  vers leur moyenne après des excès. Un RSI < 20 signifie une vente
  panique — les acheteurs rachètent rapidement.

Fréquence : 5-10 signaux/jour sur 15min, 2-5 sur 30min.
"""
from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
import numpy as np

from .config import StrategyConfig
from .indicators import atr as atr_fn


@dataclass
class RSISignal:
    direction: str   # "BUY" | "SELL"
    entry:     float
    stop:      float
    tp:        float
    rsi:       float
    confidence: float


@dataclass
class RSITrade:
    entry_idx:  int
    exit_idx:   int
    direction:  str
    entry:      float
    exit:       float
    pnl:        float
    exit_reason: str  # "tp" | "stop" | "rsi_mid"


def detect_rsi_signal(
    df: pd.DataFrame,
    i: int,
    rsi_low:  float = 20.0,
    rsi_high: float = 80.0,
    atr_mult: float = 1.5,
    rr:       float = 1.5,
    confirm_candles: int = 1,
) -> RSISignal | None:
    """Détecte un signal RSI extrême à la bougie i."""
    if i < confirm_candles or i >= len(df):
        return None

    rsi_now = float(df["rsi"].iloc[i])
    if pd.isna(rsi_now):
        return None

    # Vérifier que le RSI était extrême sur les N dernières bougies
    rsi_prev = [float(df["rsi"].iloc[i - k]) for k in range(1, confirm_candles + 1)]
    if pd.isna(rsi_prev[0]):
        return None

    close = float(df["close"].iloc[i])
    a     = float(atr_fn(df).iloc[i])
    if a <= 0:
        return None

    stop_dist = atr_mult * a

    # Signal BUY : RSI remonte depuis la zone de survente
    if rsi_prev[0] < rsi_low and rsi_now > rsi_prev[0]:
        entry = close
        stop  = entry - stop_dist
        tp    = entry + stop_dist * rr
        conf  = min(1.0, (rsi_low - rsi_prev[0]) / 10.0 * 0.5 + 0.5)
        return RSISignal("BUY", entry, stop, tp, rsi_now, conf)

    # Signal SELL : RSI redescend depuis la zone de surachat
    if rsi_prev[0] > rsi_high and rsi_now < rsi_prev[0]:
        entry = close
        stop  = entry + stop_dist
        tp    = entry - stop_dist * rr
        conf  = min(1.0, (rsi_prev[0] - rsi_high) / 10.0 * 0.5 + 0.5)
        return RSISignal("SELL", entry, stop, tp, rsi_now, conf)

    return None


def run_backtest_rsi(
    df: pd.DataFrame,
    cfg: StrategyConfig | None = None,
    rsi_low:  float = 20.0,
    rsi_high: float = 80.0,
    rr:       float = 1.5,
    atr_mult: float = 1.5,
    rsi_mid:  float = 50.0,   # sortie anticipée si RSI revient à 50
) -> dict:
    """Backtest RSI Extreme sur un DataFrame OHLCV."""
    cfg = cfg or StrategyConfig()

    # Calcul RSI et ATR manuellement (sans passer par add_indicators complet)
    from .indicators import add_indicators
    df_i = add_indicators(df, cfg)
    n    = len(df_i)

    equity       = cfg.capital
    equity_curve = [equity]
    trades: list[RSITrade] = []
    position = None
    pending  = None

    for j in range(20, n):
        bar = df_i.iloc[j]
        o   = float(bar["open"])
        h   = float(bar["high"])
        l_  = float(bar["low"])

        # Entrée en attente (signal de la bougie précédente)
        if position is None and pending is not None:
            sig = pending
            pending = None
            slip   = cfg.slippage
            entry  = o * (1 + slip) if sig.direction == "BUY" else o * (1 - slip)
            stop_d = abs(entry - sig.stop)
            if stop_d > 0:
                risk_amt = equity * (cfg.risk_percent / 100.0)
                qty = risk_amt / stop_d
                max_n = equity * cfg.max_notional_pct
                if qty * entry > max_n:
                    qty = max_n / entry
                fee_in = cfg.fee_rate * qty * entry
                tp = entry + stop_d * rr if sig.direction == "BUY" else entry - stop_d * rr
                position = {
                    "dir": sig.direction, "entry_idx": j, "entry": entry,
                    "qty": qty, "stop": sig.stop, "tp": tp, "fee": fee_in,
                }

        # Gestion position
        if position is not None:
            rsi_j     = float(df_i["rsi"].iloc[j]) if not pd.isna(df_i["rsi"].iloc[j]) else 50
            exit_price = exit_reason = None

            if position["dir"] == "BUY":
                if l_ <= position["stop"]:
                    exit_price, exit_reason = position["stop"], "stop"
                elif h >= position["tp"]:
                    exit_price, exit_reason = position["tp"], "tp"
                elif rsi_j >= rsi_mid and j > position["entry_idx"] + 1:
                    exit_price, exit_reason = float(bar["close"]), "rsi_mid"
            else:
                if h >= position["stop"]:
                    exit_price, exit_reason = position["stop"], "stop"
                elif l_ <= position["tp"]:
                    exit_price, exit_reason = position["tp"], "tp"
                elif rsi_j <= rsi_mid and j > position["entry_idx"] + 1:
                    exit_price, exit_reason = float(bar["close"]), "rsi_mid"

            if exit_price is not None:
                d_   = position["dir"]
                fill = exit_price * (1 - cfg.slippage) if d_ == "BUY" else exit_price * (1 + cfg.slippage)
                fee_out = cfg.fee_rate * position["qty"] * fill
                gross = ((fill - position["entry"]) * position["qty"] if d_ == "BUY"
                         else (position["entry"] - fill) * position["qty"])
                pnl = gross - position["fee"] - fee_out
                equity += pnl
                trades.append(RSITrade(position["entry_idx"], j, d_,
                                       position["entry"], fill, pnl, exit_reason))
                position = None

        # Chercher un nouveau signal
        if position is None and pending is None and j < n - 1:
            sig = detect_rsi_signal(df_i, j, rsi_low, rsi_high, atr_mult, rr)
            if sig is not None:
                pending = sig

        equity_curve.append(max(0, equity))

    return {
        "trades":       trades,
        "equity_curve": equity_curve,
        "metrics":      _metrics(trades, cfg.capital, equity_curve),
    }


def _metrics(trades: list[RSITrade], capital: float, equity_curve: list[float]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n_trades": 0, "message": "Aucun trade RSI généré."}

    pnls   = [t.pnl for t in trades]
    wins   = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    net    = sum(pnls)
    gp     = sum(wins)
    gl     = abs(sum(losses))

    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        peak   = max(peak, v)
        max_dd = max(max_dd, peak - v)

    exits = {}
    for t in trades:
        exits[t.exit_reason] = exits.get(t.exit_reason, 0) + 1

    return {
        "n_trades":         n,
        "win_rate":         round(len(wins) / n * 100, 2),
        "net_profit":       round(net, 2),
        "return_pct":       round(net / capital * 100, 2),
        "profit_factor":    round(gp / gl, 2) if gl > 0 else float("inf"),
        "avg_win":          round(gp / len(wins), 4) if wins else 0,
        "avg_loss":         round(-gl / len(losses), 4) if losses else 0,
        "expectancy":       round((len(wins)/n) * (gp/len(wins) if wins else 0)
                                  + (len(losses)/n) * (-gl/len(losses) if losses else 0), 4),
        "max_drawdown_pct": round(max_dd / capital * 100, 2),
        "final_equity":     round(equity_curve[-1], 2),
        "exits":            exits,
        "trades_per_day":   round(n / max(1, len(equity_curve) / (24 * 4)), 1),
    }


def print_report_rsi(result: dict, label: str = "RSI EXTREME") -> None:
    m = result["metrics"]
    print("=" * 52)
    print(f"📊 {label} — RÉSULTAT")
    print("=" * 52)
    if m.get("n_trades", 0) == 0:
        print(m.get("message"))
        return
    rows = [
        ("Nombre de trades",      m["n_trades"]),
        ("Trades / jour (moy.)",  m["trades_per_day"]),
        ("Taux de réussite (%)",  m["win_rate"]),
        ("Profit net ($)",        m["net_profit"]),
        ("Rendement (%)",         m["return_pct"]),
        ("Profit factor",         m["profit_factor"]),
        ("Espérance / trade ($)", m["expectancy"]),
        ("Gain moyen ($)",        m["avg_win"]),
        ("Perte moyenne ($)",     m["avg_loss"]),
        ("Drawdown max (%)",      m["max_drawdown_pct"]),
        ("Équité finale ($)",     m["final_equity"]),
    ]
    for lbl, val in rows:
        print(f"   {lbl:<26}: {val}")
    exits = m.get("exits", {})
    print(f"   {'Sorties':<26}: TP={exits.get('tp',0)} | SL={exits.get('stop',0)} | RSI mid={exits.get('rsi_mid',0)}")
    print("=" * 52)
