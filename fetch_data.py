#!/usr/bin/env python3
"""
Télécharge un historique de bougies depuis Binance et l'enregistre en CSV
(dans data/ par défaut), réutilisable par les autres scripts.

Exemple :
    python fetch_data.py --symbol BTCUSDT --interval 5m --bars 8000
    # -> data/BTCUSDT_5m.csv
"""
from __future__ import annotations

import argparse
import os

from scalping.data import get_history_binance, save_csv


def main():
    p = argparse.ArgumentParser(description="Télécharge des bougies Binance -> CSV")
    p.add_argument("--symbol", default="BTCUSDT")
    p.add_argument("--interval", default="5m")
    p.add_argument("--bars", type=int, default=8000, help="Nombre de bougies à récupérer")
    p.add_argument("--out", help="Chemin de sortie (défaut data/<symbol>_<interval>.csv)")
    args = p.parse_args()

    print(f"🌐 Téléchargement {args.symbol} {args.interval} (~{args.bars} bougies)...")
    df = get_history_binance(args.symbol, args.interval, args.bars)
    if df.empty:
        print("❌ Aucune donnée reçue (réseau / restriction géographique Binance ?).")
        return

    out = args.out or os.path.join("data", f"{args.symbol}_{args.interval}.csv")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    save_csv(df, out)
    print(f"✅ {len(df)} bougies enregistrées dans {out}")
    print(f"   Période : {df['time'].iloc[0]}  ->  {df['time'].iloc[-1]}")


if __name__ == "__main__":
    main()
