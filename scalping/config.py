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
    risk_percent: float = field(default_factory=lambda: _env_float("RISK_PERCENT", 1.5))
    rr_ratio: float = field(default_factory=lambda: _env_float("RR_RATIO", 2.0))

    # Frais aller-retour estimés (en fraction).
    # 0.001 = taker (0.1%/côté) | 0.0005 = maker limit order (0.05%/côté)
    fee_rate: float = 0.0005
    # Slippage estimé par côté (fraction du prix).
    slippage: float = 0.0002

    # Plafond de notionnel par position en fraction du capital (anti
    # sur-effet-de-levier quand le stop est très serré).
    max_notional_pct: float = 1.0

    # Trailing stop (fraction). None = désactivé.
    # Désactivé : sur crypto le trailing à 0.3% coupe les trades gagnants avant le TP.
    trailing_pct: float | None = None

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
    breakout_buffer_atr: float = 0.15   # marge au-delà du niveau (en ATR)
    breakout_volume_mult: float = 1.5   # volume mini = 1.5x la moyenne
    breakout_body_pct: float = 0.40     # corps mini = 40% du range (filtre bougies faibles)
    breakout_min_touches: int = 2       # niveaux testés au moins N fois (plus fiables)
    require_retest: bool = False        # exiger un retest du niveau cassé
    retest_lookback: int = 12           # fenêtre (bougies) pour retrouver la cassure à retester

    # --- Filtre de régime (force de tendance) ---
    use_adx_filter: bool = True         # ne valider les cassures que si tendance assez forte
    breakout_min_adx: float = 20.0      # seuil ADX minimal pour une cassure

    # --- Multi-timeframe ---
    use_mtf: bool = False               # exiger l'alignement avec un TF supérieur
    htf_multiplier: int = 3             # TF sup = htf_multiplier × TF d'entrée (5m×3 = 15m)

    # Activer / désactiver les composantes du score.
    # Les backtests montrent que les patterns chandeliers et figures
    # n'ont pas d'espérance positive sur crypto en TF courts.
    use_candle_patterns: bool = False
    use_chart_patterns: bool = False

    # Filtre macro : ne prendre que des trades dans le sens de la MA200.
    use_ma200_filter: bool = False
    ma200_period: int = 200

    # Veto EMA : la direction du trade DOIT être alignée avec la tendance EMA.
    require_ema_trend: bool = False

    # Veto MACD : histogramme MACD doit confirmer la direction.
    require_macd_confirm: bool = False

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
