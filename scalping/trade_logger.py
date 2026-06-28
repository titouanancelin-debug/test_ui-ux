"""
Logger CSV des signaux et trades en live.

Crée/complète le fichier trades_log.csv dans le répertoire de travail.
Colonnes : timestamp, symbol, interval, strategy, direction,
           entry, stop, tp, confidence, executed, equity
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trades_log.csv")

_HEADERS = [
    "timestamp", "symbol", "interval", "strategy",
    "direction", "entry", "stop", "tp",
    "confidence", "executed", "equity",
]


def _ensure_file() -> None:
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            csv.writer(f).writerow(_HEADERS)


def log_signal(
    symbol: str,
    interval: str,
    strategy: str,
    direction: str,
    entry: float,
    stop: float,
    tp: float,
    confidence: float,
    executed: bool = False,
    equity: float = 0.0,
) -> None:
    _ensure_file()
    row = [
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        symbol, interval, strategy, direction,
        round(entry, 6), round(stop, 6), round(tp, 6),
        round(confidence, 3), int(executed), round(equity, 2),
    ]
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow(row)


def print_last(n: int = 10) -> None:
    """Affiche les N derniers signaux loggés."""
    if not os.path.exists(LOG_FILE):
        print("Aucun signal enregistré.")
        return
    with open(LOG_FILE) as f:
        rows = list(csv.reader(f))
    header, data = rows[0], rows[1:]
    print("  ".join(f"{h:<12}" for h in header))
    print("-" * 100)
    for row in data[-n:]:
        print("  ".join(f"{v:<12}" for v in row))
