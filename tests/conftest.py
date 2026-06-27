"""Fixtures partagées pour construire des bougies de test."""
import pandas as pd
import pytest


def _make_df(rows):
    """rows : liste de tuples (open, high, low, close, volume)."""
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
    df.insert(0, "time", pd.date_range("2024-01-01", periods=len(df), freq="1min", tz="UTC"))
    return df.astype(
        {"open": float, "high": float, "low": float, "close": float, "volume": float}
    )


def _from_closes(closes, volume=100.0, wick=0.1):
    """Construit un DataFrame où open=close (bougies neutres), pratique pour
    tester les figures chartistes qui ne dépendent que des high/low/close."""
    rows = [(c, c + wick, c - wick, c, volume) for c in closes]
    return _make_df(rows)


@pytest.fixture
def make_df():
    return _make_df


@pytest.fixture
def from_closes():
    return _from_closes
