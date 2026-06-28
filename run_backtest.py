#!/usr/bin/env python3
"""
Lance un backtest de la stratégie sur des données historiques.

Exemples :
    # Données Binance (si réseau dispo)
    python run_backtest.py --symbol BTCUSDT --interval 5m --limit 1000

    # Depuis un CSV (colonnes : time,open,high,low,close,volume)
    python run_backtest.py --csv data/btc_5m.csv

    # Données synthétiques (hors-ligne, pour tester la mécanique)
    python run_backtest.py --synthetic --bars 3000
"""
from __future__ import annotations

import argparse

from scalping.config import StrategyConfig
from scalping.data import (get_candles_binance, get_history_binance,
                            get_candles_yf, load_csv, synthetic_ohlcv)
from scalping.backtest import run_backtest, print_report


def parse_args():
    p = argparse.ArgumentParser(description="Backtest scalping (patterns + cassures S/R)")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--symbol", default="BTCUSDT", help="Symbole Binance crypto (ex: BTCUSDT)")
    src.add_argument("--yf",     help="Symbole yfinance — stocks/forex (ex: AAPL, EURUSD=X)")
    src.add_argument("--csv",    help="Chemin d'un CSV OHLCV")
    src.add_argument("--synthetic", action="store_true", help="Données synthétiques hors-ligne")

    p.add_argument("--interval", default="5m", help="Intervalle Binance (défaut 5m)")
    p.add_argument("--limit", type=int, default=1000, help="Nb de bougies Binance")
    p.add_argument("--bars", type=int, default=3000, help="Nb de bougies synthétiques")

    p.add_argument("--capital", type=float, help="Capital ($)")
    p.add_argument("--risk", type=float, help="Risque par trade (%)")
    p.add_argument("--rr", type=float, help="Ratio Risk/Reward")
    p.add_argument("--min-confidence", type=float, help="Confiance minimale 0..1")

    # Leviers stratégie
    p.add_argument("--retest", action="store_true", help="Entrer au retest du niveau cassé")
    p.add_argument("--mtf", action="store_true", help="Exiger l'alignement multi-timeframe")
    p.add_argument("--htf-mult", type=int, help="Multiplicateur du TF supérieur (défaut 3)")
    p.add_argument("--no-adx", action="store_true", help="Désactiver le filtre ADX")
    p.add_argument("--adx-min", type=float, help="Seuil ADX minimal pour les cassures")

    p.add_argument("--plot", action="store_true", help="Affiche la courbe d'équité (matplotlib)")
    return p.parse_args()


def main():
    args = parse_args()

    cfg = StrategyConfig()
    if args.capital is not None:
        cfg.capital = args.capital
    if args.risk is not None:
        cfg.risk_percent = args.risk
    if args.rr is not None:
        cfg.rr_ratio = args.rr
    if args.min_confidence is not None:
        cfg.min_confidence = args.min_confidence
    if args.retest:
        cfg.require_retest = True
    if args.mtf:
        cfg.use_mtf = True
    if args.htf_mult is not None:
        cfg.htf_multiplier = args.htf_mult
    if args.no_adx:
        cfg.use_adx_filter = False
    if args.adx_min is not None:
        cfg.breakout_min_adx = args.adx_min

    if args.csv:
        print(f"📂 Chargement CSV : {args.csv}")
        df = load_csv(args.csv)
    elif args.synthetic:
        print(f"🧪 Génération de {args.bars} bougies synthétiques...")
        df = synthetic_ohlcv(n=args.bars)
    elif args.yf:
        print(f"📈 yfinance {args.yf} {args.interval} (2 ans)...")
        df = get_candles_yf(args.yf, args.interval, period="2y")
    else:
        print(f"🌐 Récupération Binance {args.symbol} {args.interval} ({args.limit} bougies)...")
        if args.limit > 1000:
            df = get_history_binance(args.symbol, args.interval, args.limit)
        else:
            df = get_candles_binance(args.symbol, args.interval, args.limit)

    if df.empty or len(df) < 100:
        print("❌ Données insuffisantes pour backtester.")
        return

    print(f"✅ {len(df)} bougies chargées. Lancement du backtest...\n")
    result = run_backtest(df, cfg)
    print_report(result)

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(11, 5))
            plt.plot(result["equity_curve"])
            plt.title("Courbe d'équité")
            plt.xlabel("Bougies")
            plt.ylabel("Équité ($)")
            plt.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig("equity_curve.png", dpi=120)
            print("\n🖼️  Courbe enregistrée : equity_curve.png")
        except ImportError:
            print("\n(matplotlib non installé : pip install matplotlib)")


if __name__ == "__main__":
    main()
