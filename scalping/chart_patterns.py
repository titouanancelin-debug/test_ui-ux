"""
Figures CHARTISTES (chart patterns), construites à partir des pivots
(swing highs / lows). Contrairement aux chandeliers, ces figures se
déroulent sur plusieurs dizaines de bougies.

Patterns couverts :
  - Double / Triple Top et Bottom
  - Tête-épaules (Head & Shoulders) et son inverse
  - Triangles : ascendant, descendant, symétrique
  - Biseaux (wedges) : ascendant, descendant
  - Drapeaux (flags) : haussier, baissier

La détection est volontairement PRUDENTE : en cas de doute, elle ne
renvoie rien plutôt que de produire un faux signal. Un signal n'est émis
que lorsque la figure se *confirme* (cassure de la ligne de cou / du
niveau) sur la bougie clôturée `i`.

Anti-lookahead : seuls les pivots déjà *confirmés* à la bougie i sont
utilisés (un pivot en j n'est connu qu'à j + window).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .indicators import atr as atr_fn
from .levels import find_pivots


@dataclass
class ChartPattern:
    name: str
    direction: int        # +1 haussier, -1 baissier
    level: float          # niveau cassé (ligne de cou / résistance / support)


def _atr_at(df: pd.DataFrame, i: int) -> float:
    a = atr_fn(df).iloc[i]
    if not np.isfinite(a) or a <= 0:
        a = df["close"].iloc[i] * 0.005
    return float(a)


def _recent(idx_list, df, col, i, window, n=6):
    """Pivots confirmés à i, sous forme [(idx, prix)], les n plus récents."""
    usable = [j for j in idx_list if j <= i - window]
    pts = [(j, float(df[col].iloc[j])) for j in usable]
    return pts[-n:]


def _slope(p1, p2):
    if p2[0] == p1[0]:
        return 0.0
    return (p2[1] - p1[1]) / (p2[0] - p1[0])


def detect_chart_patterns(
    df: pd.DataFrame,
    i: int,
    pivots: tuple[list, list] | None = None,
    window: int = 3,
    tol_atr: float = 0.6,
    buffer_atr: float = 0.10,
    min_pole_atr: float = 3.0,
) -> list[ChartPattern]:
    """Détecte les figures qui se confirment sur la bougie clôturée i."""
    if i < window + 5 or i >= len(df):
        return []

    if pivots is None:
        idx_highs, idx_lows = find_pivots(df.iloc[: i + 1], window)
    else:
        idx_highs, idx_lows = pivots

    highs = _recent(idx_highs, df, "high", i, window)
    lows = _recent(idx_lows, df, "low", i, window)

    a = _atr_at(df, i)
    tol = tol_atr * a
    buf = buffer_atr * a
    close = float(df["close"].iloc[i])
    prev = float(df["close"].iloc[i - 1])

    found: list[ChartPattern] = []

    def broke_below(level):
        return prev >= level - buf and close < level - buf

    def broke_above(level):
        return prev <= level + buf and close > level + buf

    # ---- Double / Triple Top (baissier) ----
    if len(highs) >= 2:
        h1, h2 = highs[-2], highs[-1]
        if abs(h1[1] - h2[1]) <= tol:
            between = [lo for lo in lows if h1[0] < lo[0] < h2[0]]
            if between:
                neck = min(lo[1] for lo in between)
                if broke_below(neck):
                    name = "double_top"
                    if len(highs) >= 3 and abs(highs[-3][1] - h2[1]) <= tol:
                        name = "triple_top"
                    found.append(ChartPattern(name, -1, neck))

    # ---- Double / Triple Bottom (haussier) ----
    if len(lows) >= 2:
        l1, l2 = lows[-2], lows[-1]
        if abs(l1[1] - l2[1]) <= tol:
            between = [hi for hi in highs if l1[0] < hi[0] < l2[0]]
            if between:
                neck = max(hi[1] for hi in between)
                if broke_above(neck):
                    name = "double_bottom"
                    if len(lows) >= 3 and abs(lows[-3][1] - l2[1]) <= tol:
                        name = "triple_bottom"
                    found.append(ChartPattern(name, 1, neck))

    # ---- Tête-épaules (baissier) ----
    if len(highs) >= 3:
        ls, head, rs = highs[-3], highs[-2], highs[-1]
        if head[1] > ls[1] and head[1] > rs[1] and abs(ls[1] - rs[1]) <= 1.5 * tol:
            troughs = [lo for lo in lows if ls[0] < lo[0] < rs[0]]
            if troughs:
                neck = float(np.mean([lo[1] for lo in troughs]))
                if broke_below(neck):
                    found.append(ChartPattern("head_and_shoulders", -1, neck))

    # ---- Tête-épaules inversée (haussier) ----
    if len(lows) >= 3:
        ls, head, rs = lows[-3], lows[-2], lows[-1]
        if head[1] < ls[1] and head[1] < rs[1] and abs(ls[1] - rs[1]) <= 1.5 * tol:
            peaks = [hi for hi in highs if ls[0] < hi[0] < rs[0]]
            if peaks:
                neck = float(np.mean([hi[1] for hi in peaks]))
                if broke_above(neck):
                    found.append(ChartPattern("inverse_head_and_shoulders", 1, neck))

    # ---- Triangles & biseaux (au moins 2 pivots de chaque côté) ----
    if len(highs) >= 2 and len(lows) >= 2:
        sh = _slope(highs[-2], highs[-1])     # pente des sommets
        sl = _slope(lows[-2], lows[-1])       # pente des creux
        res_line = highs[-1][1] + sh * (i - highs[-1][0])   # projection à i
        sup_line = lows[-1][1] + sl * (i - lows[-1][0])
        flat = tol / max(highs[-1][0] - highs[-2][0], 1)    # seuil de "platitude"

        rising_h, falling_h = sh > flat, sh < -flat
        rising_l, falling_l = sl > flat, sl < -flat
        flat_h, flat_l = abs(sh) <= flat, abs(sl) <= flat

        # Triangle ascendant : sommets plats + creux montants -> cassure haut
        if flat_h and rising_l and broke_above(res_line):
            found.append(ChartPattern("ascending_triangle", 1, res_line))
        # Triangle descendant : creux plats + sommets descendants -> cassure bas
        elif flat_l and falling_h and broke_below(sup_line):
            found.append(ChartPattern("descending_triangle", -1, sup_line))
        # Triangle symétrique : sommets descendent, creux montent -> sens de la cassure
        elif falling_h and rising_l:
            if broke_above(res_line):
                found.append(ChartPattern("symmetrical_triangle", 1, res_line))
            elif broke_below(sup_line):
                found.append(ChartPattern("symmetrical_triangle", -1, sup_line))
        # Biseau ascendant : tout monte mais converge -> baissier
        elif rising_h and rising_l and sl > sh and broke_below(sup_line):
            found.append(ChartPattern("rising_wedge", -1, sup_line))
        # Biseau descendant : tout descend mais converge -> haussier
        elif falling_h and falling_l and sh > sl and broke_above(res_line):
            found.append(ChartPattern("falling_wedge", 1, res_line))

    # ---- Drapeaux (flags) : forte impulsion + petite consolidation ----
    pole = 12
    if i >= pole + 3:
        pole_move = close - float(df["close"].iloc[i - pole])
        recent_high = float(df["high"].iloc[i - 4 : i].max())
        recent_low = float(df["low"].iloc[i - 4 : i].min())
        consolidation = (recent_high - recent_low) <= 2.0 * a
        if pole_move > min_pole_atr * a and consolidation and broke_above(recent_high):
            found.append(ChartPattern("bull_flag", 1, recent_high))
        elif pole_move < -min_pole_atr * a and consolidation and broke_below(recent_low):
            found.append(ChartPattern("bear_flag", -1, recent_low))

    return found


def directional_chart_score(patterns: list[ChartPattern]) -> int:
    return sum(p.direction for p in patterns)
