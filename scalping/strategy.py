"""
Moteur de signaux : combine tous les modules en une décision.

Philosophie (alignée sur ta préférence pour les cassures) :
  - La CASSURE de support/résistance est le signal PRINCIPAL (poids fort),
    avec ses filtres anti-faux-breakout (clôture franche + volume).
  - La tendance (EMA) et le MACD donnent le contexte.
  - Les patterns (chandeliers + chartistes) confirment / renforcent.
  - Le RSI sert de garde-fou (on n'achète pas en zone de surachat, etc.).

Chaque signal porte un SCORE DE CONFIANCE (0..1) et la liste des raisons,
pour la transparence (utile en alertes paper et au debug).

La même fonction est utilisée par le backtest et le live -> cohérence
totale entre la recherche et l'exécution. On ne décide JAMAIS sur une
bougie non clôturée (anti-repaint).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .config import StrategyConfig
from .indicators import add_indicators, atr as atr_fn
from . import candlesticks as cs
from . import chart_patterns as cp
from .levels import detect_levels, detect_breakout, nearest_levels, find_pivots, Level


@dataclass
class Signal:
    direction: str             # "BUY" / "SELL"
    entry: float
    stop: float
    confidence: float
    reasons: list[str] = field(default_factory=list)
    levels: list[Level] = field(default_factory=list)
    index: int = -1


@dataclass
class Prepared:
    """Pré-calculs réutilisables sur tout le DataFrame (perf backtest)."""
    df: pd.DataFrame
    flags: pd.DataFrame
    pivots: tuple[list, list]


def prepare(df: pd.DataFrame, cfg: StrategyConfig | None = None) -> Prepared:
    cfg = cfg or StrategyConfig()
    df_ind = add_indicators(df, cfg)
    flags = cs.detect_all(df_ind)
    pivots = find_pivots(df_ind, cfg.pivot_window)
    return Prepared(df_ind, flags, pivots)


def _trend(row) -> str:
    if row["close"] > row["ema_fast"] > row["ema_slow"]:
        return "BULLISH"
    if row["close"] < row["ema_fast"] < row["ema_slow"]:
        return "BEARISH"
    return "NEUTRAL"


def generate_signal(
    prep: Prepared, i: int, cfg: StrategyConfig | None = None
) -> Signal | None:
    """Évalue la bougie clôturée i et renvoie un Signal ou None."""
    cfg = cfg or StrategyConfig()
    df = prep.df
    if i < max(cfg.ema_slow, cfg.sr_lookback // 4, 30) or i >= len(df):
        return None

    row = df.iloc[i]
    price = float(row["close"])
    atr_i = float(atr_fn(df).iloc[i])
    if atr_i <= 0:
        return None

    levels = detect_levels(
        df.iloc[: i + 1], cfg.sr_lookback, cfg.pivot_window, cfg.sr_cluster_atr
    )
    trend = _trend(row)
    rsi_v = float(row["rsi"])
    macd_hist = float(row["macd_hist"])

    bull, bear, reasons = 0.0, 0.0, []

    # --- 1. Cassure S/R (signal principal) ---
    bo = detect_breakout(df, i, levels, cfg.breakout_buffer_atr, cfg.breakout_volume_mult)
    if bo is not None:
        w = 0.45 + (0.10 if bo.volume_ok else 0.0)
        vol_txt = "volume OK" if bo.volume_ok else "volume faible"
        if bo.direction == "BUY":
            bull += w
            reasons.append(f"Cassure résistance {bo.level:.4f} ({vol_txt})")
        else:
            bear += w
            reasons.append(f"Cassure support {bo.level:.4f} ({vol_txt})")

    # --- 2. Tendance (contexte) ---
    if trend == "BULLISH":
        bull += 0.20
        reasons.append("Tendance haussière (EMA)")
    elif trend == "BEARISH":
        bear += 0.20
        reasons.append("Tendance baissière (EMA)")

    # --- 3. MACD ---
    if macd_hist > 0:
        bull += 0.10
    elif macd_hist < 0:
        bear += 0.10

    # --- 4. Patterns chandeliers ---
    candle_score = cs.directional_score(prep.flags, i)
    if candle_score > 0:
        bull += min(0.20, 0.07 * candle_score)
        reasons.append("Chandeliers haussiers: " + ", ".join(cs.patterns_at(prep.flags, i)))
    elif candle_score < 0:
        bear += min(0.20, 0.07 * abs(candle_score))
        reasons.append("Chandeliers baissiers: " + ", ".join(cs.patterns_at(prep.flags, i)))

    # --- 5. Figures chartistes ---
    charts = cp.detect_chart_patterns(
        df, i, prep.pivots, cfg.pivot_window, buffer_atr=cfg.breakout_buffer_atr
    )
    for pat in charts:
        if pat.direction > 0:
            bull += 0.15
            reasons.append(f"Figure: {pat.name}")
        else:
            bear += 0.15
            reasons.append(f"Figure: {pat.name}")

    # --- 6. Garde-fous RSI (on calme l'enthousiasme aux extrêmes) ---
    if rsi_v >= cfg.rsi_overbought:
        bull *= 0.4
        reasons.append(f"RSI surachat {rsi_v:.0f} (freine les achats)")
    if rsi_v <= cfg.rsi_oversold:
        bear *= 0.4
        reasons.append(f"RSI survente {rsi_v:.0f} (freine les ventes)")

    # --- Décision ---
    net = bull - bear
    if abs(net) < 1e-9:
        return None
    direction = "BUY" if net > 0 else "SELL"
    confidence = min(1.0, abs(net))
    if confidence < cfg.min_confidence:
        return None

    # --- Stop : au-delà du niveau cassé, sinon basé sur l'ATR ---
    if bo is not None and bo.direction == direction:
        stop = bo.level - 0.5 * atr_i if direction == "BUY" else bo.level + 0.5 * atr_i
    else:
        nearest_sup, nearest_res = nearest_levels(levels, price)
        if direction == "BUY":
            base = price - 1.5 * atr_i
            stop = min(base, nearest_sup.price - 0.3 * atr_i) if nearest_sup else base
        else:
            base = price + 1.5 * atr_i
            stop = max(base, nearest_res.price + 0.3 * atr_i) if nearest_res else base

    # Cohérence finale.
    if (direction == "BUY" and stop >= price) or (direction == "SELL" and stop <= price):
        return None

    return Signal(direction, price, float(stop), confidence, reasons, levels, i)
