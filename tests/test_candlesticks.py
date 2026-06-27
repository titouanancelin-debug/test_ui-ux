"""Tests des détecteurs de chandeliers sur des cas construits à la main."""
from scalping import candlesticks as cs
from scalping.data import synthetic_ohlcv


def test_bullish_engulfing(make_df):
    df = make_df([
        (10, 10.5, 9.5, 10, 100),     # bougie de contexte
        (10, 10.2, 8.8, 9, 100),      # précédente baissière
        (8.9, 10.6, 8.8, 10.2, 100),  # englobante haussière
    ])
    assert bool(cs.bullish_engulfing(df).iloc[-1])
    assert not bool(cs.bearish_engulfing(df).iloc[-1])


def test_bearish_engulfing(make_df):
    df = make_df([
        (10, 10.5, 9.5, 10, 100),
        (9, 10.2, 8.8, 10, 100),       # précédente haussière
        (10.1, 10.6, 8.8, 8.9, 100),   # englobante baissière
    ])
    assert bool(cs.bearish_engulfing(df).iloc[-1])


def test_doji(make_df):
    df = make_df([(10, 10.6, 9.4, 10.02, 100)])
    assert bool(cs.doji(df).iloc[-1])


def test_marubozu_bull(make_df):
    df = make_df([(10, 11.0, 10.0, 11.0, 100)])
    assert bool(cs.marubozu_bull(df).iloc[-1])


def test_hammer_requires_downtrend(make_df):
    df = make_df([
        (20, 20.2, 19.8, 20, 100),
        (19, 19.2, 18.8, 19, 100),
        (18, 18.2, 17.8, 18, 100),
        (17, 17.2, 16.8, 17, 100),
        (16, 16.2, 15.8, 16, 100),
        (15.5, 15.7, 15.3, 15.5, 100),
        (15.2, 15.4, 15.0, 15.2, 100),
        (15.0, 15.15, 14.5, 15.1, 100),  # marteau après baisse
    ])
    assert bool(cs.hammer(df).iloc[-1])


def test_morning_star(make_df):
    df = make_df([
        (20, 20.3, 19.7, 20, 100),
        (20, 20.3, 17.6, 18, 100),      # grande baissière
        (17.9, 18.4, 17.5, 18.0, 100),  # petit corps (étoile)
        (18.1, 19.7, 18.0, 19.5, 100),  # forte haussière
    ])
    assert bool(cs.morning_star(df).iloc[-1])


def test_three_white_soldiers(make_df):
    df = make_df([
        (9, 9.3, 8.7, 9, 100),
        (10, 11.1, 9.9, 11, 100),
        (10.5, 11.7, 10.4, 11.6, 100),
        (11.1, 12.3, 11.0, 12.2, 100),
    ])
    assert bool(cs.three_white_soldiers(df).iloc[-1])


def test_detect_all_covers_all_patterns():
    df = synthetic_ohlcv(n=200)
    flags = cs.detect_all(df)
    assert set(flags.columns) == set(cs.DETECTORS.keys())
    # chaque détecteur a une direction déclarée
    assert all(name in cs.PATTERN_DIRECTION for name in cs.DETECTORS)


def test_directional_score_sign():
    df = synthetic_ohlcv(n=300)
    flags = cs.detect_all(df)
    # le score doit être un entier (somme de directions)
    assert isinstance(cs.directional_score(flags, 250), int)
