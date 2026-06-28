"""
Gestion du risque : taille de position, stop-loss, take-profit.

Corrige deux faiblesses du prototype d'origine :
  1. Aucun plafond de notionnel : avec un stop serré (scalping), la
     taille calculée par le risque pouvait dépasser largement le capital
     (effet de levier involontaire). On plafonne désormais le notionnel.
  2. SL/TP sans cohérence avec les niveaux : le TP peut viser le prochain
     niveau S/R, le SL se place au-delà du niveau cassé.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import StrategyConfig
from .levels import Level


@dataclass
class TradePlan:
    direction: str     # "BUY" / "SELL"
    entry: float
    stop: float
    take_profit: float
    qty: float
    risk_amount: float     # perte si le stop est touché (hors frais)
    notional: float        # exposition (qty * entry)


def position_size(
    entry: float, stop: float, cfg: StrategyConfig, capital: float | None = None
) -> tuple[float, float]:
    """Renvoie (qty, notionnel) en respectant le risque ET le plafond de notionnel.

    `capital` permet de passer l'équité courante (compound growth) plutôt que
    le capital initial fixé dans la config.
    """
    cap = capital if capital is not None else cfg.capital
    risk_amount = cap * (cfg.risk_percent / 100.0)
    stop_dist = abs(entry - stop)
    if stop_dist <= 0:
        return 0.0, 0.0

    qty = risk_amount / stop_dist

    max_notional = cap * cfg.max_notional_pct
    if qty * entry > max_notional:
        qty = max_notional / entry

    return qty, qty * entry


def take_profit_price(
    entry: float,
    stop: float,
    direction: str,
    cfg: StrategyConfig,
    levels: list[Level] | None = None,
) -> float:
    """TP basé uniquement sur le ratio R/R (sans plafonnage S/R qui écrase les gains)."""
    stop_dist = abs(entry - stop)
    if direction == "BUY":
        return entry + stop_dist * cfg.rr_ratio
    else:
        return entry - stop_dist * cfg.rr_ratio


def build_trade_plan(
    direction: str,
    entry: float,
    stop: float,
    cfg: StrategyConfig,
    levels: list[Level] | None = None,
    capital: float | None = None,
) -> TradePlan | None:
    """Construit un plan de trade complet, ou None s'il est invalide.

    `capital` permet de passer l'équité courante pour un sizing progressif.
    """
    if direction not in ("BUY", "SELL"):
        return None
    if (direction == "BUY" and stop >= entry) or (direction == "SELL" and stop <= entry):
        return None

    qty, notional = position_size(entry, stop, cfg, capital)
    if qty <= 0:
        return None

    tp = take_profit_price(entry, stop, direction, cfg, levels)
    risk_amount = qty * abs(entry - stop)
    return TradePlan(direction, entry, stop, tp, qty, risk_amount, notional)
