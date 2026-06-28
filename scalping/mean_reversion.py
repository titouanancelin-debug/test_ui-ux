"""
Stratégie Mean Reversion sur niveaux S/R.

Logique (inverse de la cassure) :
  1. Détecter les niveaux S/R forts (plusieurs touches).
  2. Quand le prix touche un niveau et montre un signal de REJET
     (bougie de rejet : longue mèche vers le niveau, corps dans la direction
     opposée), entrer dans la direction du rebond.
  3. Stop juste au-delà du niveau touché.
  4. TP = RR × stop_distance (RR plus faible que breakout : 1.5 suffit
     car le win rate est plus élevé ~45-55%).

Pourquoi ça marche sur forex :
  Le forex est en range ~70% du temps. Les niveaux S/R testés plusieurs fois
  ont tendance à TENIR, pas à être cassés. C'est l'inverse de la crypto.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from .config import StrategyConfig
from .indicators import atr as atr_fn, add_indicators
from .levels import detect_levels, Level


@dataclass
class MRSignal:
    direction: str    # "BUY" (rebond sur support) | "SELL" (rebond sur résistance)
    entry: float
    stop: float
    tp: float
    level: float
    confidence: float


@dataclass
class MRTrade:
    entry_idx: int
    exit_idx: int
    direction: str
    entry: float
    exit: float
    qty: float
    pnl: float
    exit_reason: str


def detect_mr_signal(
    df: pd.DataFrame,
    i: int,
    levels: list[Level],
    cfg: StrategyConfig,
    rr: float = 1.5,
    touch_atr: float = 0.3,
    reject_body_pct: float = 0.35,
    min_wick_pct: float = 0.40,
) -> MRSignal | None:
    """Détecte un signal de rejet sur un niveau S/R à la bougie i."""
    if i < 5 or i >= len(df):
        return None

    row   = df.iloc[i]
    o     = float(row["open"])
    h     = float(row["high"])
    l     = float(row["low"])
    c     = float(row["close"])
    rng   = h - l
    if rng <= 0:
        return None

    body  = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l

    a = float(atr_fn(df).iloc[i])
    if a <= 0:
        return None
    tol = touch_atr * a

    # RSI garde-fou
    rsi_v = float(row.get("rsi", 50))

    # --- Rejet haussier sur support ---
    for lv in [l_ for l_ in levels if l_.kind == "support" and l_.touches >= 2]:
        touch = l <= lv.price + tol and l >= lv.price - tol
        wick_ok = lower >= min_wick_pct * rng      # longue mèche basse
        body_ok = body >= reject_body_pct * rng    # corps significatif
        bull_body = c > o                          # corps haussier
        if touch and wick_ok and body_ok and bull_body and rsi_v < 65:
            entry = c
            stop  = lv.price - 0.5 * a
            if stop >= entry:
                continue
            tp = entry + abs(entry - stop) * rr
            return MRSignal("BUY", entry, stop, tp, lv.price, min(1.0, lv.touches * 0.2))

    # --- Rejet baissier sur résistance ---
    for lv in [l_ for l_ in levels if l_.kind == "resistance" and l_.touches >= 2]:
        touch = h >= lv.price - tol and h <= lv.price + tol
        wick_ok = upper >= min_wick_pct * rng      # longue mèche haute
        body_ok = body >= reject_body_pct * rng
        bear_body = c < o                          # corps baissier
        if touch and wick_ok and body_ok and bear_body and rsi_v > 35:
            entry = c
            stop  = lv.price + 0.5 * a
            if stop <= entry:
                continue
            tp = entry - abs(stop - entry) * rr
            return MRSignal("SELL", entry, stop, tp, lv.price, min(1.0, lv.touches * 0.2))

    return None


def run_backtest_mr(df: pd.DataFrame, cfg: StrategyConfig | None = None, rr: float = 1.5) -> dict:
    """Backtest Mean Reversion sur un DataFrame OHLCV."""
    cfg = cfg or StrategyConfig()

    df_ind = add_indicators(df, cfg)
    n      = len(df_ind)
    start  = max(cfg.ema_slow, cfg.sr_lookback // 4, 30)

    equity       = cfg.capital
    equity_curve = [equity]
    trades: list[MRTrade] = []
    position = None
    pending  = None

    for j in range(start, n):
        bar = df_ind.iloc[j]
        o   = float(bar["open"])
        h   = float(bar["high"])
        l_  = float(bar["low"])

        # Entrée en attente
        if position is None and pending is not None:
            sig = pending
            pending = None
            slip  = cfg.slippage
            entry = o * (1 + slip) if sig.direction == "BUY" else o * (1 - slip)
            stop_dist = abs(entry - sig.stop)
            if stop_dist > 0:
                risk_amount = equity * (cfg.risk_percent / 100.0)
                qty = risk_amount / stop_dist
                max_notional = equity * cfg.max_notional_pct
                if qty * entry > max_notional:
                    qty = max_notional / entry
                entry_fee = cfg.fee_rate * qty * entry
                tp = entry + abs(entry - sig.stop) * rr if sig.direction == "BUY" else entry - abs(sig.stop - entry) * rr
                position = {"dir": sig.direction, "entry_idx": j, "entry": entry,
                            "qty": qty, "stop": sig.stop, "tp": tp, "fee_paid": entry_fee}

        # Gestion de la position
        if position is not None:
            exit_price = exit_reason = None
            if position["dir"] == "BUY":
                if l_ <= position["stop"]:
                    exit_price, exit_reason = position["stop"], "stop"
                elif h >= position["tp"]:
                    exit_price, exit_reason = position["tp"], "tp"
            else:
                if h >= position["stop"]:
                    exit_price, exit_reason = position["stop"], "stop"
                elif l_ <= position["tp"]:
                    exit_price, exit_reason = position["tp"], "tp"

            if exit_price is not None:
                d_   = position["dir"]
                fill = exit_price * (1 - cfg.slippage) if d_ == "BUY" else exit_price * (1 + cfg.slippage)
                exit_fee = cfg.fee_rate * position["qty"] * fill
                gross = ((fill - position["entry"]) * position["qty"] if d_ == "BUY"
                         else (position["entry"] - fill) * position["qty"])
                pnl = gross - position["fee_paid"] - exit_fee
                equity += pnl
                trades.append(MRTrade(position["entry_idx"], j, d_,
                                      position["entry"], fill, position["qty"], pnl, exit_reason))
                position = None

        # Chercher un nouveau signal
        if position is None and pending is None and j < n - 1:
            levels = detect_levels(df_ind.iloc[:j+1], cfg.sr_lookback, cfg.pivot_window, cfg.sr_cluster_atr)
            sig = detect_mr_signal(df_ind, j, levels, cfg, rr=rr)
            if sig is not None:
                pending = sig

        equity_curve.append(equity)

    return {
        "trades": trades,
        "equity_curve": equity_curve,
        "metrics": _metrics_mr(trades, cfg.capital, equity_curve),
    }


def _metrics_mr(trades: list[MRTrade], capital: float, equity_curve: list[float]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n_trades": 0, "message": "Aucun trade Mean Reversion généré."}

    pnls   = [t.pnl for t in trades]
    wins   = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    net    = sum(pnls)
    gp     = sum(wins)
    gl     = abs(sum(losses))

    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        max_dd = max(max_dd, peak - v)

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
    }


def print_report_mr(result: dict, label: str = "MEAN REVERSION") -> None:
    m = result["metrics"]
    print("=" * 50)
    print(f"📊 {label} — RÉSULTAT")
    print("=" * 50)
    if m.get("n_trades", 0) == 0:
        print(m.get("message"))
        return
    labels = {
        "n_trades":         "Nombre de trades",
        "win_rate":         "Taux de réussite (%)",
        "net_profit":       "Profit net ($)",
        "return_pct":       "Rendement (%)",
        "profit_factor":    "Profit factor",
        "expectancy":       "Espérance / trade ($)",
        "avg_win":          "Gain moyen ($)",
        "avg_loss":         "Perte moyenne ($)",
        "max_drawdown_pct": "Drawdown max (%)",
        "final_equity":     "Équité finale ($)",
    }
    for k, label_ in labels.items():
        print(f"   {label_:<28}: {m[k]}")
    print("=" * 50)
