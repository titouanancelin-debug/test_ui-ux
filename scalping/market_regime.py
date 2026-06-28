"""
Données de régime de marché pour améliorer la qualité des signaux.

1. Funding Rate (Binance Futures)
   - Positif élevé (> +0.05%) : marché surlevéragé LONG → favoriser les SELL, réduire les BUY
   - Négatif élevé (< -0.05%) : marché surlevéragé SHORT → favoriser les BUY, réduire les SELL
   - Neutre (-0.05% à +0.05%) : pas de biais, signaux normaux

2. Corrélation des positions ouvertes
   - Cryptos sont corrélées entre elles (BTC/SOL/LINK bougent ensemble)
   - On limite le risque total crypto cumulé pour éviter 5 positions perdantes en même temps
"""
from __future__ import annotations

import urllib.request
import json
import logging
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

# Mapping symbole Binance spot → symbole futures
_FUTURES_MAP = {
    "BTCUSDT":  "BTCUSDT",
    "ETHUSDT":  "ETHUSDT",
    "SOLUSDT":  "SOLUSDT",
    "LINKUSDT": "LINKUSDT",
    "AAVEUSDT": "AAVEUSDT",
    "ARBUSDT":  "ARBUSDT",
    "INJUSDT":  "INJUSDT",
    "OPUSDT":   "OPUSDT",
    "SUIUSDT":  "SUIUSDT",
}

# Seuils funding rate
FR_HIGH  =  0.0005   # +0.05% → marché trop long → baisser confiance BUY
FR_LOW   = -0.0005   # -0.05% → marché trop short → baisser confiance SELL
FR_EXTREME_HIGH =  0.001   # +0.1% → signal SELL très fort
FR_EXTREME_LOW  = -0.001   # -0.1% → signal BUY très fort

_cache: dict[str, tuple[float, float]] = {}   # symbol → (funding_rate, timestamp)
_CACHE_TTL = 3600   # 1h (funding rate se met à jour toutes les 8h)


def get_funding_rate(symbol: str) -> float | None:
    """
    Retourne le funding rate actuel pour un symbole (futures Binance).
    Valeur entre -0.01 et +0.01 typiquement (fraction, pas %).
    Retourne None si pas de contrat futures ou erreur réseau.
    """
    fut_sym = _FUTURES_MAP.get(symbol)
    if not fut_sym:
        return None

    # Cache
    if fut_sym in _cache:
        fr, ts = _cache[fut_sym]
        if time.time() - ts < _CACHE_TTL:
            return fr

    try:
        url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={fut_sym}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        fr = float(data.get("lastFundingRate", 0))
        _cache[fut_sym] = (fr, time.time())
        return fr
    except Exception as e:
        logger.debug(f"Funding rate {symbol}: {e}")
        return None


def funding_signal_adjustment(symbol: str, direction: str) -> tuple[float, str]:
    """
    Retourne (multiplicateur_confiance, message) basé sur le funding rate.

    multiplicateur > 1 : signal renforcé
    multiplicateur < 1 : signal affaibli (peut annuler si trop faible)
    multiplicateur = 1 : neutre
    """
    fr = get_funding_rate(symbol)
    if fr is None:
        return 1.0, ""

    fr_pct = fr * 100  # en %

    if direction == "BUY":
        if fr >= FR_EXTREME_HIGH:
            # Funding très positif = trop de longs → BUY risqué
            return 0.5, f"⚠️ Funding élevé ({fr_pct:+.3f}%) → longs surlevéragés, BUY risqué"
        elif fr >= FR_HIGH:
            return 0.75, f"Funding positif ({fr_pct:+.3f}%) → légère prudence BUY"
        elif fr <= FR_EXTREME_LOW:
            # Funding très négatif = trop de shorts → BUY encore plus fort
            return 1.3, f"✅ Funding très négatif ({fr_pct:+.3f}%) → shorts à couvrir, BUY renforcé"
        elif fr <= FR_LOW:
            return 1.15, f"Funding négatif ({fr_pct:+.3f}%) → BUY légèrement renforcé"

    elif direction == "SELL":
        if fr <= FR_EXTREME_LOW:
            return 0.5, f"⚠️ Funding très négatif ({fr_pct:+.3f}%) → shorts surlevéragés, SELL risqué"
        elif fr <= FR_LOW:
            return 0.75, f"Funding négatif ({fr_pct:+.3f}%) → légère prudence SELL"
        elif fr >= FR_EXTREME_HIGH:
            return 1.3, f"✅ Funding très positif ({fr_pct:+.3f}%) → longs à liquider, SELL renforcé"
        elif fr >= FR_HIGH:
            return 1.15, f"Funding positif ({fr_pct:+.3f}%) → SELL légèrement renforcé"

    return 1.0, f"Funding neutre ({fr_pct:+.3f}%)"


