"""Tests des figures chartistes sur des structures construites."""
from scalping import chart_patterns as cp
from scalping.levels import find_pivots


def test_double_top(from_closes):
    # Deux sommets ~égaux (14) séparés d'un creux (~11), puis cassure du creux.
    closes = [10, 11, 12, 13, 14, 13, 12, 11, 12, 13, 14, 13, 12, 11, 10, 9]
    df = from_closes(closes)
    pivots = find_pivots(df, window=2)
    names = [p.name for p in cp.detect_chart_patterns(df, 14, pivots, window=2)]
    assert "double_top" in names


def test_double_bottom(from_closes):
    # Deux creux ~égaux (10), séparés d'un sommet (~13), puis cassure du sommet.
    closes = [14, 13, 12, 11, 10, 11, 12, 13, 12, 11, 10, 11, 12, 13, 14, 15]
    df = from_closes(closes)
    pivots = find_pivots(df, window=2)
    names = [p.name for p in cp.detect_chart_patterns(df, 14, pivots, window=2)]
    assert "double_bottom" in names
