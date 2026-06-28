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

import numpy as np

from .config import StrategyConfig
from .indicators import add_indicators, atr as atr_fn, ema
from . import candlesticks as cs
from . import chart_patterns as cp
from .levels import (
    detect_levels,
    detect_breakout,
    detect_retest,
    nearest_levels,
    find_pivots,
    Level,
)


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


def mtf_trend_series(df: pd.DataFrame, multiplier: int, cfg: StrategyConfig) -> pd.Series:
    """Tendance d'un timeframe SUPÉRIEUR, ramenée sur chaque bougie d'entrée.

    On regroupe les bougies par paquets de `multiplier` (ex: 3 bougies 5m =
    1 bougie 15m), on calcule la tendance EMA de ce TF supérieur, puis on
    l'attribue à chaque bougie d'entrée. Anti-lookahead : une bougie
    d'entrée n'utilise que la dernière bougie supérieure DÉJÀ CLÔTURÉE
    (le paquet précédent, pas celui en cours de formation).
    """
    n = len(df)
    multiplier = max(2, int(multiplier))
    group = np.arange(n) // multiplier
    g = df.groupby(group).agg(close=("close", "last"))
    ema_f = ema(g["close"], cfg.ema_fast)
    ema_s = ema(g["close"], cfg.ema_slow)
    gt = np.zeros(len(g), dtype=int)
    gt[(g["close"] > ema_f) & (ema_f > ema_s)] = 1
    gt[(g["close"] < ema_f) & (ema_f < ema_s)] = -1

    completed = group - 1                 # dernier paquet entièrement clôturé
    out = np.zeros(n, dtype=int)
    mask = completed >= 0
    out[mask] = gt[completed[mask]]
    return pd.Series(out, index=df.index)


def prepare(df: pd.DataFrame, cfg: StrategyConfig | None = None) -> Prepared:
    cfg = cfg or StrategyConfig()
    df_ind = add_indicators(df, cfg)
    if cfg.use_mtf:
        df_ind["htf_trend"] = mtf_trend_series(df_ind, cfg.htf_multiplier, cfg)
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
    adx_v = float(row["adx"])
    htf = int(row["htf_trend"]) if (cfg.use_mtf and "htf_trend" in df.columns) else 0
    ma200_v = float(row["ma200"]) if "ma200" in df.columns else None

    bull, bear, reasons = 0.0, 0.0, []

    # --- 0. Filtre macro MA200 : on n'achète qu'au-dessus, on ne vend qu'en dessous ---
    if cfg.use_ma200_filter and ma200_v is not None and not pd.isna(ma200_v):
        above_ma200 = price > ma200_v
        below_ma200 = price < ma200_v
    else:
        above_ma200 = below_ma200 = True

    # --- 1. Cassure / retest S/R (signal principal) ---
    if cfg.require_retest:
        bo = detect_retest(
            df, i, levels, cfg.retest_lookback,
            cfg.breakout_buffer_atr, cfg.breakout_volume_mult,
        )
        kind, base_w = "Retest", 0.50
    else:
        bo = detect_breakout(
            df, i, levels, cfg.breakout_buffer_atr, cfg.breakout_volume_mult,
            cfg.breakout_body_pct, cfg.breakout_min_touches,
        )
        kind, base_w = "Cassure", 0.45

    # Filtre de régime : une cassure n'est fiable qu'avec une tendance assez forte.
    if bo is not None and cfg.use_adx_filter and adx_v < cfg.breakout_min_adx:
        reasons.append(f"ADX {adx_v:.0f} < {cfg.breakout_min_adx:.0f} -> cassure ignorée")
        bo = None

    if bo is not None:
        w = base_w + (0.10 if bo.volume_ok else 0.0)
        vol_txt = "volume OK" if bo.volume_ok else "volume faible"
        side_txt = "résistance" if bo.direction == "BUY" else "support"
        if bo.direction == "BUY":
            bull += w
        else:
            bear += w
        reasons.append(f"{kind} {side_txt} {bo.level:.4f} ({vol_txt})")

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

    # --- 4. Patterns chandeliers (désactivés par défaut : pas d'espérance positive sur crypto) ---
    if cfg.use_candle_patterns:
        candle_score = cs.directional_score(prep.flags, i)
        if candle_score > 0:
            bull += min(0.20, 0.07 * candle_score)
            reasons.append("Chandeliers haussiers: " + ", ".join(cs.patterns_at(prep.flags, i)))
        elif candle_score < 0:
            bear += min(0.20, 0.07 * abs(candle_score))
            reasons.append("Chandeliers baissiers: " + ", ".join(cs.patterns_at(prep.flags, i)))

    # --- 5. Figures chartistes (désactivées par défaut : trop peu d'occurrences fiables) ---
    if cfg.use_chart_patterns:
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

    # --- 7. Alignement multi-timeframe (si activé) ---
    if cfg.use_mtf and htf != 0:
        if htf > 0:
            bull += 0.10
        else:
            bear += 0.10

    # --- Décision ---
    net = bull - bear
    if abs(net) < 1e-9:
        return None
    direction = "BUY" if net > 0 else "SELL"

    # Veto MA200 : on n'achète qu'au-dessus, on ne vend qu'en dessous.
    if cfg.use_ma200_filter and ma200_v is not None and not pd.isna(ma200_v):
        if direction == "BUY" and not above_ma200:
            return None
        if direction == "SELL" and not below_ma200:
            return None
        reasons.append(f"MA200 {'au-dessus' if above_ma200 else 'en dessous'} ({ma200_v:.0f})")

    # Veto EMA : on n'achète qu'en tendance haussière, on ne vend qu'en tendance baissière.
    if cfg.require_ema_trend:
        if direction == "BUY" and trend != "BULLISH":
            return None
        if direction == "SELL" and trend != "BEARISH":
            return None

    # Veto MACD : l'histogramme doit confirmer la direction du trade.
    if cfg.require_macd_confirm:
        if direction == "BUY" and macd_hist <= 0:
            return None
        if direction == "SELL" and macd_hist >= 0:
            return None

    # Veto multi-timeframe : on ne prend pas de trade à contre-tendance du TF supérieur.
    if cfg.use_mtf and htf != 0:
        if (direction == "BUY" and htf < 0) or (direction == "SELL" and htf > 0):
            return None
        reasons.append("Aligné avec le TF supérieur")

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
