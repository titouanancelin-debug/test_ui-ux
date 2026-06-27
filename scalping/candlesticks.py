"""
Bibliothèque de patterns de CHANDELIERS japonais (candlesticks).

Chaque détecteur renvoie une pd.Series booléenne alignée sur l'index du
DataFrame : True sur la bougie où le pattern se COMPLÈTE.

Tous les seuils sont relatifs (par rapport à l'amplitude de la bougie ou
à la tendance récente) pour fonctionner sur n'importe quel actif/prix.

Note importante : un pattern de chandelier n'a de valeur que dans son
CONTEXTE (tendance, niveau clé). La direction (haussier/baissier) de
chaque pattern est donnée dans PATTERN_DIRECTION ; le filtrage par
tendance/niveau est fait dans strategy.py.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

# Direction de chaque pattern : +1 haussier, -1 baissier, 0 indécision.
PATTERN_DIRECTION: dict[str, int] = {
    # 1 bougie
    "doji": 0,
    "dragonfly_doji": 1,
    "gravestone_doji": -1,
    "long_legged_doji": 0,
    "spinning_top": 0,
    "marubozu_bull": 1,
    "marubozu_bear": -1,
    "hammer": 1,
    "inverted_hammer": 1,
    "hanging_man": -1,
    "shooting_star": -1,
    # 2 bougies
    "bullish_engulfing": 1,
    "bearish_engulfing": -1,
    "bullish_harami": 1,
    "bearish_harami": -1,
    "piercing_line": 1,
    "dark_cloud_cover": -1,
    "tweezer_bottom": 1,
    "tweezer_top": -1,
    "bullish_kicker": 1,
    "bearish_kicker": -1,
    # 3 bougies
    "morning_star": 1,
    "evening_star": -1,
    "three_white_soldiers": 1,
    "three_black_crows": -1,
    "three_inside_up": 1,
    "three_inside_down": -1,
    "three_outside_up": 1,
    "three_outside_down": -1,
    "abandoned_baby_bull": 1,
    "abandoned_baby_bear": -1,
}


def _parts(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Décompose chaque bougie en ses éléments géométriques."""
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    rng = (h - l).replace(0, np.nan)
    body = (c - o).abs()
    upper = h - o.combine(c, max)
    lower = o.combine(c, min) - l
    return {
        "o": o, "h": h, "l": l, "c": c,
        "rng": rng, "body": body,
        "upper": upper, "lower": lower,
        "bull": c > o, "bear": c < o,
    }


def _uptrend(c: pd.Series, window: int = 5) -> pd.Series:
    """Le marché montait AVANT la bougie courante (proxy simple)."""
    return c.shift(1) > c.shift(1 + window)


def _downtrend(c: pd.Series, window: int = 5) -> pd.Series:
    return c.shift(1) < c.shift(1 + window)


# ----------------------------------------------------------------------
# Patterns à 1 bougie
# ----------------------------------------------------------------------
def doji(df, body_max=0.1) -> pd.Series:
    p = _parts(df)
    return (p["body"] <= body_max * p["rng"]).fillna(False)


def dragonfly_doji(df, body_max=0.1, wick_min=0.6) -> pd.Series:
    p = _parts(df)
    return (
        (p["body"] <= body_max * p["rng"])
        & (p["lower"] >= wick_min * p["rng"])
        & (p["upper"] <= 0.1 * p["rng"])
    ).fillna(False)


def gravestone_doji(df, body_max=0.1, wick_min=0.6) -> pd.Series:
    p = _parts(df)
    return (
        (p["body"] <= body_max * p["rng"])
        & (p["upper"] >= wick_min * p["rng"])
        & (p["lower"] <= 0.1 * p["rng"])
    ).fillna(False)


def long_legged_doji(df, body_max=0.1, wick_min=0.35) -> pd.Series:
    p = _parts(df)
    return (
        (p["body"] <= body_max * p["rng"])
        & (p["upper"] >= wick_min * p["rng"])
        & (p["lower"] >= wick_min * p["rng"])
    ).fillna(False)


def spinning_top(df) -> pd.Series:
    p = _parts(df)
    return (
        (p["body"] <= 0.35 * p["rng"])
        & (p["upper"] >= 0.25 * p["rng"])
        & (p["lower"] >= 0.25 * p["rng"])
    ).fillna(False)


def marubozu_bull(df, wick_max=0.05) -> pd.Series:
    p = _parts(df)
    return (
        p["bull"]
        & (p["upper"] <= wick_max * p["rng"])
        & (p["lower"] <= wick_max * p["rng"])
        & (p["body"] >= 0.9 * p["rng"])
    ).fillna(False)


def marubozu_bear(df, wick_max=0.05) -> pd.Series:
    p = _parts(df)
    return (
        p["bear"]
        & (p["upper"] <= wick_max * p["rng"])
        & (p["lower"] <= wick_max * p["rng"])
        & (p["body"] >= 0.9 * p["rng"])
    ).fillna(False)