# ---------------------------------------------------------------------------
# Gestion de la corrélation des positions ouvertes
# ---------------------------------------------------------------------------

# Groupes de corrélation (actifs qui bougent ensemble)
CORR_GROUPS = {
    "crypto_large":  ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "crypto_defi":   ["LINKUSDT", "AAVEUSDT", "INJUSDT", "OPUSDT"],
    "crypto_l2":     ["ARBUSDT", "OPUSDT", "SUIUSDT"],
    "stocks_us":     ["MSFT", "TSLA", "AMZN"],
}

# Risque max cumulé par groupe (% du capital)
MAX_GROUP_RISK = {
    "crypto_large": 3.0,   # max 3% du capital exposé sur BTC+ETH+SOL simultanément
    "crypto_defi":  3.0,
    "crypto_l2":    2.0,
    "stocks_us":    3.0,
}


class CorrelationManager:
    """Suit les positions ouvertes et calcule le risque corrélé."""

    def __init__(self):
        self._open: dict[str, float] = {}   # symbol → risk_pct engagé

    def add_position(self, symbol: str, risk_pct: float) -> None:
        self._open[symbol] = risk_pct

    def remove_position(self, symbol: str) -> None:
        self._open.pop(symbol, None)

    def group_risk(self, symbol: str) -> tuple[str | None, float]:
        """Retourne (nom_groupe, risque_total_du_groupe_actuellement_ouvert)."""
        for group, members in CORR_GROUPS.items():
            if any(m in symbol for m in members):
                total = sum(r for s, r in self._open.items()
                            if any(m in s for m in members))
                return group, total
        return None, 0.0

    def adjusted_risk(self, symbol: str, base_risk_pct: float) -> tuple[float, str]:
        """
        Retourne (risk_pct_ajusté, message).
        Réduit le risque si le groupe est déjà fortement exposé.
        """
        group, current_risk = self.group_risk(symbol)
        if group is None:
            return base_risk_pct, ""

        max_risk = MAX_GROUP_RISK.get(group, 3.0)
        remaining = max_risk - current_risk

        if remaining <= 0:
            return 0.0, f"⛔ Groupe '{group}' saturé ({current_risk:.1f}% / {max_risk}%) — signal ignoré"

        if base_risk_pct > remaining:
            adj = remaining
            return adj, f"⚠️ Risque réduit {base_risk_pct:.1f}%→{adj:.1f}% (groupe '{group}' à {current_risk:.1f}%/{max_risk}%)"

        return base_risk_pct, ""


def print_funding_table(symbols: list[str]) -> None:
    """Affiche un tableau des funding rates pour diagnostic."""
    print(f"\n{'Symbole':<12} {'Funding rate':>14} {'Biais':>20}")
    print("-" * 50)
    for sym in symbols:
        fr = get_funding_rate(sym)
        if fr is None:
            print(f"{sym:<12} {'N/A':>14}")
            continue
        fr_pct = fr * 100
        if fr > FR_HIGH:
            biais = "🔴 Trop long → favorise SELL"
        elif fr < FR_LOW:
            biais = "🟢 Trop short → favorise BUY"
        else:
            biais = "⚪ Neutre"
        print(f"{sym:<12} {fr_pct:>+13.4f}%  {biais}")
    print()
