"""
Notifications Telegram pour les signaux de trading.

Configuration (dans .env ou variables d'environnement) :
    TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
    TELEGRAM_CHAT_ID=123456789

Obtenir ces valeurs :
    1. Ouvre Telegram → cherche @BotFather → /newbot → copie le token
    2. Envoie un message à ton bot, puis ouvre :
       https://api.telegram.org/bot<TOKEN>/getUpdates
       → copie le "chat":{"id": ...}
"""
from __future__ import annotations

import os
import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _configured() -> bool:
    return bool(_TOKEN and _CHAT_ID)


def send(text: str) -> bool:
    """Envoie un message Telegram. Retourne True si succès."""
    if not _configured():
        return False
    url  = f"https://api.telegram.org/bot{_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id":    _CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read()).get("ok", False)
    except Exception as e:
        logger.warning(f"Telegram send failed: {e}")
        return False


def notify_signal(symbol: str, interval: str, direction: str,
                  entry: float, stop: float, tp: float,
                  confidence: float, reasons: list[str],
                  strategy: str = "breakout") -> None:
    emoji = "🟢" if direction == "BUY" else "🔴"
    tag   = "MR" if strategy == "mr" else "BO"
    lines = [
        f"{emoji} <b>SIGNAL {direction} [{tag}]</b>",
        f"📌 {symbol} {interval}  |  confiance {confidence:.0%}",
        f"",
        f"Entrée  : <code>{entry:.4f}</code>",
        f"Stop    : <code>{stop:.4f}</code>",
        f"TP      : <code>{tp:.4f}</code>",
        f"",
        f"<i>{' | '.join(reasons)}</i>",
    ]
    send("\n".join(lines))


def notify_order(symbol: str, direction: str, qty: float,
                 entry: float, stop: float, tp: float,
                 order_type: str = "bracket") -> None:
    emoji = "✅"
    lines = [
        f"{emoji} <b>ORDRE ENVOYÉ — {direction} {symbol}</b>",
        f"Type    : {order_type}",
        f"Qty     : {qty:.6f}",
        f"Entrée  : <code>{entry:.4f}</code>",
        f"SL      : <code>{stop:.4f}</code>",
        f"TP      : <code>{tp:.4f}</code>",
    ]
    send("\n".join(lines))


def notify_error(symbol: str, message: str) -> None:
    send(f"⚠️ <b>ERREUR [{symbol}]</b>\n<code>{message}</code>")


def notify_startup(n_strategies: int, capital: float, mode: str) -> None:
    send(
        f"🚀 <b>Bot démarré</b>\n"
        f"Mode     : {mode}\n"
        f"Capital  : {capital:,.2f}$\n"
        f"Stratégies actives : {n_strategies}"
    )


def notify_equity(capital: float, pct_change: float) -> None:
    arrow = "📈" if pct_change >= 0 else "📉"
    send(f"{arrow} <b>Équité mise à jour</b> : {capital:,.2f}$ ({pct_change:+.2f}%)")
