"""
Configuration centralisée.

Les secrets (clés API) viennent UNIQUEMENT des variables d'environnement
(ou d'un fichier .env local), jamais du code source. Les paramètres de
stratégie ont des valeurs par défaut raisonnables, surchargeables via
l'environnement.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

# Chargement optionnel d'un fichier .env (sans planter s'il est absent
# ou si python-dotenv n'est pas installé).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dépendance optionnelle
    pass


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class StrategyConfig:
    """Paramètres de la stratégie et de la gestion du risque."""

    capital: float = field(default_factory=lambda: _env_float("CAPITAL", 200.0))
    risk_percent: float = field(default_factory=lambda: _env_float("RISK_PERCENT", 1.0))
    rr_ratio: float = field(default_factory=lambda: _env_float("RR_RATIO", 2.0))

    # Frais aller-retour estimés (en fraction). 0.001 = 0.1 % par côté.
    # Crucial en scalping : des frais sous-estimés rendent un backtest menteur.
    fee_rate: float = 0.001
    # Slippage estimé par côté (fraction du prix).
    slippage: float = 0.0005

    # Plafond de notionnel par position en fraction du capital (anti
    # sur-effet-de-levier quand le stop est très serré).
    max_notional_pct: float = 1.0

    # Trailing stop (fraction). None = désactivé.
    trailing_pct: float | None = 0.003

    # --- Filtres de signal ---
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    atr_period: int = 14

    # --- Détection support/résistance ---
    sr_lookback: int = 150
    pivot_window: int = 3          # nb de bougies de chaque côté d'un pivot
    sr_cluster_atr: float = 0.5    # regroupe les niveaux distants de < 0.5*ATR

    # --- Cassure (breakout) ---
    breakout_buffer_atr: float = 0.10   # marge au-delà du niveau (en ATR)
    breakout_volume_mult: float = 1.3   # volume mini = 1.3x la moyenne
    require_retest: bool = False        # exiger un retest du niveau cassé

    # Score minimal (0..1) pour émettre un signal.
    min_confidence: float = 0.5


@dataclass
class AlpacaConfig:
    """Identifiants Alpaca (paper). Chargés depuis l'environnement."""

    api_key: str = field(default_factory=lambda: os.environ.get("ALPACA_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.environ.get("ALPACA_API_SECRET", ""))
    base_url: str = field(
        default_factory=lambda: os.environ.get(
            "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
        )
    )

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    @property
    def headers(self) -> dict:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json",
        }
