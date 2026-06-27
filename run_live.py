#!/usr/bin/env python3
"""
Boucle LIVE — génère des signaux en temps réel (paper trading).

Par défaut : MODE ALERTE uniquement (aucun ordre réel envoyé). On affiche
les signaux détectés avec leur plan de trade et leurs justifications.

Avec --execute : envoie des ordres bracket sur Alpaca Paper (clés via .env).
À n'utiliser qu'après avoir validé la stratégie en backtest.

Anti-repaint : on retire la dernière bougie (en cours de formation) et on
ne décide que sur des bougies CLÔTURÉES.

Exemples :
    python run_live.py --interval 5m --once
    python run_live.py --interval 5m --execute
"""
from __future__ import annotations

import argparse
import time
from datetime import datetime

from scalping.config import StrategyConfig, AlpacaConfig
from scalping.data import get_candles_binance
from scalping.strategy import prepare, generate_signal
from scalping.risk import build_trade_plan

DEFAULT_SYMBOLS = {
    "BTCUSDT": "BTC/USD",
    "ETHUSDT": "ETH/USD",
    "SOLUSDT": "SOL/USD",
}


def analyze_once(binance_sym, alpaca_sym, cfg, interval, limit, broker=None):
    df = get_candles_binance(binance_sym, interval, limit)
    if df.empty or len(df) < 120:
        print(f"⚠️  [{binance_sym}] données insuffisantes")
        return

    # Retirer la bougie en cours (non clôturée) -> anti-repaint.
    df = df.iloc[:-1].reset_index(drop=True)

    prep = prepare(df, cfg)
    sig = generate_signal(prep, len(prep.df) - 1, cfg)
    if sig is None:
        print(f"🔍 [{binance_sym}] pas de signal (clôture {df['close'].iloc[-1]:.4f})")
        return

    plan = build_trade_plan(sig.direction, sig.entry, sig.stop, cfg, sig.levels)
    if plan is None:
        print(f"🔍 [{binance_sym}] signal {sig.direction} rejeté (plan invalide)")
        return

    print(f"\n🎯 SIGNAL {sig.direction} sur {binance_sym} | confiance {sig.confidence:.0%}")
    print(f"   Entrée ~{plan.entry:.4f} | SL {plan.stop:.4f} | TP {plan.take_profit:.4f}")
    print(f"   Qty {plan.qty:.6f} | Notionnel {plan.notional:.2f}$ | Risque {plan.risk_amount:.2f}$")
    print("   Raisons : " + " ; ".join(sig.reasons))

    if broker is not None:
        if broker.has_position(alpaca_sym):
            print(f"   ⏭️  Position déjà ouverte sur {alpaca_sym}, on n'empile pas.")
            return
        res = broker.submit_bracket(
            alpaca_sym, sig.direction, plan.qty, plan.stop, plan.take_profit
        )
        if res.get("ok"):
            kind = "bracket (OCO)" if res.get("bracket") else "marché simple"
            print(f"   ✅ Ordre {kind} envoyé sur {alpaca_sym}")
            if res.get("warning"):
                print(f"   ⚠️  Bracket refusé ({res['warning']}) -> surveille SL/TP toi-même")
        else:
            print(f"   ❌ Ordre refusé : {res.get('error')}")


def main():
    p = argparse.ArgumentParser(description="Live scalping — signaux paper")
    p.add_argument("--interval", default="5m", help="Intervalle (défaut 5m)")
    p.add_argument("--limit", type=int, default=500, help="Nb de bougies récupérées")
    p.add_argument("--loop-interval", type=int, default=60, help="Secondes entre analyses")
    p.add_argument("--once", action="store_true", help="Une seule analyse puis sortie")
    p.add_argument("--execute", action="store_true", help="Envoyer des ordres sur Alpaca Paper")
    p.add_argument("--min-confidence", type=float, help="Confiance minimale 0..1")
    args = p.parse_args()

    cfg = StrategyConfig()
    if args.min_confidence is not None:
        cfg.min_confidence = args.min_confidence

    broker = None
    if args.execute:
        from scalping.broker_alpaca import AlpacaClient

        acfg = AlpacaConfig()
        if not acfg.configured:
            print("❌ --execute demandé mais clés Alpaca absentes (voir .env.example).")
            return
        broker = AlpacaClient(acfg)
        acct = broker.get_account()
        print(f"✅ Alpaca connecté | cash : {float(acct['cash']):,.2f}$")

    mode = "EXÉCUTION (paper)" if broker else "ALERTE seulement"
    print("=" * 55)
    print(f"🚀 LIVE SCALPING — mode {mode}")
    print(f"   Intervalle {args.interval} | confiance min {cfg.min_confidence}")
    print("=" * 55)

    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n⏰ [{now}] analyse...")
        for b_sym, a_sym in DEFAULT_SYMBOLS.items():
            try:
                analyze_once(b_sym, a_sym, cfg, args.interval, args.limit, broker)
            except Exception as e:
                print(f"⚠️  Erreur [{b_sym}] : {e}")
            time.sleep(1)

        if args.once:
            break
        print(f"\n💤 prochaine analyse dans {args.loop_interval}s...")
        time.sleep(args.loop_interval)


if __name__ == "__main__":
    main()