def _hammer_shape(df) -> pd.Series:
    """Petit corps en haut, longue mèche basse, mèche haute courte."""
    p = _parts(df)
    return (
        (p["lower"] >= 2 * p["body"])
        & (p["upper"] <= p["body"])
        & (p["body"] <= 0.4 * p["rng"])
    ).fillna(False)


def _star_shape(df) -> pd.Series:
    """Petit corps en bas, longue mèche haute, mèche basse courte."""
    p = _parts(df)
    return (
        (p["upper"] >= 2 * p["body"])
        & (p["lower"] <= p["body"])
        & (p["body"] <= 0.4 * p["rng"])
    ).fillna(False)


def hammer(df) -> pd.Series:
    return (_hammer_shape(df) & _downtrend(df["close"])).fillna(False)


def hanging_man(df) -> pd.Series:
    return (_hammer_shape(df) & _uptrend(df["close"])).fillna(False)


def inverted_hammer(df) -> pd.Series:
    return (_star_shape(df) & _downtrend(df["close"])).fillna(False)


def shooting_star(df) -> pd.Series:
    return (_star_shape(df) & _uptrend(df["close"])).fillna(False)


# ----------------------------------------------------------------------
# Patterns à 2 bougies
# ----------------------------------------------------------------------
def bullish_engulfing(df) -> pd.Series:
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    return (
        (pc < po)               # bougie précédente baissière
        & (c > o)               # bougie courante haussière
        & (c >= po)             # englobe le corps précédent
        & (o <= pc)
    ).fillna(False)


def bearish_engulfing(df) -> pd.Series:
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    return (
        (pc > po)
        & (c < o)
        & (o >= pc)
        & (c <= po)
    ).fillna(False)


def bullish_harami(df) -> pd.Series:
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    return (
        (pc < po)                       # grande bougie baissière
        & (c > o)                       # petite bougie haussière
        & (o > pc) & (c < po)           # contenue dans le corps précédent
        & ((c - o).abs() < (po - pc).abs())
    ).fillna(False)


def bearish_harami(df) -> pd.Series:
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    return (
        (pc > po)
        & (c < o)
        & (o < pc) & (c > po)
        & ((c - o).abs() < (pc - po).abs())
    ).fillna(False)


def piercing_line(df) -> pd.Series:
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    mid_prev = (po + pc) / 2
    return (
        (pc < po)               # baissière avant
        & (c > o)               # haussière
        & (o < pc)              # ouvre sous la clôture précédente
        & (c > mid_prev)        # clôture au-dessus de la moitié
        & (c < po)              # mais pas au-dessus de l'ouverture (sinon engulfing)
    ).fillna(False)


def dark_cloud_cover(df) -> pd.Series:
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    mid_prev = (po + pc) / 2
    return (
        (pc > po)
        & (c < o)
        & (o > pc)
        & (c < mid_prev)
        & (c > po)
    ).fillna(False)


def tweezer_bottom(df, tol=0.001) -> pd.Series:
    l = df["low"]
    pl = l.shift(1)
    same_low = (l - pl).abs() <= tol * df["close"]
    p = _parts(df)
    return (same_low & p["bull"] & (df["close"].shift(1) < df["open"].shift(1))).fillna(False)


def tweezer_top(df, tol=0.001) -> pd.Series:
    h = df["high"]
    ph = h.shift(1)
    same_high = (h - ph).abs() <= tol * df["close"]
    p = _parts(df)
    return (same_high & p["bear"] & (df["close"].shift(1) > df["open"].shift(1))).fillna(False)


def bullish_kicker(df) -> pd.Series:
    """Gap haussier après une bougie baissière (ouverture > ouverture préc.)."""
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    return ((pc < po) & (c > o) & (o > po)).fillna(False)


def bearish_kicker(df) -> pd.Series:
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    return ((pc > po) & (c < o) & (o < po)).fillna(False)


# ----------------------------------------------------------------------
# Patterns à 3 bougies
# ----------------------------------------------------------------------
def morning_star(df, doji_max=0.3) -> pd.Series:
    o, c = df["open"], df["close"]
    body = (c - o).abs()
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    first_bear = (c.shift(2) < o.shift(2)) & (body.shift(2) >= 0.5 * rng.shift(2))
    small_mid = body.shift(1) <= doji_max * rng.shift(1)
    third_bull = (c > o) & (c > (o.shift(2) + c.shift(2)) / 2)
    return (first_bear & small_mid & third_bull).fillna(False)


def evening_star(df, doji_max=0.3) -> pd.Series:
    o, c = df["open"], df["close"]
    body = (c - o).abs()
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    first_bull = (c.shift(2) > o.shift(2)) & (body.shift(2) >= 0.5 * rng.shift(2))
    small_mid = body.shift(1) <= doji_max * rng.shift(1)
    third_bear = (c < o) & (c < (o.shift(2) + c.shift(2)) / 2)
    return (first_bull & small_mid & third_bear).fillna(False)


def three_white_soldiers(df) -> pd.Series:
    o, c = df["open"], df["close"]
    bull = c > o
    rising_close = (c > c.shift(1)) & (c.shift(1) > c.shift(2))
    # chaque ouverture dans le corps précédent
    open_in_body = (o > o.shift(1)) & (o < c.shift(1))
    return (
        bull & bull.shift(1) & bull.shift(2)
        & rising_close
        & open_in_body & open_in_body.shift(1)
    ).fillna(False)


