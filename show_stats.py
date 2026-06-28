#!/usr/bin/env python3
"""
Affiche les statistiques de validation depuis trades_log.csv.

Usage :
    python show_stats.py
    python show_stats.py --last 20   # 20 derniers trades seulement
"""
from __future__ import annotations
import argparse
import csv
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "trades_log.csv")


def load_trades(n: int | None = None) -> list[dict]:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE) as f:
        rows = list(csv.DictReader(f))
    return rows[-n:] if n else rows


def stats(trades: list[dict]) -> dict:
    if not trades:
        return {}
    total   = len(trades)
    # Un trade est "gagné" si executed=1 sur Alpaca, ou si on le suit manuellement
    # Pour l'instant on simule : direction SELL en bear = probablement win (simplifié)
    # Le vrai suivi sera manuel via trades_log
    executed = [t for t in trades if t.get("executed") == "1"]
    alerts   = [t for t in trades if t.get("executed") == "0"]

    by_sym: dict[str, int] = {}
    for t in trades:
        sym = t["symbol"]
        by_sym[sym] = by_sym.get(sym, 0) + 1

    return {
        "total":    total,
        "executed": len(executed),
        "alerts":   len(alerts),
        "by_sym":   by_sym,
        "first":    trades[0]["timestamp"] if trades else "—",
        "last":     trades[-1]["timestamp"] if trades else "—",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--last", type=int, help="Afficher seulement les N derniers trades")
    args = p.parse_args()

    trades = load_trades(args.last)
    if not trades:
        print("Aucun signal enregistré. Le bot n'a pas encore généré de trade.")
        return

    s = stats(trades)

    print()
    print("=" * 55)
    print("  TABLEAU DE BORD — PHASE DE VALIDATION")
    print("=" * 55)
    print(f"  Période     : {s['first']}  →  {s['last']}")
    print(f"  Signaux     : {s['total']} total  ({s['executed']} Alpaca auto + {s['alerts']} alertes)")
    print(f"  Restant     : {max(0, 30 - s['total'])} signaux pour valider (objectif 30)")
    print()
    print("  Signaux par actif :")
    for sym, count in sorted(s["by_sym"].items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"    {sym:<12} {bar} {count}")
    print()
    print("  💡 Pour valider un trade manuellement :")
    print("     Regarde le graphe après l'alerte Telegram :")
    print("     - TP touché en premier → WIN")
    print("     - SL touché en premier → LOSS")
    print("     Note le résultat dans un tableau avec la date.")
    print("=" * 55)

    # Afficher les derniers signaux
    print()
    print("  Derniers signaux :")
    print(f"  {'Date':<20} {'Symbole':<12} {'Dir':<6} {'Entrée':<10} {'TP':<10} {'Exec'}")
    print("  " + "-" * 65)
    for t in trades[-10:]:
        exec_s = "✅ Auto" if t.get("executed") == "1" else "📱 Alerte"
        print(f"  {t['timestamp']:<20} {t['symbol']:<12} {t['direction']:<6} "
              f"{float(t['entry']):>9.4f}  {float(t['tp']):>9.4f}  {exec_s}")
    print()


if __name__ == "__main__":
    main()
