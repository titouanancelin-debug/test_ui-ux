"""
Accès aux données OHLCV.

Convention de DataFrame utilisée PARTOUT dans le projet :
    colonnes = ["time", "open", "high", "low", "close", "volume"]
    - time   : datetime (UTC) ou entier ms
    - prix   : float
    - index  : RangeIndex (0..n-1)

Trois sources :
  - Binance (klines publiques, sans clé) : get_candles_binance()
  - CSV local                            : load_csv()
  - Générateur synthétique (offline)     : synthetic_ohlcv()
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import requests

OHLCV_COLUMNS = ["time", "open", "high", "low", "close", "volume"]

BINANCE_URL = "https://api.binance.com/api/v3/klines"

# Intervalles Binance valides (pour validation rapide).
VALID_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
}


def _coerce_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Force les types et l'ordre des colonnes, supprime les NaN."""
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    return df[OHLCV_COLUMNS]


def get_candles_binance(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """Récupère jusqu'à 1000 bougies depuis Binance (données publiques).

    Renvoie un DataFrame OHLCV vide en cas d'erreur réseau/HTTP.
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"Intervalle invalide : {interval!r}")

    params = {"symbol": symbol, "interval": interval, "limit": min(limit, 1000)}
    try:
        r = requests.get(BINANCE_URL, params=params, timeout=10)
        if r.status_code != 200:
            print(f"⚠️  Binance HTTP {r.status_code} [{symbol} {interval}]")
            return pd.DataFrame(columns=OHLCV_COLUMNS)

        raw = r.json()
        df = pd.DataFrame(
            raw,
            columns=[
                "time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_buy_base", "taker_buy_quote", "ignore",
            ],
        )
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        return _coerce_ohlcv(df)

    except Exception as e:  # réseau, JSON, etc.
        print(f"⚠️  Erreur Binance [{symbol} {interval}] : {e}")
        return pd.DataFrame(columns=OHLCV_COLUMNS)


def load_csv(path: str) -> pd.DataFrame:
    """Charge un CSV OHLCV. Tolérant sur la casse et la colonne de temps."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    # Normalise un éventuel nom de colonne de temps.
    for cand in ("time", "timestamp", "date", "datetime", "open_time"):
        if cand in df.columns:
            df = df.rename(columns={cand: "time"})
            break
    if "time" not in df.columns:
        df["time"] = range(len(df))

    missing = {"open", "high", "low", "close", "volume"} - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans {path} : {missing}")
    return _coerce_ohlcv(df)


def synthetic_ohlcv(
    n: int = 2000,
    start_price: float = 100.0,
    seed: int | None = 42,
    trend: float = 0.0,
    volatility: float = 0.004,
) -> pd.DataFrame:
    """Génère des bougies OHLCV pseudo-réalistes (marche aléatoire).

    Utile pour développer/tester sans accès réseau. Ce n'est PAS un
    marché réel : à n'utiliser que pour valider la mécanique du code.
    """
    rng = np.random.default_rng(seed)
    # Retours log avec une légère dérive + régimes de volatilité.
    drift = trend / max(n, 1)
    vol = volatility * (1 + 0.5 * np.sin(np.linspace(0, 6 * np.pi, n)))
    rets = rng.normal(drift, vol, n)
    close = start_price * np.exp(np.cumsum(rets))

    open_ = np.empty(n)
    open_[0] = start_price
    open_[1:] = close[:-1]

    # Mèches proportionnelles à la volatilité locale.
    wick = np.abs(rng.normal(0, vol, n)) * close
    high = np.maximum(open_, close) + wick
    low = np.minimum(open_, close) - wick
    volume = rng.lognormal(mean=8.0, sigma=0.4, size=n)

    times = pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC")
    df = pd.DataFrame(
        {
            "time": times,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )
    return _coerce_ohlcv(df)
