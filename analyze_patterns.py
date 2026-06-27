#!/usr/bin/env python3
"""
Classe chaque pattern par espérance réelle sur tes données.

Exemples :
    python analyze_patterns.py --csv data/btc_5m.csv
    python analyze_patterns.py --symbol BTCUSDT --interval 5m --history 5000
    python analyze_patterns.py --synthetic --bars 5000

Sortie : un tableau trié par espérance (en R). Les patterns avec une
espérance positive et assez d'occurrences sont ceux à privilégier.
"""
from __future__ import annotations

import argparse

from scalping.config import StrategyConfig
from scalping.data import (
    get_candles_binance,
    get_history_binance,
    load_csv,
    synthetic_ohlcv,
)
from scalping.pattern_stats import evaluate_patterns


def main():
    p = argparse.ArgumentParser(description="Espérance réelle de chaque pattern")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--symbol", default="BTCUSDT")
    src.add_argument("--csv")
    src.add_argument("--synthetic", action="store_true")

    p.add_argument("--interval", default="5m")
    p.add_argument("--history", type=int, default=5000, help="Nb de bougies (Binance, paginé)")
    p.add_argument("--bars", type=int, default=5000, help="Nb de bougies synthétiques")
    p.add_argument("--stop-atr", type=float, default=1.0, help="Stop en multiples d'ATR")
    p.add_argument("--rr", type=float, default=2.0, help="Ratio Risk/Reward de l'objectif")
    p.add_argument("--max-hold", type=int, default=20, help="Durée max d'un trade (bougies)")
    p.add_argument("--min-occ", type=int, default=5, help="Occurrences minimales")
    p.add_argument("--save", help="Chemin CSV pour sauvegarder le tableau")
    args = p.parse_args()

    if args.csv:
        print(f"📂 Chargement CSV : {args.csv}")
        df = load_csv(args.csv)
    elif args.synthetic:
        print(f"🧪 {args.bars} bougies synthétiques...")
        df = synthetic_ohlcv(n=args.bars)
    else:
        print(f"🌐 Binance {args.symbol} {args.interval} (~{args.history} bougies)...")
        df = get_history_binance(args.symbol, args.interval, args.history)
        if df.empty:
            df = get_candles_binance(args.symbol, args.interval, 1000)

    if df.empty or len(df) < 200:
        print("❌ Données insuffisantes.")
        return

    print(f"✅ {len(df)} bougies. Analyse (stop={args.stop_atr}×ATR, RR={args.rr})...\n")
    cfg = StrategyConfig()
    table = evaluate_patterns(
        df, cfg,
        stop_atr=args.stop_atr, rr=args.rr,
        max_hold=args.max_hold, min_occurrences=args.min_occ,
    )

    if table.empty:
        print("Aucun pattern avec assez d'occurrences.")
        return

    print("=" * 78)
    print("ESPÉRANCE PAR PATTERN (triée par expectancy_R décroissante)")
    print("=" * 78)
    print(table.to_string(index=False))
    print("=" * 78)
    pos = table[table["expectancy_R"] > 0]
    print(f"\n✅ {len(pos)}/{len(table)} patterns avec espérance positive sur ces données.")
    print("   (À confirmer en backtest complet avec filtres tendance/volume.)")

    if args.save:
        table.to_csv(args.save, index=False)
        print(f"\n💾 Tableau sauvegardé : {args.save}")


if __name__ == "__main__":
    main()
