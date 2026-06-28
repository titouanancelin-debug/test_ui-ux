"""
Accès aux données OHLCV.

Convention de DataFrame utilisée PARTOUT dans le projet :
    colonnes = ["time", "open", "high", "low", "close", "volume"]
    - time   : datetime (UTC) ou entier ms
    - prix   : float
    - index  : RangeIndex (0..n-1)

Sources disponibles :
  - Binance (crypto, sans clé)       : get_candles_binance(), get_history_binance()
  - yfinance (stocks, ETF, forex)    : get_candles_yf()
  - Alpaca data API (stocks live)    : get_candles_alpaca_stocks()
  - CSV local                        : load_csv()
  - Générateur synthétique (offline) : synthetic_ohlcv()
"""
from __future__ import annotations

import time

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


def get_history_binance(symbol: str, interval: str, total: int = 5000) -> pd.DataFrame:
    """Récupère un long historique en paginant (Binance limite à 1000/req).

    Remonte le temps depuis maintenant jusqu'à obtenir ~`total` bougies.
    Idéal pour constituer un jeu de données de backtest sérieux.
    """
    if interval not in VALID_INTERVALS:
        raise ValueError(f"Intervalle invalide : {interval!r}")

    frames: list[pd.DataFrame] = []
    remaining = total
    end_time: int | None = None

    while remaining > 0:
        limit = min(1000, remaining)
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if end_time is not None:
            params["endTime"] = end_time
        try:
            r = requests.get(BINANCE_URL, params=params, timeout=10)
        except Exception as e:
            print(f"⚠️  Erreur réseau Binance : {e}")
            break
        if r.status_code != 200:
            print(f"⚠️  Binance HTTP {r.status_code} (arrêt pagination)")
            break
        data = r.json()
        if not data:
            break

        chunk = pd.DataFrame(
            data,
            columns=[
                "time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_buy_base", "taker_buy_quote", "ignore",
            ],
        )
        frames.append(chunk)
        end_time = int(data[0][0]) - 1   # juste avant la plus ancienne reçue
        remaining -= len(data)
        if len(data) < limit:
            break
        time.sleep(0.2)                  # politesse envers l'API

    if not frames:
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    full = pd.concat(frames, ignore_index=True)
    full["time"] = pd.to_datetime(full["time"], unit="ms", utc=True)
    full = full.drop_duplicates(subset="time").sort_values("time").reset_index(drop=True)
    return _coerce_ohlcv(full)


def get_candles_yf(
    symbol: str,
    interval: str = "1h",
    period: str = "2y",
) -> pd.DataFrame:
    """Données OHLCV via yfinance — stocks US, ETF, forex, indices.

    Symboles utiles :
      Stocks : "AAPL", "NVDA", "SPY", "QQQ"
      Forex  : "EURUSD=X", "GBPUSD=X", "USDJPY=X", "XAUUSD=X"
    Intervalles supportés : 1m, 5m, 15m, 30m, 1h, 1d, 1wk
    Note : les données intraday (≤1h) sont limitées à ~60 jours par yfinance.
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("Installe yfinance : pip install yfinance")

    yf_interval = {"4h": "1h"}.get(interval, interval)

    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=yf_interval, auto_adjust=True)
    if df.empty:
        return pd.DataFrame(columns=OHLCV_COLUMNS)

    df = df.reset_index()
    df.columns = [str(c).lower() for c in df.columns]
    for cand in ("datetime", "date", "timestamp"):
        if cand in df.columns:
            df = df.rename(columns={cand: "time"})
            break
    if "time" not in df.columns:
        df["time"] = range(len(df))

    df["time"] = pd.to_datetime(df["time"], utc=True)
    missing = {"open", "high", "low", "close", "volume"} - set(df.columns)
    if missing:
        return pd.DataFrame(columns=OHLCV_COLUMNS)
    return _coerce_ohlcv(df)


def get_candles_alpaca_stocks(
    symbol: str,
    interval: str = "1Hour",
    limit: int = 1000,
) -> pd.DataFrame:
    """Données OHLCV pour actions US via l'API data Alpaca (clés dans .env).

    Intervalles : 1Min, 5Min, 15Min, 30Min, 1Hour, 4Hour, 1Day
    """
    import os
    api_key    = os.environ.get("ALPACA_API_KEY", "")
    api_secret = os.environ.get("ALPACA_API_SECRET", "")
    if not api_key or not api_secret:
        raise RuntimeError("ALPACA_API_KEY / ALPACA_API_SECRET absents (voir .env)")

    tf_map = {"1h": "1Hour", "4h": "4Hour", "1d": "1Day"}
    timeframe = tf_map.get(interval.lower(), interval)

    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": api_secret}
    params  = {"timeframe": timeframe, "limit": min(limit, 10000),
                "adjustment": "split", "feed": "iex"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            print(f"⚠️  Alpaca data HTTP {r.status_code} [{symbol}]")
            return pd.DataFrame(columns=OHLCV_COLUMNS)
        bars = r.json().get("bars", [])
        if not bars:
            return pd.DataFrame(columns=OHLCV_COLUMNS)
        df = pd.DataFrame(bars)
        df = df.rename(columns={"t": "time", "o": "open", "h": "high",
                                 "l": "low",  "c": "close", "v": "volume"})
        df["time"] = pd.to_datetime(df["time"], utc=True)
        return _coerce_ohlcv(df)
    except Exception as e:
        print(f"⚠️  Erreur Alpaca data [{symbol}] : {e}")
        return pd.DataFrame(columns=OHLCV_COLUMNS)


def save_csv(df: pd.DataFrame, path: str) -> None:
    """Sauvegarde un DataFrame OHLCV en CSV (réutilisable par load_csv)."""
    df.to_csv(path, index=False)


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