def three_black_crows(df) -> pd.Series:
    o, c = df["open"], df["close"]
    bear = c < o
    falling_close = (c < c.shift(1)) & (c.shift(1) < c.shift(2))
    open_in_body = (o < o.shift(1)) & (o > c.shift(1))
    return (
        bear & bear.shift(1) & bear.shift(2)
        & falling_close
        & open_in_body & open_in_body.shift(1)
    ).fillna(False)


def three_inside_up(df) -> pd.Series:
    """Harami haussier (j-1) confirmé par une clôture au-dessus (j)."""
    harami = bullish_harami(df).shift(1).fillna(False)
    confirm = df["close"] > df["close"].shift(1)
    return (harami & confirm).fillna(False)


def three_inside_down(df) -> pd.Series:
    harami = bearish_harami(df).shift(1).fillna(False)
    confirm = df["close"] < df["close"].shift(1)
    return (harami & confirm).fillna(False)


def three_outside_up(df) -> pd.Series:
    """Engulfing haussier (j-1) confirmé par une clôture plus haute (j)."""
    eng = bullish_engulfing(df).shift(1).fillna(False)
    confirm = df["close"] > df["close"].shift(1)
    return (eng & confirm).fillna(False)


def three_outside_down(df) -> pd.Series:
    eng = bearish_engulfing(df).shift(1).fillna(False)
    confirm = df["close"] < df["close"].shift(1)
    return (eng & confirm).fillna(False)


def abandoned_baby_bull(df, doji_max=0.2) -> pd.Series:
    o, c, h, l = df["open"], df["close"], df["high"], df["low"]
    body = (c - o).abs()
    rng = (h - l).replace(0, np.nan)
    first_bear = c.shift(2) < o.shift(2)
    mid_doji = body.shift(1) <= doji_max * rng.shift(1)
    gap_down = h.shift(1) < l.shift(2)        # doji gappe sous la 1re
    gap_up = l > h.shift(1)                    # 3e gappe au-dessus du doji
    third_bull = c > o
    return (first_bear & mid_doji & gap_down & gap_up & third_bull).fillna(False)


def abandoned_baby_bear(df, doji_max=0.2) -> pd.Series:
    o, c, h, l = df["open"], df["close"], df["high"], df["low"]
    body = (c - o).abs()
    rng = (h - l).replace(0, np.nan)
    first_bull = c.shift(2) > o.shift(2)
    mid_doji = body.shift(1) <= doji_max * rng.shift(1)
    gap_up = l.shift(1) > h.shift(2)
    gap_down = h < l.shift(1)
    third_bear = c < o
    return (first_bull & mid_doji & gap_up & gap_down & third_bear).fillna(False)


# Registre nom -> fonction (l'ordre n'a pas d'importance).
DETECTORS = {
    "doji": doji,
    "dragonfly_doji": dragonfly_doji,
    "gravestone_doji": gravestone_doji,
    "long_legged_doji": long_legged_doji,
    "spinning_top": spinning_top,
    "marubozu_bull": marubozu_bull,
    "marubozu_bear": marubozu_bear,
    "hammer": hammer,
    "inverted_hammer": inverted_hammer,
    "hanging_man": hanging_man,
    "shooting_star": shooting_star,
    "bullish_engulfing": bullish_engulfing,
    "bearish_engulfing": bearish_engulfing,
    "bullish_harami": bullish_harami,
    "bearish_harami": bearish_harami,
    "piercing_line": piercing_line,
    "dark_cloud_cover": dark_cloud_cover,
    "tweezer_bottom": tweezer_bottom,
    "tweezer_top": tweezer_top,
    "bullish_kicker": bullish_kicker,
    "bearish_kicker": bearish_kicker,
    "morning_star": morning_star,
    "evening_star": evening_star,
    "three_white_soldiers": three_white_soldiers,
    "three_black_crows": three_black_crows,
    "three_inside_up": three_inside_up,
    "three_inside_down": three_inside_down,
    "three_outside_up": three_outside_up,
    "three_outside_down": three_outside_down,
    "abandoned_baby_bull": abandoned_baby_bull,
    "abandoned_baby_bear": abandoned_baby_bear,
}


def detect_all(df: pd.DataFrame) -> pd.DataFrame:
    """Renvoie un DataFrame booléen : une colonne par pattern."""
    return pd.DataFrame(
        {name: fn(df).astype(bool) for name, fn in DETECTORS.items()},
        index=df.index,
    )


def patterns_at(flags: pd.DataFrame, i: int) -> list[str]:
    """Liste des patterns actifs sur la ligne i."""
    row = flags.iloc[i]
    return [name for name in flags.columns if bool(row[name])]


def directional_score(flags: pd.DataFrame, i: int) -> int:
    """Somme des directions des patterns actifs en i (>0 haussier, <0 baissier)."""
    return sum(PATTERN_DIRECTION.get(name, 0) for name in patterns_at(flags, i))
