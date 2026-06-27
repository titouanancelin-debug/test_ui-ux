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
    buffer_atr: float = 0.10,
    volume_mult: float = 1.3,
) -> Breakout | None:
    """Teste si la bougie CLÔTURÉE i casse une zone S/R.

    Filtres anti-faux-breakout :
      - la CLÔTURE (pas juste la mèche) dépasse le niveau d'au moins
        buffer_atr * ATR,
      - le volume dépasse volume_mult * sa moyenne.
    """
    if i < 1 or i >= len(df):
        return None

    close = df["close"].iloc[i]
    prev_close = df["close"].iloc[i - 1]
    a = atr_fn(df).iloc[i]
    if not np.isfinite(a) or a <= 0:
        a = close * 0.005
    buf = buffer_atr * a

    vma = volume_ma(df).iloc[i]
    volume_ok = bool(np.isfinite(vma) and df["volume"].iloc[i] >= volume_mult * vma)

    # Cassure haussière : on était sous une résistance, on clôture franchement au-dessus.
    for lv in [l for l in levels if l.kind == "resistance"]:
        if prev_close <= lv.price + buf and close > lv.price + buf:
            return Breakout("BUY", lv.price, volume_ok, i)

    # Cassure baissière : on était au-dessus d'un support, on clôture franchement en dessous.
    for lv in [l for l in levels if l.kind == "support"]:
        if prev_close >= lv.price - buf and close < lv.price - buf:
            return Breakout("SELL", lv.price, volume_ok, i)

    return None
