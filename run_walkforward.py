#!/usr/bin/env python3
"""
Validation walk-forward de la stratégie (in-sample / out-of-sample).

Exemples :
    python run_walkforward.py --csv data/btc_5m.csv --is 2000 --oos 500
    python run_walkforward.py --symbol BTCUSDT --interval 5m --history 8000
    python run_walkforward.py --synthetic --bars 8000
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
from scalping.walkforward import walk_forward, print_walkforward


def main():
    p = argparse.ArgumentParser(description="Walk-forward (validation OOS)")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--symbol", default="BTCUSDT")
    src.add_argument("--csv")
    src.add_argument("--synthetic", action="store_true")

    p.add_argument("--interval", default="5m")
    p.add_argument("--history", type=int, default=8000)
    p.add_argument("--bars", type=int, default=8000)

    p.add_argument("--is", dest="is_bars", type=int, default=1500, help="Bougies in-sample")
    p.add_argument("--oos", dest="oos_bars", type=int, default=500, help="Bougies out-of-sample")
    p.add_argument("--step", type=int, help="Décalage entre fenêtres (défaut = oos)")
    p.add_argument("--retest", action="store_true")
    p.add_argument("--mtf", action="store_true")
    args = p.parse_args()

    if args.csv:
        print(f"📂 CSV : {args.csv}")
        df = load_csv(args.csv)
    elif args.synthetic:
        print(f"🧪 {args.bars} bougies synthétiques...")
        df = synthetic_ohlcv(n=args.bars)
    else:
        print(f"🌐 Binance {args.symbol} {args.interval} (~{args.history} bougies)...")
        df = get_history_binance(args.symbol, args.interval, args.history)
        if df.empty:
            df = get_candles_binance(args.symbol, args.interval, 1000)

    needed = args.is_bars + args.oos_bars
    if df.empty or len(df) < needed:
        print(f"❌ Il faut au moins {needed} bougies (reçu {len(df)}).")
        return

    cfg = StrategyConfig()
    if args.retest:
        cfg.require_retest = True
    if args.mtf:
        cfg.use_mtf = True

    print(f"✅ {len(df)} bougies. Walk-forward IS={args.is_bars} / OOS={args.oos_bars}...\n")
    result = walk_forward(
        df, cfg, is_bars=args.is_bars, oos_bars=args.oos_bars, step=args.step
    )
    print_walkforward(result)


if __name__ == "__main__":
    main()
