"""
Support / Résistance et cassures (breakouts).

Approche :
  1. Détecter les pivots (swing highs / swing lows) — extremums locaux.
  2. Regrouper les pivots proches en "zones" (un niveau testé plusieurs
     fois est plus fort).
  3. Détecter une cassure : clôture franche au-delà d'une zone, avec
     filtres anti-faux-signal (marge en ATR + confirmation de volume),
     et optionnellement un retest.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import numpy as np

from .indicators import atr as atr_fn, volume_ma


@dataclass
class Level:
    price: float
    kind: str          # "support" ou "resistance"
    touches: int       # nombre de pivots regroupés (force du niveau)


def find_pivots(df: pd.DataFrame, window: int = 3):
    """Renvoie (idx_highs, idx_lows) des pivots confirmés.

    Un pivot haut en i = high[i] strictement supérieur aux `window`
    bougies de chaque côté. Confirmé seulement `window` bougies plus tard
    (pas de lecture du futur en live).
    """
    highs = df["high"].values
    lows = df["low"].values
    n = len(df)
    idx_highs, idx_lows = [], []
    for i in range(window, n - window):
        seg_h = highs[i - window : i + window + 1]
        seg_l = lows[i - window : i + window + 1]
        if highs[i] == seg_h.max() and (seg_h == highs[i]).sum() == 1:
            idx_highs.append(i)
        if lows[i] == seg_l.min() and (seg_l == lows[i]).sum() == 1:
            idx_lows.append(i)
    return idx_highs, idx_lows


def detect_levels(
    df: pd.DataFrame,
    lookback: int = 150,
    window: int = 3,
    cluster_atr: float = 0.5,
) -> list[Level]:
    """Détecte et regroupe les niveaux S/R sur les `lookback` dernières bougies."""
    sub = df.iloc[-lookback:] if len(df) > lookback else df
    sub = sub.reset_index(drop=True)
    idx_highs, idx_lows = find_pivots(sub, window)

    a = atr_fn(sub).iloc[-1]
    if not np.isfinite(a) or a <= 0:
        a = sub["close"].iloc[-1] * 0.005  # repli : 0.5 % du prix
    tol = cluster_atr * a

    def cluster(prices: list[float], kind: str) -> list[Level]:
        if not prices:
            return []
        prices = sorted(prices)
        groups = [[prices[0]]]
        for p in prices[1:]:
            if abs(p - groups[-1][-1]) <= tol:
                groups[-1].append(p)
            else:
                groups.append([p])
        return [Level(float(np.mean(g)), kind, len(g)) for g in groups]

    res = cluster([sub["high"].iloc[i] for i in idx_highs], "resistance")
    sup = cluster([sub["low"].iloc[i] for i in idx_lows], "support")
    return sup + res


def nearest_levels(levels: list[Level], price: float):
    """Renvoie (support le plus proche en dessous, résistance la plus proche au-dessus)."""
    supports = [lv for lv in levels if lv.price < price]
    resistances = [lv for lv in levels if lv.price > price]
    nearest_sup = max(supports, key=lambda l: l.price) if supports else None
    nearest_res = min(resistances, key=lambda l: l.price) if resistances else None
    return nearest_sup, nearest_res


@dataclass
class Breakout:
    direction: str     # "BUY" (cassure de résistance) ou "SELL" (cassure de support)
    level: float
    volume_ok: bool
    index: int


def detect_breakout(
    df: pd.DataFrame,
    i: int,
    levels: list[Level],
    buffer_atr: float = 0.15,
    volume_mult: float = 1.5,
    body_pct: float = 0.40,
    min_touches: int = 2,
) -> Breakout | None:
    """Teste si la bougie CLÔTURÉE i casse une zone S/R.

    Filtres anti-faux-breakout :
      - la CLÔTURE dépasse le niveau d'au moins buffer_atr * ATR,
      - le volume dépasse volume_mult * sa moyenne,
      - le corps de la bougie représente au moins body_pct du range
        (filtre les cassures sur bougies indécises / doji).
    """
    if i < 1 or i >= len(df):
        return None

    close = df["close"].iloc[i]
    open_ = df["open"].iloc[i]
    high = df["high"].iloc[i]
    low = df["low"].iloc[i]
    prev_close = df["close"].iloc[i - 1]

    a = atr_fn(df).iloc[i]
    if not np.isfinite(a) or a <= 0:
        a = close * 0.005
    buf = buffer_atr * a

    candle_range = high - low
    body = abs(close - open_)
    body_strong = candle_range <= 0 or (body / candle_range) >= body_pct

    vma = volume_ma(df).iloc[i]
    volume_ok = bool(np.isfinite(vma) and df["volume"].iloc[i] >= volume_mult * vma)

    # Cassure haussière : clôture franche au-dessus, bougie haussière forte, niveau solide.
    for lv in [l for l in levels if l.kind == "resistance" and l.touches >= min_touches]:
        if prev_close <= lv.price + buf and close > lv.price + buf:
            if close > open_ and body_strong:
                return Breakout("BUY", lv.price, volume_ok, i)

    # Cassure baissière : clôture franche en dessous, bougie baissière forte, niveau solide.
    for lv in [l for l in levels if l.kind == "support" and l.touches >= min_touches]:
        if prev_close >= lv.price - buf and close < lv.price - buf:
            if close < open_ and body_strong:
                return Breakout("SELL", lv.price, volume_ok, i)

    return None


def detect_retest(
    df: pd.DataFrame,
    i: int,
    levels: list[Level],
    lookback: int = 12,
    buffer_atr: float = 0.10,
    volume_mult: float = 1.3,
    tol_atr: float = 0.4,
) -> Breakout | None:
    """Détecte une entrée sur RETEST d'un niveau récemment cassé.

    Entrée plus prudente que la cassure brute : on attend que le prix
    revienne tester le niveau cassé et qu'il TIENNE (le niveau cassé fait
    désormais office de support/résistance), ce qui filtre beaucoup de
    faux breakouts.

      - BUY  : une résistance a été cassée à la hausse récemment, le prix
               revient la toucher (mèche basse) mais CLÔTURE au-dessus.
      - SELL : un support a été cassé à la baisse récemment, le prix
               revient le toucher (mèche haute) mais CLÔTURE en dessous.
    """
    if i < lookback + 1 or i >= len(df):
        return None

    close = df["close"].iloc[i]
    low = df["low"].iloc[i]
    high = df["high"].iloc[i]
    open_ = df["open"].iloc[i]

    a = atr_fn(df).iloc[i]
    if not np.isfinite(a) or a <= 0:
        a = close * 0.005
    buf = buffer_atr * a
    tol = tol_atr * a

    vma = volume_ma(df).iloc[i]
    volume_ok = bool(np.isfinite(vma) and df["volume"].iloc[i] >= volume_mult * vma)

    window_close = df["close"].iloc[i - lookback : i]

    # Retest haussier d'une résistance cassée.
    for lv in [l for l in levels if l.kind == "resistance"]:
        broke_recently = bool((window_close > lv.price + buf).any())
        retest_touch = low <= lv.price + tol
        holds = close > lv.price and close > open_     # bougie de rejet haussière
        if broke_recently and retest_touch and holds:
            return Breakout("BUY", lv.price, volume_ok, i)

    # Retest baissier d'un support cassé.
    for lv in [l for l in levels if l.kind == "support"]:
        broke_recently = bool((window_close < lv.price - buf).any())
        retest_touch = high >= lv.price - tol
        holds = close < lv.price and close < open_     # bougie de rejet baissière
        if broke_recently and retest_touch and holds:
            return Breakout("SELL", lv.price, volume_ok, i)

    return None
