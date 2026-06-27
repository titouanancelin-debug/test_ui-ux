"""Tests cassure / retest et gestion du risque."""
from scalping.levels import Level, detect_breakout, detect_retest
from scalping.config import StrategyConfig
from scalping.risk import position_size, build_trade_plan


def test_detect_breakout_buy(make_df):
    rows = [(98, 98.2, 97.8, 98, 100) for _ in range(24)]
    rows.append((98, 101.2, 97.9, 101, 300))   # clôture franche au-dessus de 100 + volume
    df = make_df(rows)
    levels = [Level(100.0, "resistance", 2)]
    bo = detect_breakout(df, len(df) - 1, levels)
    assert bo is not None
    assert bo.direction == "BUY"
    assert bo.volume_ok


def test_detect_retest_buy(make_df):
    rows = [(98, 98.2, 97.8, 98, 100) for _ in range(15)]
    rows += [(102, 102.2, 101.8, 102, 100) for _ in range(5)]   # cassure à la hausse
    rows.append((100.5, 101.2, 99.9, 101, 150))                 # retest qui tient
    rows += [(101, 101.2, 100.8, 101, 100) for _ in range(3)]
    df = make_df(rows)
    levels = [Level(100.0, "resistance", 2)]
    rt = detect_retest(df, 20, levels)
    assert rt is not None
    assert rt.direction == "BUY"


def test_position_size_caps_notional():
    cfg = StrategyConfig()
    cfg.capital = 200
    cfg.risk_percent = 1.0     # risque 2$
    cfg.max_notional_pct = 1.0  # notionnel <= 200$
    # Stop très serré -> taille théorique énorme -> doit être plafonnée.
    qty, notional = position_size(100, 99.9, cfg)
    assert round(notional, 2) == 200.0
    assert round(qty, 4) == 2.0


def test_position_size_risk_based_when_not_capped():
    cfg = StrategyConfig()
    cfg.capital = 200
    cfg.risk_percent = 1.0
    cfg.max_notional_pct = 1.0
    qty, notional = position_size(100, 80, cfg)   # stop large -> petite taille
    assert round(qty, 4) == 0.1
    assert round(notional, 2) == 10.0


def test_build_trade_plan_rejects_wrong_side_stop():
    cfg = StrategyConfig()
    # BUY avec un stop AU-DESSUS de l'entrée : incohérent -> None
    assert build_trade_plan("BUY", 100, 101, cfg) is None
    # SELL avec un stop EN DESSOUS : incohérent -> None
    assert build_trade_plan("SELL", 100, 99, cfg) is None
