"""
Stratégie London Breakout.

Logique :
  1. Calculer le range de la session asiatique (00:00 - 08:00 UTC).
  2. À l'ouverture de Londres (08:00 UTC), entrer sur la cassure du range :
       - Cassure haussière : clôture > Asian High + buffer
       - Cassure baissière : clôture < Asian Low  - buffer
  3. Stop à l'extrémité opposée du range.
  4. TP = RR × stop_distance.

Pourquoi ça marche :
  La session asiatique est peu volatile et crée un range compact.
  Les institutions européennes et américaines prennent position à l'ouverture
  de Londres, ce qui génère un mouvement directionnel fort et fiable.

Utilisation :
  from scalping.london_breakout import run_backtest_lb, print_report_lb
  result = run_backtest_lb(df, cfg)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from .config import StrategyConfig


@dataclass
class LBTrade:
    date: str
    direction: str
    entry: float
    stop: float
    tp: float
    exit_price: float
    pnl: float
    exit_reason: str   # "tp" | "stop" | "eod"


def _asian_range(day_df: pd.DataFrame) -> tuple[float, float] | None:
    """High et Low de la session asiatique (00:00-08:00 UTC) du jour."""
    asian = day_df[day_df["time"].dt.hour < 8]
    if len(asian) < 3:
        return None
    return float(asian["high"].max()), float(asian["low"].min())


def run_backtest_lb(df: pd.DataFrame, cfg: StrategyConfig | None = None) -> dict:
    """Backtest London Breakout sur un DataFrame 1h OHLCV (index UTC)."""
    cfg = cfg or StrategyConfig()

    # Paramètres LB
    buffer_pct   = 0.0010   # 0.10% au-delà du range pour confirmer la cassure
    rr            = cfg.rr_ratio
    fee_rate      = cfg.fee_rate
    slippage      = cfg.slippage
    risk_pct      = cfg.risk_percent / 100.0

    if "time" not in df.columns:
        df = df.reset_index()
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)

    equity  = cfg.capital
    equity_curve = [equity]
    trades: list[LBTrade] = []

    # Grouper par date (UTC)
    df["_date"] = df["time"].dt.date
    dates = sorted(df["_date"].unique())

    for date in dates:
        day_df = df[df["_date"] == date].copy()

        result = _asian_range(day_df)
        if result is None:
            continue
        asian_high, asian_low = result
        range_size = asian_high - asian_low
        if range_size <= 0:
            continue

        buf = buffer_pct * ((asian_high + asian_low) / 2)

        # Bougies de London (08:00-17:00 UTC)
        london = day_df[day_df["time"].dt.hour.between(8, 16)]
        if london.empty:
            continue

        position = None

        for _, bar in london.iterrows():
            o = float(bar["open"])
            h = float(bar["high"])
            l_ = float(bar["low"])
            c  = float(bar["close"])

            # Gérer la position ouverte
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
                    fill = exit_price * (1 - slippage) if position["dir"] == "BUY" else exit_price * (1 + slippage)
                    exit_fee = fee_rate * position["qty"] * fill
                    gross = ((fill - position["entry"]) * position["qty"]
                             if position["dir"] == "BUY"
                             else (position["entry"] - fill) * position["qty"])
                    pnl = gross - position["fee_paid"] - exit_fee
                    equity += pnl
                    trades.append(LBTrade(
                        str(date), position["dir"], position["entry"],
                        position["stop"], position["tp"], fill, pnl, exit_reason
                    ))
                    position = None

            # Chercher une entrée (une seule par jour)
            if position is None:
                direction = None
                if c > asian_high + buf and o <= asian_high + buf:
                    direction = "BUY"
                elif c < asian_low - buf and o >= asian_low - buf:
                    direction = "SELL"

                if direction is not None:
                    entry = c * (1 + slippage) if direction == "BUY" else c * (1 - slippage)
                    if direction == "BUY":
                        stop = asian_low - buf
                        tp   = entry + (entry - stop) * rr
                    else:
                        stop = asian_high + buf
                        tp   = entry - (stop - entry) * rr

                    stop_dist = abs(entry - stop)
                    if stop_dist <= 0:
                        continue

                    risk_amount = equity * risk_pct
                    qty = risk_amount / stop_dist
                    max_notional = equity * cfg.max_notional_pct
                    if qty * entry > max_notional:
                        qty = max_notional / entry

                    entry_fee = fee_rate * qty * entry
                    position = {
                        "dir": direction, "entry": entry, "stop": stop,
                        "tp": tp, "qty": qty, "fee_paid": entry_fee,
                    }

        # Fermeture en fin de session si position encore ouverte
        if position is not None and not london.empty:
            last_close = float(london.iloc[-1]["close"])
            fill = last_close * (1 - slippage) if position["dir"] == "BUY" else last_close * (1 + slippage)
            exit_fee = fee_rate * position["qty"] * fill
            gross = ((fill - position["entry"]) * position["qty"]
                     if position["dir"] == "BUY"
                     else (position["entry"] - fill) * position["qty"])
            pnl = gross - position["fee_paid"] - exit_fee
            equity += pnl
            trades.append(LBTrade(
                str(date), position["dir"], position["entry"],
                position["stop"], position["tp"], fill, pnl, "eod"
            ))

        equity_curve.append(equity)

    return {
        "trades": trades,
        "equity_curve": equity_curve,
        "metrics": _metrics(trades, cfg.capital, equity_curve),
    }


def _metrics(trades: list[LBTrade], capital: float, equity_curve: list[float]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n_trades": 0, "message": "Aucun trade London Breakout généré."}

    pnls  = [t.pnl for t in trades]
    wins  = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    net   = sum(pnls)
    gp    = sum(wins)
    gl    = abs(sum(losses))

    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        max_dd = max(max_dd, peak - v)

    return {
        "n_trades":              n,
        "win_rate":              round(len(wins) / n * 100, 2),
        "net_profit":            round(net, 2),
        "return_pct":            round(net / capital * 100, 2),
        "profit_factor":         round(gp / gl, 2) if gl > 0 else float("inf"),
        "avg_win":               round(gp / len(wins), 4) if wins else 0,
        "avg_loss":              round(-gl / len(losses), 4) if losses else 0,
        "expectancy":            round((len(wins)/n) * (gp/len(wins) if wins else 0)
                                       + (len(losses)/n) * (-gl/len(losses) if losses else 0), 4),
        "max_drawdown_pct":      round(max_dd / capital * 100, 2),
        "final_equity":          round(equity_curve[-1], 2),
    }


def print_report_lb(result: dict) -> None:
    m = result["metrics"]
    print("=" * 50)
    print("📊 LONDON BREAKOUT — RÉSULTAT")
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
    for k, label in labels.items():
        print(f"   {label:<28}: {m[k]}")
    print("=" * 50)
