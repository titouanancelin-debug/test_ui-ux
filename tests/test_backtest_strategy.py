"""Tests d'intégration : stratégie, backtest, multi-timeframe, espérance."""
from scalping.data import synthetic_ohlcv
from scalping.config import StrategyConfig
from scalping.backtest import run_backtest
from scalping.strategy import prepare, generate_signal, mtf_trend_series
from scalping.pattern_stats import evaluate_patterns
from scalping.walkforward import walk_forward


def test_backtest_runs_and_reports():
    res = run_backtest(synthetic_ohlcv(n=1000))
    assert "metrics" in res
    assert len(res["equity_curve"]) > 0
    m = res["metrics"]
    assert "n_trades" in m


def test_backtest_window_subset():
    df = synthetic_ohlcv(n=1500)
    cfg = StrategyConfig()
    prep = prepare(df, cfg)
    full = run_backtest(df, cfg, prep=prep)["metrics"].get("n_trades", 0)
    part = run_backtest(df, cfg, prep=prep, start_idx=800, end_idx=1200)["metrics"].get("n_trades", 0)
    # Une fenêtre restreinte ne peut pas produire plus de trades que tout l'historique.
    assert part <= full


def test_walk_forward_runs():
    df = synthetic_ohlcv(n=4000)
    res = walk_forward(df, is_bars=1500, oos_bars=500)
    assert "summary" in res
    assert res["summary"]["n_folds"] >= 1
    for f in res["folds"]:
        assert f["oos_range"][0] >= f["is_range"][1]  # OOS après IS (anti-lookahead)


def test_signal_shape():
    df = synthetic_ohlcv(n=600)
    cfg = StrategyConfig()
    prep = prepare(df, cfg)
    sig = None
    for i in range(100, len(df)):
        sig = generate_signal(prep, i, cfg)
        if sig:
            break
    if sig is not None:
        assert sig.direction in ("BUY", "SELL")
        assert 0.0 <= sig.confidence <= 1.0
        if sig.direction == "BUY":
            assert sig.stop < sig.entry
        else:
            assert sig.stop > sig.entry


def test_mtf_trend_no_lookahead_values():
    df = synthetic_ohlcv(n=300)
    cfg = StrategyConfig()
    s = mtf_trend_series(df, 3, cfg)
    assert len(s) == len(df)
    assert set(s.unique()).issubset({-1, 0, 1})
    # Les toutes premières bougies n'ont pas de TF supérieur clôturé -> 0.
    assert s.iloc[0] == 0


def test_mtf_mode_runs():
    cfg = StrategyConfig()
    cfg.use_mtf = True
    res = run_backtest(synthetic_ohlcv(n=1000), cfg)
    assert "metrics" in res


def test_evaluate_patterns_returns_table():
    df = synthetic_ohlcv(n=2000)
    table = evaluate_patterns(df, min_occurrences=3)
    # colonnes attendues
    for col in ("pattern", "type", "n", "win_rate", "expectancy_R"):
        assert col in table.columns
    assert len(table) > 0
