"""
Validation WALK-FORWARD (in-sample / out-of-sample).

Principe : on découpe l'historique en fenêtres glissantes.
  - Sur chaque fenêtre IN-SAMPLE (IS), on choisit le meilleur réglage
    (ici : le seuil de confiance) parmi une petite grille.
  - On évalue ce réglage sur la fenêtre OUT-OF-SAMPLE (OOS) qui suit,
    c.-à-d. sur des données JAMAIS vues lors du choix.

On n'agrège que les résultats OOS : c'est la seule mesure honnête de ce
qu'on aurait vraiment obtenu. Si l'OOS s'effondre alors que l'IS brille,
c'est du sur-apprentissage.

Anti-lookahead : les indicateurs sont calculés une fois sur tout
l'historique (chaque indicateur en i n'utilise que i et le passé), et le
choix du réglage sur IS précède toujours, dans le temps, la fenêtre OOS.
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd

from .config import StrategyConfig
from .strategy import prepare
from .backtest import run_backtest


def walk_forward(
    df: pd.DataFrame,
    cfg: StrategyConfig | None = None,
    is_bars: int = 1500,
    oos_bars: int = 500,
    step: int | None = None,
    grid: list[float] | None = None,
    min_trades_is: int = 10,
) -> dict:
    """Lance la validation walk-forward et renvoie {folds, summary}."""
    cfg = cfg or StrategyConfig()
    step = step or oos_bars
    grid = grid or [0.4, 0.5, 0.6, 0.7]

    prep = prepare(df, cfg)
    n = len(prep.df)
    folds = []

    start = 0
    while start + is_bars + oos_bars <= n:
        is_lo, is_hi = start, start + is_bars
        oos_lo, oos_hi = is_hi, is_hi + oos_bars

        # 1) Choix du seuil de confiance sur l'IN-SAMPLE.
        best_mc, best_score = grid[0], None
        for mc in grid:
            c = replace(cfg, min_confidence=mc)
            m = run_backtest(prep.df, c, prep=prep, start_idx=is_lo, end_idx=is_hi)["metrics"]
            if m.get("n_trades", 0) < min_trades_is:
                continue
            score = m.get("expectancy", -9.9)
            if best_score is None or score > best_score:
                best_score, best_mc = score, mc

        # 2) Évaluation OUT-OF-SAMPLE avec ce réglage.
        c = replace(cfg, min_confidence=best_mc)
        oos = run_backtest(prep.df, c, prep=prep, start_idx=oos_lo, end_idx=oos_hi)["metrics"]

        folds.append({
            "is_range": (is_lo, is_hi),
            "oos_range": (oos_lo, oos_hi),
            "chosen_min_confidence": best_mc,
            "is_expectancy": round(best_score, 3) if best_score is not None else None,
            "oos_trades": oos.get("n_trades", 0),
            "oos_win_rate": oos.get("win_rate", 0.0),
            "oos_net": oos.get("net_profit", 0.0),
            "oos_profit_factor": oos.get("profit_factor", 0.0),
            "oos_expectancy": oos.get("expectancy", 0.0),
        })
        start += step

    summary = _summarize(folds, cfg.capital)
    return {"folds": folds, "summary": summary}


def _summarize(folds: list[dict], capital: float) -> dict:
    if not folds:
        return {"n_folds": 0, "message": "Pas assez de données pour une fenêtre IS+OOS."}

    total_net = sum(f["oos_net"] for f in folds)
    total_trades = sum(f["oos_trades"] for f in folds)
    profitable = sum(1 for f in folds if f["oos_net"] > 0)
    expectancies = [f["oos_expectancy"] for f in folds if f["oos_trades"] > 0]
    return {
        "n_folds": len(folds),
        "oos_total_net": round(total_net, 2),
        "oos_total_return_pct": round(total_net / capital * 100, 2),
        "oos_total_trades": total_trades,
        "profitable_folds": f"{profitable}/{len(folds)}",
        "oos_mean_expectancy": round(sum(expectancies) / len(expectancies), 3) if expectancies else 0.0,
    }


def print_walkforward(result: dict) -> None:
    s = result["summary"]
    print("=" * 92)
    print("VALIDATION WALK-FORWARD (résultats OUT-OF-SAMPLE uniquement)")
    print("=" * 92)
    if s.get("n_folds", 0) == 0:
        print(s.get("message"))
        return

    hdr = f"{'fold':>4} {'OOS bougies':>16} {'min_conf':>9} {'trades':>7} {'winrate%':>9} {'net$':>9} {'PF':>6} {'exp(R/$)':>9}"
    print(hdr)
    print("-" * 92)
    for i, f in enumerate(result["folds"]):
        lo, hi = f["oos_range"]
        print(
            f"{i:>4} {f'{lo}-{hi}':>16} {f['chosen_min_confidence']:>9} "
            f"{f['oos_trades']:>7} {f['oos_win_rate']:>9} {f['oos_net']:>9} "
            f"{f['oos_profit_factor']:>6} {f['oos_expectancy']:>9}"
        )
    print("-" * 92)
    print(f"  Folds                 : {s['n_folds']}")
    print(f"  Folds profitables     : {s['profitable_folds']}")
    print(f"  Net OOS cumulé        : {s['oos_total_net']} $  ({s['oos_total_return_pct']} %)")
    print(f"  Trades OOS cumulés    : {s['oos_total_trades']}")
    print(f"  Espérance OOS moyenne : {s['oos_mean_expectancy']}")
    print("=" * 92)
