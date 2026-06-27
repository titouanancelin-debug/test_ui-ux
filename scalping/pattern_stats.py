"""
Mesure de l'ESPÉRANCE RÉELLE de chaque pattern sur un jeu de données.

Idée : au lieu de croire la théorie, on teste chaque pattern isolément.
Pour chaque occurrence d'un pattern, on simule un trade simple dans sa
direction (entrée à l'ouverture suivante, stop = stop_atr × ATR,
objectif = rr × stop), frais + slippage inclus, et on agrège :

  - n           : nombre d'occurrences
  - win_rate    : % de trades gagnants
  - expectancy_R: gain moyen par trade, exprimé en multiples de risque (R)
  - profit_factor, total_R, avg_pct

On obtient un classement : quels patterns ont une vraie espérance
positive *sur tes données*. Garde ceux-là, désactive les autres.

⚠️ Test isolé et indicatif (pas de filtre de tendance/volume ni de gestion
de position avancée). Le verdict final reste le backtest complet.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from .config import StrategyConfig
from .indicators import add_indicators, atr as atr_fn
from . import candlesticks as cs
from . import chart_patterns as cp
from .levels import find_pivots


def _forward_trade(
    df: pd.DataFrame,
    i: int,
    direction: int,
    atr_i: float,
    cfg: StrategyConfig,
    stop_atr: float,
    rr: float,
    max_hold: int,
):
    """Simule un trade depuis la bougie i. Renvoie (net_pct, R, reason) ou None."""
    if i + 1 >= len(df) or atr_i <= 0:
        return None
    sign = 1 if direction > 0 else -1

    o = float(df["open"].iloc[i + 1])
    entry = o * (1 + cfg.slippage) if sign > 0 else o * (1 - cfg.slippage)
    risk_per_unit = stop_atr * atr_i
    stop = entry - sign * risk_per_unit
    target = entry + sign * rr * risk_per_unit

    exit_price, reason = None, "timeout"
    end = min(i + 1 + max_hold, len(df))
    for j in range(i + 1, end):
        h, l = float(df["high"].iloc[j]), float(df["low"].iloc[j])
        if sign > 0:
            if l <= stop:
                exit_price, reason = stop, "stop"; break
            if h >= target:
                exit_price, reason = target, "tp"; break
        else:
            if h >= stop:
                exit_price, reason = stop, "stop"; break
            if l <= target:
                exit_price, reason = target, "tp"; break
    if exit_price is None:
        exit_price = float(df["close"].iloc[end - 1])

    exit_fill = exit_price * (1 - cfg.slippage) if sign > 0 else exit_price * (1 + cfg.slippage)
    gross_pct = sign * (exit_fill - entry) / entry
    net_pct = gross_pct - 2 * cfg.fee_rate            # frais aller-retour
    risk_frac = risk_per_unit / entry
    R = net_pct / risk_frac if risk_frac > 0 else 0.0
    return net_pct, R, reason


def _aggregate(name: str, kind: str, results: list) -> dict | None:
    if not results:
        return None
    rs = [r[1] for r in results]
    pcts = [r[0] for r in results]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    n = len(rs)
    return {
        "pattern": name,
        "type": kind,
        "n": n,
        "win_rate": round(len(wins) / n * 100, 1),
        "expectancy_R": round(float(np.mean(rs)), 3),
        "total_R": round(float(np.sum(rs)), 2),
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "avg_pct": round(float(np.mean(pcts)) * 100, 3),
    }


def evaluate_patterns(
    df: pd.DataFrame,
    cfg: StrategyConfig | None = None,
    stop_atr: float = 1.0,
    rr: float = 2.0,
    max_hold: int = 20,
    min_occurrences: int = 5,
) -> pd.DataFrame:
    """Classe tous les patterns par espérance (en R) sur le DataFrame fourni."""
    cfg = cfg or StrategyConfig()
    d = add_indicators(df, cfg)
    atr_series = atr_fn(d)
    rows = []

    # --- Chandeliers ---
    flags = cs.detect_all(d)
    start = max(cfg.ema_slow, 30)
    for name in flags.columns:
        direction = cs.PATTERN_DIRECTION.get(name, 0)
        if direction == 0:
            continue  # pattern d'indécision : pas de sens directionnel à tester
        idx = [i for i in flags.index[flags[name]] if start <= i < len(d) - 1]
        results = []
        for i in idx:
            r = _forward_trade(d, i, direction, float(atr_series.iloc[i]), cfg, stop_atr, rr, max_hold)
            if r:
                results.append(r)
        agg = _aggregate(name, "chandelier", results)
        if agg and agg["n"] >= min_occurrences:
            rows.append(agg)

    # --- Figures chartistes ---
    pivots = find_pivots(d, cfg.pivot_window)
    chart_results: dict[str, list] = {}
    for i in range(start, len(d) - 1):
        for pat in cp.detect_chart_patterns(d, i, pivots, cfg.pivot_window):
            r = _forward_trade(d, i, pat.direction, float(atr_series.iloc[i]), cfg, stop_atr, rr, max_hold)
            if r:
                chart_results.setdefault(pat.name, []).append(r)
    for name, results in chart_results.items():
        agg = _aggregate(name, "figure", results)
        if agg and agg["n"] >= min_occurrences:
            rows.append(agg)

    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows).sort_values("expectancy_R", ascending=False).reset_index(drop=True)
    return out
