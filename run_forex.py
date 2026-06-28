#!/usr/bin/env python3
"""
Backtest des stratégies forex/or : London Breakout et Mean Reversion.

Exemples :
    python run_forex.py --symbol EURUSD=X --strategy lb
    python run_forex.py --symbol XAUUSD=X --strategy mr
    python run_forex.py --symbol GC=F --strategy both
"""
from __future__ import annotations

import argparse

from scalping.config import StrategyConfig
from scalping.data import get_candles_yf
from scalping.london_breakout import run_backtest_lb, print_report_lb
from scalping.mean_reversion import run_backtest_mr, print_report_mr


FOREX_SYMBOLS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "GBPJPY=X": "GBP/JPY",
    "AUDUSD=X": "AUD/USD",
    "GC=F":     "Gold (XAU/USD)",
}


def main():
    p = argparse.ArgumentParser(description="Backtest forex/or — LB & MR")
    p.add_argument("--symbol",   default="EURUSD=X", help="Symbole yfinance")
    p.add_argument("--strategy", default="both", choices=["lb", "mr", "both"],
                   help="lb=London Breakout | mr=Mean Reversion | both")
    p.add_argument("--period",   default="2y",  help="Période yfinance (ex: 2y, 5y)")
    p.add_argument("--rr",       type=float, default=2.0, help="RR pour LB (défaut 2.0)")
    p.add_argument("--mr-rr",    type=float, default=1.5, help="RR pour MR (défaut 1.5)")
    p.add_argument("--capital",  type=float, default=200.0)
    p.add_argument("--all",      action="store_true", help="Tester toutes les paires")
    args = p.parse_args()

    cfg = StrategyConfig()
    cfg.capital  = args.capital
    cfg.rr_ratio = args.rr

    symbols = list(FOREX_SYMBOLS.keys()) if args.all else [args.symbol]

    for sym in symbols:
        label = FOREX_SYMBOLS.get(sym, sym)
        print(f"\n{'='*60}")
        print(f"📌 {label} ({sym})")
        print(f"{'='*60}")

        df = get_candles_yf(sym, interval="1h", period=args.period)
        if df.empty or len(df) < 200:
            print(f"❌ Données insuffisantes pour {sym}")
            continue
        print(f"✅ {len(df)} bougies chargées")

        if args.strategy in ("lb", "both"):
            cfg.rr_ratio = args.rr
            result = run_backtest_lb(df, cfg)
            print_report_lb(result)

        if args.strategy in ("mr", "both"):
            result = run_backtest_mr(df, cfg, rr=args.mr_rr)
            print_report_mr(result, label=f"MEAN REVERSION {label}")


if __name__ == "__main__":
    main()
