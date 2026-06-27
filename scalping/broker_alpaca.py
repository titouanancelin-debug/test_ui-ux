"""
Client Alpaca (Paper Trading) — minimal et robuste.

Améliorations vs prototype d'origine :
  - Clés lues depuis l'environnement (jamais en dur).
  - Ordre BRACKET (entrée + SL + TP liés en OCO) quand c'est supporté :
    si le TP est touché, le SL est annulé automatiquement (et inversement).
    L'original envoyait SL et TP séparés -> risque de position fantôme.
  - Normalisation des symboles + retries réseau.

⚠️  Alpaca ne supporte pas les ordres bracket/stop pour TOUTES les cryptos.
En cas de refus, on retombe sur un simple ordre marché et on PRÉVIENT :
le suivi SL/TP doit alors être assuré côté bot.
"""
from __future__ import annotations

import time

import requests

from .config import AlpacaConfig


class AlpacaClient:
    def __init__(self, cfg: AlpacaConfig | None = None):
        self.cfg = cfg or AlpacaConfig()
        if not self.cfg.configured:
            raise RuntimeError(
                "Clés Alpaca absentes. Renseignez ALPACA_API_KEY / "
                "ALPACA_API_SECRET (voir .env.example)."
            )

    # -- HTTP avec retries --
    def _request(self, method: str, path: str, **kw):
        url = f"{self.cfg.base_url}{path}"
        delay = 2
        last = None
        for _ in range(4):
            try:
                r = requests.request(method, url, headers=self.cfg.headers, timeout=10, **kw)
                return r
            except requests.RequestException as e:  # erreurs réseau uniquement
                last = e
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"Échec réseau Alpaca après retries : {last}")

    # -- Compte / positions --
    def get_account(self) -> dict:
        r = self._request("GET", "/v2/account")
        r.raise_for_status()
        return r.json()

    def get_positions(self) -> list[dict]:
        r = self._request("GET", "/v2/positions")
        return r.json() if r.status_code == 200 else []

    @staticmethod
    def _norm(symbol: str) -> str:
        return symbol.replace("/", "").upper()

    def has_position(self, symbol: str) -> bool:
        target = self._norm(symbol)
        return any(self._norm(p.get("symbol", "")) == target for p in self.get_positions())

    # -- Ordres --
    def submit_bracket(
        self, symbol: str, direction: str, qty: float, stop: float, take_profit: float
    ) -> dict:
        """Tente un ordre bracket (OCO). Retombe sur un ordre marché si refusé."""
        side = "buy" if direction == "BUY" else "sell"
        body = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side,
            "type": "market",
            "time_in_force": "gtc",
            "order_class": "bracket",
            "take_profit": {"limit_price": round(take_profit, 4)},
            "stop_loss": {"stop_price": round(stop, 4)},
        }
        r = self._request("POST", "/v2/orders", json=body)
        if r.status_code in (200, 201):
            return {"ok": True, "bracket": True, "order": r.json()}

        msg = ""
        try:
            msg = r.json().get("message", r.text)
        except Exception:
            msg = r.text
        # Repli : ordre marché simple (le bot devra surveiller SL/TP).
        body_simple = {
            "symbol": symbol, "qty": str(qty), "side": side,
            "type": "market", "time_in_force": "gtc",
        }
        r2 = self._request("POST", "/v2/orders", json=body_simple)
        if r2.status_code in (200, 201):
            return {"ok": True, "bracket": False, "order": r2.json(), "warning": msg}
        return {"ok": False, "error": msg or r2.text}

    def cancel_all(self) -> None:
        self._request("DELETE", "/v2/orders")
