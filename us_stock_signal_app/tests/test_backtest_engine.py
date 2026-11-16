from __future__ import annotations

import math
import unittest
from datetime import datetime, timedelta, timezone

from backtest_engine import backtest_symbol_signals, selected_rule, simulate_recommended_trade, simulate_rule_trade


def make_bars(closes: list[float]) -> list[dict]:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    bars = []
    for index, close in enumerate(closes):
        bars.append(
            {
                "time": (start + timedelta(days=index)).isoformat().replace("+00:00", "Z"),
                "open": close * 0.998,
                "high": close * 1.012,
                "low": close * 0.988,
                "close": close,
                "volume": 1_000_000 + (index % 7) * 80_000,
            }
        )
    return bars


def make_ohlc(rows: list[tuple[float, float, float, float]]) -> list[dict]:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return [
        {
            "time": (start + timedelta(days=index)).isoformat().replace("+00:00", "Z"),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1_000_000,
        }
        for index, (open_price, high, low, close) in enumerate(rows)
    ]


def base_config() -> dict:
    return {
        "provider": "demo",
        "alerts": {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_deep_oversold": 25,
            "rsi_recovery": 35,
            "rsi_overheated": 70,
            "ma_periods": [20, 60, 120],
            "volume_period": 20,
            "volume_spike_multiple": 2.0,
            "large_cap_volume_spike_multiple": 1.5,
            "gap_pct": 3.0,
            "ma_distance_pct": {},
        },
        "positions": [{"symbol": "TEST", "held": True, "average_entry_price": 10}],
        "alert_preferences": {},
    }


class BacktestEngineTests(unittest.TestCase):
    def test_backtest_measures_forward_returns_after_signal_date(self) -> None:
        closes = [100 + math.sin(index / 7) * 4 + index * 0.03 for index in range(260)]
        payload = backtest_symbol_signals("TEST", make_bars(closes), base_config(), min_score=0, lookback=80, cooldown_days=10)

        self.assertGreater(payload["summary"]["signals"], 0)
        self.assertLessEqual(max(event["index"] for event in payload["events"]), len(closes) - 61)
        self.assertEqual(payload["events"][-1]["entry_index"], payload["events"][-1]["index"] + 1)
        self.assertIn("rule_result", payload["events"][0])
        self.assertIn("20d", payload["events"][0]["returns"])
        self.assertIn("60d", payload["events"][0]["max_drawdown"])
        self.assertIsNotNone(payload["summary"]["avg_return_20d"])
        self.assertIn("avg_rule_return", payload["summary"])
        self.assertEqual(payload["mode"], "watch")

    def test_backtest_returns_empty_when_history_is_too_short(self) -> None:
        closes = [100 + index * 0.1 for index in range(180)]
        payload = backtest_symbol_signals("TEST", make_bars(closes), base_config(), min_score=0)

        self.assertEqual(payload["summary"]["signals"], 0)
        self.assertEqual(payload["evaluated_days"], 0)
        self.assertEqual(payload["events"], [])

    def test_growth_trade_uses_next_open_entry_and_stop_loss(self) -> None:
        bars = make_ohlc(
            [
                (99, 101, 98, 100),
                (100, 102, 92, 94),
            ]
        )

        result = simulate_rule_trade(bars, 1, selected_rule("growth"))

        self.assertEqual(result["exit_reason"], "손절")
        self.assertEqual(result["return_pct"], -8.0)
        self.assertEqual(result["holding_days"], 1)

    def test_growth_trade_handles_partial_profit_and_trailing_exit(self) -> None:
        bars = make_ohlc(
            [
                (99, 101, 98, 100),
                (100, 116, 99, 115),
                (115, 126, 113, 125),
                (125, 127, 113, 114),
            ]
        )

        result = simulate_rule_trade(bars, 1, selected_rule("growth"))

        self.assertEqual(result["exit_reason"], "트레일링")
        self.assertTrue(result["target_1_hit"])
        self.assertTrue(result["target_2_hit"])
        self.assertEqual([part["label"] for part in result["parts"]], ["1차익절", "2차익절"])
        self.assertGreater(result["return_pct"], 16)

    def test_recommended_hold90_trade_does_not_force_sell_early(self) -> None:
        bars = make_ohlc(
            [
                (99, 101, 98, 100),
                (100, 118, 92, 110),
                (110, 122, 105, 120),
                (120, 125, 108, 121),
            ]
        )

        rule = selected_rule("hold90")
        rule["max_holding_days"] = 3
        result = simulate_recommended_trade(bars, 1)
        custom_result = simulate_rule_trade(bars, 1, rule)

        self.assertEqual(result["exit_reason"], "90일종료")
        self.assertEqual(custom_result["exit_reason"], "3일종료")
        self.assertFalse(custom_result["target_1_hit"])
        self.assertFalse(custom_result["target_2_hit"])
        self.assertEqual(custom_result["return_pct"], 21.0)

    def test_growth_structure_rule_exits_after_support_breakdown(self) -> None:
        bars = make_ohlc(
            [
                (99, 101, 98, 100),
                (100, 105, 99, 104),
                (104, 106, 103, 105),
                (105, 106, 102, 103),
                (103, 104, 93, 93.5),
                (93.4, 94, 92.8, 93),
            ]
        )

        result = simulate_rule_trade(bars, 1, selected_rule("growth_structure"))

        self.assertEqual(result["exit_reason"], "구조손절")
        self.assertTrue(result["structure_stop_hit"])
        self.assertIn("S1", result["structure_reason"])
        self.assertEqual(result["exit_index"], 5)
        self.assertEqual(result["exit_price"], 93.4)


if __name__ == "__main__":
    unittest.main()
