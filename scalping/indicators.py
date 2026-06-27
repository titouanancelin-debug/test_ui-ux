"""
Indicateurs techniques, tous vectorisés (renvoient des pd.Series alignées
sur l'index du DataFrame). Aucune dépendance à TA-Lib pour rester
installable partout.

Convention anti-repaint : ces fonctions calculent sur toute la série.
C'est au code appelant (stratégie/backtest) de n'utiliser QUE des bougies
clôturées pour décider (cf. strategy.py / backtest.py).
"""
from __future__ import annotations

import pandas as pd
import numpy as np


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI avec lissage de Wilder (standard), via ewm(alpha=1/period)."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100 - (100 / (1 + rs))
    # Si pas de perte du tout -> RSI = 100 ; si pas de gain -> 0.
    out = out.where(avg_loss != 0, 100.0)
    out = out.where(avg_gain != 0, out.where(avg_loss == 0, 0.0))
    return out.fillna(50.0)


def macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """Renvoie un DataFrame avec colonnes macd, signal, hist."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (lissage de Wilder)."""
    tr = true_range(df)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ADX : force de la tendance (pas la direction)."""
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = true_range(df)
    atr_ = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
        alpha=1 / period, adjust=False
    ).mean() / atr_.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
        alpha=1 / period, adjust=False
    ).mean() / atr_.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / period, adjust=False).mean().fillna(0.0)


def bollinger(series: pd.Series, window: int = 20, n_std: float = 2.0) -> pd.DataFrame:
    mid = sma(series, window)
    std = series.rolling(window).std()
    return pd.DataFrame(
        {"bb_mid": mid, "bb_up": mid + n_std * std, "bb_low": mid - n_std * std}
    )


def vwap(df: pd.DataFrame) -> pd.Series:
    """VWAP cumulatif (utile en intraday). À réinitialiser par session si besoin."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol = df["volume"].cumsum().replace(0, np.nan)
    return (typical * df["volume"]).cumsum() / cum_vol


def volume_ma(df: pd.DataFrame, window: int = 20) -> pd.Series:
    return df["volume"].rolling(window).mean()


def add_indicators(df: pd.DataFrame, cfg=None) -> pd.DataFrame:
    """Ajoute les indicateurs usuels au DataFrame (copie)."""
    from .config import StrategyConfig

    cfg = cfg or StrategyConfig()
    out = df.copy()
    out["ema_fast"] = ema(out["close"], cfg.ema_fast)
    out["ema_slow"] = ema(out["close"], cfg.ema_slow)
    out["rsi"] = rsi(out["close"], cfg.rsi_period)
    macd_df = macd(out["close"])
    out["macd"] = macd_df["macd"]
    out["macd_signal"] = macd_df["signal"]
    out["macd_hist"] = macd_df["hist"]
    out["atr"] = atr(out, cfg.atr_period)
    out["adx"] = adx(out, cfg.atr_period)
    out["vol_ma"] = volume_ma(out, 20)
    return out
