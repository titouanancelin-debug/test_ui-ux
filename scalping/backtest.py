"""
Backtester événementiel (bar par bar), volontairement RÉALISTE :

  - Décision à la clôture de la bougie i, ENTRÉE à l'ouverture de i+1
    (on ne triche pas avec le futur).
  - Frais ET slippage appliqués à l'entrée et à la sortie (sans ça, un
    backtest de scalping est mensonger).
  - Si stop et take-profit sont touchés dans la même bougie, on suppose
    le STOP en premier (hypothèse prudente).
  - Trailing stop optionnel.

Métriques : winrate, profit factor, expectancy, max drawdown, etc.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import StrategyConfig
from .strategy import prepare, generate_signal
from .risk import build_trade_plan


@dataclass
class Trade:
    entry_idx: int
    exit_idx: int
    direction: str
    entry: float
    exit: float
    qty: float
    pnl: float
    exit_reason: str        # "tp" / "stop" / "trail" / "eod"
    confidence: float


def _exit_fill(level: float, direction: str, slippage: float) -> float:
    # Sortie défavorable : on vend un peu moins cher / on rachète un peu plus cher.
    return level * (1 - slippage) if direction == "BUY" else level * (1 + slippage)


def run_backtest(
    df: pd.DataFrame,
    cfg: StrategyConfig | None = None,
    prep=None,
    start_idx: int | None = None,
    end_idx: int | None = None,
) -> dict:
    """Backtest sur tout le DataFrame, ou sur une fenêtre [start_idx, end_idx).

    `prep` (résultat de strategy.prepare) peut être fourni pour éviter de
    recalculer les indicateurs/pivots — utile en walk-forward où l'on teste
    plusieurs fenêtres sur les mêmes données.
    """
    cfg = cfg or StrategyConfig()
    if prep is None:
        prep = prepare(df, cfg)
    d = prep.df
    n = len(d)
    warmup = max(cfg.ema_slow, 30) + cfg.pivot_window
    start = max(warmup, start_idx) if start_idx is not None else warmup
    stop_at = min(end_idx, n) if end_idx is not None else n

    trades: list[Trade] = []
    equity = cfg.capital
    equity_curve = [equity]

    position = None          # dict décrivant la position ouverte
    pending = None           # Signal en attente d'exécution à l'ouverture suivante

    for j in range(start, stop_at):
        bar = d.iloc[j]
        o, h, l = float(bar["open"]), float(bar["high"]), float(bar["low"])

        # 1) Exécuter une entrée en attente, à l'ouverture de cette bougie.
        if position is None and pending is not None:
            sig = pending
            pending = None
            slip = cfg.slippage
            entry_fill = o * (1 + slip) if sig.direction == "BUY" else o * (1 - slip)
            plan = build_trade_plan(sig.direction, entry_fill, sig.stop, cfg, sig.levels)
            if plan is not None:
                entry_fee = cfg.fee_rate * plan.qty * entry_fill
                position = {
                    "dir": sig.direction,
                    "entry_idx": j,
                    "entry": entry_fill,
                    "qty": plan.qty,
                    "stop": plan.stop,
                    "tp": plan.take_profit,
                    "fee_paid": entry_fee,
                    "hw": entry_fill,   # plus haut atteint (trailing)
                    "lw": entry_fill,   # plus bas atteint (trailing)
                    "conf": sig.confidence,
                }

        # 2) Gérer la position ouverte sur cette bougie.
        if position is not None:
            d_ = position["dir"]
            exit_price = exit_reason = None

            if d_ == "BUY":
                if l <= position["stop"]:
                    exit_price, exit_reason = position["stop"], "stop"
                elif h >= position["tp"]:
                    exit_price, exit_reason = position["tp"], "tp"
            else:
                if h >= position["stop"]:
                    exit_price, exit_reason = position["stop"], "stop"
                elif l <= position["tp"]:
                    exit_price, exit_reason = position["tp"], "tp"

            if exit_price is not None:
                fill = _exit_fill(exit_price, d_, cfg.slippage)
                exit_fee = cfg.fee_rate * position["qty"] * fill
                gross = (
                    (fill - position["entry"]) * position["qty"]
                    if d_ == "BUY"
                    else (position["entry"] - fill) * position["qty"]
                )
                pnl = gross - position["fee_paid"] - exit_fee
                equity += pnl
                trades.append(
                    Trade(
                        position["entry_idx"], j, d_, position["entry"], fill,
                        position["qty"], pnl, exit_reason, position["conf"],
                    )
                )
                position = None
            else:
                # Mise à jour du trailing stop (après le test de sortie : pas de lookahead intrabar).
                if cfg.trailing_pct:
                    if d_ == "BUY":
                        position["hw"] = max(position["hw"], h)
                        new_stop = position["hw"] * (1 - cfg.trailing_pct)
                        position["stop"] = max(position["stop"], new_stop)
                    else:
                        position["lw"] = min(position["lw"], l)
                        new_stop = position["lw"] * (1 + cfg.trailing_pct)
                        position["stop"] = min(position["stop"], new_stop)

        # 3) Chercher un nouveau signal (à la clôture de cette bougie) si on est plat.
        if position is None and pending is None and j < stop_at - 1:
            sig = generate_signal(prep, j, cfg)
            if sig is not None:
                pending = sig

        equity_curve.append(equity)

    metrics = compute_metrics(trades, cfg.capital, equity_curve)
    return {"trades": trades, "equity_curve": equity_curve, "metrics": metrics}


def compute_metrics(trades: list[Trade], capital: float, equity_curve: list[float]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n_trades": 0, "message": "Aucun trade généré sur cette période."}

    pnls = [t.pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    net = sum(pnls)

    # Max drawdown sur la courbe d'équité.
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        max_dd = max(max_dd, peak - v)

    # Pertes consécutives max.
    streak = max_streak = 0
    for p in pnls:
        streak = streak + 1 if p <= 0 else 0
        max_streak = max(max_streak, streak)

    win_rate = len(wins) / n
    avg_win = (gross_profit / len(wins)) if wins else 0.0
    avg_loss = (-gross_loss / len(losses)) if losses else 0.0

    return {
        "n_trades": n,
        "win_rate": round(win_rate * 100, 2),
        "net_profit": round(net, 2),
        "return_pct": round(net / capital * 100, 2),
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "expectancy": round(win_rate * avg_win + (1 - win_rate) * avg_loss, 4),
        "max_drawdown": round(max_dd, 2),
        "max_drawdown_pct": round(max_dd / capital * 100, 2),
        "max_consecutive_losses": max_streak,
        "final_equity": round(equity_curve[-1], 2),
    }


def print_report(result: dict) -> None:
    m = result["metrics"]
    print("=" * 50)
    print("📊 RÉSULTAT DU BACKTEST")
    print("=" * 50)
    if m.get("n_trades", 0) == 0:
        print(m.get("message"))
        return
    labels = {
        "n_trades": "Nombre de trades",
        "win_rate": "Taux de réussite (%)",
        "net_profit": "Profit net ($)",
        "return_pct": "Rendement (%)",
        "profit_factor": "Profit factor",
        "expectancy": "Espérance / trade ($)",
        "avg_win": "Gain moyen ($)",
        "avg_loss": "Perte moyenne ($)",
        "max_drawdown": "Drawdown max ($)",
        "max_drawdown_pct": "Drawdown max (%)",
        "max_consecutive_losses": "Pertes consécutives max",
        "final_equity": "Équité finale ($)",
    }
    for k, label in labels.items():
        print(f"   {label:<28}: {m[k]}")
    print("=" * 50)
