from __future__ import annotations

import math
import unittest
from datetime import datetime, timedelta, timezone

from signal_engine import (
    add_chart_overlay_signals,
    analyze_symbol,
    apply_market_regime,
    bollinger_bands,
    build_vix_state,
    build_signal_score,
    ichimoku_lines,
    rank_alert,
    rsi,
    rsi_score_context,
    score_stage,
    sma,
    support_resistance_levels,
    support_resistance_score_context,
)


def make_bars(
    closes: list[float],
    volumes: list[float] | None = None,
    opens: list[float] | None = None,
    highs: list[float] | None = None,
    lows: list[float] | None = None,
) -> list[dict]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = []
    for index, close in enumerate(closes):
        bars.append(
            {
                "time": (start + timedelta(days=index)).isoformat().replace("+00:00", "Z"),
                "open": opens[index] if opens else close,
                "high": highs[index] if highs else close * 1.01,
                "low": lows[index] if lows else close * 0.99,
                "close": close,
                "volume": volumes[index] if volumes else 1_000_000,
            }
        )
    return bars


class IndicatorTests(unittest.TestCase):
    def test_sma_waits_for_full_period(self) -> None:
        self.assertEqual(sma([1, 2, 3], 3), [None, None, 2.0])

    def test_rsi_drops_on_persistent_losses(self) -> None:
        values = [100 - index for index in range(30)]
        output = rsi(values, 14)
        self.assertLess(output[-1], 5)

    def test_rsi_matches_wilder_reference_value(self) -> None:
        values = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
        self.assertAlmostEqual(rsi(values, 14)[-1], 70.4641, places=4)

    def test_bollinger_bands_wait_for_period_and_wrap_price(self) -> None:
        values = [float(index) for index in range(1, 21)]
        bands = bollinger_bands(values, 20, 2)
        self.assertIsNone(bands["middle"][18])
        self.assertAlmostEqual(bands["middle"][19], 10.5)
        self.assertGreater(bands["upper"][19], values[-1])
        self.assertLess(bands["lower"][19], values[0])

    def test_ichimoku_lines_use_high_low_midpoints(self) -> None:
        highs = [float(index) for index in range(1, 61)]
        lows = [high - 1 for high in highs]
        lines = ichimoku_lines(highs, lows)
        self.assertAlmostEqual(lines["tenkan"][8], 4.5)
        self.assertAlmostEqual(lines["kijun"][25], 13.0)
        self.assertAlmostEqual(lines["span_b"][51], 26.0)


class AnalysisTests(unittest.TestCase):
    def base_config(self) -> dict:
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
            "positions": [],
            "alert_preferences": {},
        }

    def test_detects_oversold_signal(self) -> None:
        closes = [100 + index * 0.1 for index in range(210)] + [118, 115, 111, 106, 101, 96, 91, 86, 81, 77]
        config = self.base_config()
        result = analyze_symbol("TEST", make_bars(closes), config)
        signal_types = {signal["type"] for signal in result["signals"]}
        self.assertTrue({"RSI_OVERSOLD", "RSI_DEEP_OVERSOLD"} & signal_types)
        latest = result["bars"][-1]
        self.assertIsNotNone(latest["bb_upper"])
        self.assertIsNotNone(latest["ichimoku_kijun"])

    def test_empty_watch_score_starts_at_neutral_50(self) -> None:
        score = build_signal_score([], None, "대기", [])

        self.assertEqual(score["value"], 50)
        self.assertEqual(score["stage"], "대기")

    def test_context_only_watch_score_uses_review_language(self) -> None:
        score = build_signal_score(
            [],
            None,
            "대기",
            [
                {
                    "type": "SUPPORT_RESISTANCE_STATE",
                    "points": 9,
                    "level": "상태",
                    "message": "지지선 근접",
                },
                {
                    "type": "MA_TREND_STATE",
                    "points": 6,
                    "level": "상태",
                    "message": "이평 추세 양호",
                },
                {
                    "type": "ICHIMOKU_STATE",
                    "points": 7,
                    "level": "상태",
                    "message": "일목 구름 위",
                },
            ],
        )

        self.assertEqual(score["value"], 72)
        self.assertEqual(score["stage"], "자리검토")

    def test_rsi_state_score_is_more_granular(self) -> None:
        self.assertEqual(rsi_score_context("TEST", 40.0, False)["points"], 4)
        self.assertEqual(rsi_score_context("TEST", 45.0, False)["points"], 2)
        self.assertEqual(rsi_score_context("TEST", 50.0, False)["points"], 0)
        self.assertEqual(rsi_score_context("TEST", 65.0, False)["points"], -3)

    def test_support_resistance_detects_nearest_levels(self) -> None:
        closes = [100.0 + (index % 20 - 10) * 0.18 for index in range(180)]
        highs = [close + 0.8 for close in closes]
        lows = [close - 0.8 for close in closes]
        for index in (35, 82, 124):
            lows[index] = 96.0 + index * 0.002
        for index in (48, 96, 142):
            highs[index] = 108.0 + index * 0.002
        closes[-1] = 101.0
        highs[-1] = 101.8
        lows[-1] = 100.2

        levels = support_resistance_levels("TEST", make_bars(closes, highs=highs, lows=lows), closes[-1])

        self.assertIsNotNone(levels["nearest_support"])
        self.assertIsNotNone(levels["nearest_resistance"])
        self.assertLess(levels["nearest_support"]["price"], closes[-1])
        self.assertGreater(levels["nearest_resistance"]["price"], closes[-1])

    def test_position_support_resistance_uses_entry_date_scope(self) -> None:
        closes = [100.0] * 80 + [108.0 + (index % 6) * 0.35 for index in range(50)]
        highs = [close + 0.8 for close in closes]
        lows = [close - 0.8 for close in closes]
        for index in (20, 44, 68):
            highs[index] = 150.0
        highs[96] = 118.0
        lows[92] = 104.0
        closes[-1] = 112.0
        highs[-1] = 113.0
        lows[-1] = 111.0

        levels = support_resistance_levels(
            "TEST",
            make_bars(closes, highs=highs, lows=lows),
            closes[-1],
            entry_date="2026-03-22",
            average_entry_price=106.0,
        )

        self.assertEqual(levels["scope"], "position")
        self.assertEqual(levels["scope_label"], "매수일 이후")
        self.assertIsNotNone(levels["nearest_support"])
        self.assertIsNotNone(levels["nearest_resistance"])
        self.assertLess(levels["nearest_resistance"]["price"], 125.0)

    def test_support_resistance_context_rewards_near_support(self) -> None:
        levels = {
            "nearest_support": {"label": "S1", "distance_pct": -1.2},
            "nearest_resistance": {"label": "R1", "distance_pct": 8.5},
        }
        context = support_resistance_score_context("TEST", levels, False)

        self.assertIsNotNone(context)
        self.assertGreater(context["points"], 0)
        self.assertEqual(context["type"], "SUPPORT_RESISTANCE_STATE")

    def test_unheld_symbol_without_alert_uses_context_score(self) -> None:
        closes = [100 + (index % 10 - 5) * 0.1 for index in range(220)]
        config = self.base_config()
        result = analyze_symbol("TEST", make_bars(closes), config)

        self.assertEqual(result["signals"], [])
        self.assertEqual(result["alert_level"], "대기")
        self.assertIn("현재 등급은 대기", result["summary"])
        self.assertEqual(result["score"]["mode"], "watch")
        self.assertEqual(result["score"]["label"], "진입점수")
        self.assertGreater(result["score"]["value"], 50)
        self.assertIn("MA_TREND_STATE", {driver["type"] for driver in result["score"]["drivers"]})

    def test_unheld_bearish_volume_with_low_rsi_is_fear_interest(self) -> None:
        closes = [100 + index * 0.1 for index in range(210)] + [118, 115, 111, 106, 101, 96, 91, 86, 81, 77]
        volumes = [1_000_000] * (len(closes) - 1) + [3_000_000]
        config = self.base_config()
        result = analyze_symbol("TEST", make_bars(closes, volumes=volumes), config)
        bearish_volume = next(signal for signal in result["signals"] if signal["type"] == "BEARISH_VOLUME_SPIKE")

        self.assertEqual(bearish_volume["level"], "공포관심")
        self.assertEqual(result["alert_level"], "공포관심")
        self.assertGreaterEqual(result["score"]["value"], 60)
        self.assertIn("BEARISH_VOLUME_SPIKE", {driver["type"] for driver in result["score"]["drivers"]})

    def test_ichimoku_recovery_alone_is_not_buy_opportunity(self) -> None:
        closes = [100.0] * 60 + [99.0, 101.0]
        latest_index = len(closes) - 1
        previous_index = latest_index - 1
        spans = [100.0] * len(closes)
        bollinger = {"lower": [None] * len(closes)}
        ichimoku = {"span_a": spans, "span_b": [98.0] * len(closes)}
        sma_values = {20: [95.0] * len(closes), 60: [96.0] * len(closes)}
        signals: list[dict] = []

        add_chart_overlay_signals(
            "AAPL",
            signals,
            closes,
            sma_values,
            bollinger,
            ichimoku,
            latest_index,
            previous_index,
            62.0,
            0.8,
            self.base_config()["alerts"],
            False,
        )
        alert_level = rank_alert(signals)
        score = build_signal_score(signals, None, alert_level)

        self.assertEqual(alert_level, "반등후보")
        self.assertEqual(score["value"], 62)
        self.assertNotEqual(score["stage"], "진입검토")
        self.assertEqual(score["stage"], "반등체크")

    def test_ichimoku_recovery_needs_rsi_and_volume_for_opportunity(self) -> None:
        closes = [100.0] * 60 + [99.0, 101.0]
        latest_index = len(closes) - 1
        previous_index = latest_index - 1
        spans = [100.0] * len(closes)
        bollinger = {"lower": [None] * len(closes)}
        ichimoku = {"span_a": spans, "span_b": [98.0] * len(closes)}
        sma_values = {20: [99.0] * len(closes), 60: [98.0] * len(closes)}
        signals: list[dict] = []

        add_chart_overlay_signals(
            "AAPL",
            signals,
            closes,
            sma_values,
            bollinger,
            ichimoku,
            latest_index,
            previous_index,
            52.0,
            1.3,
            self.base_config()["alerts"],
            False,
        )
        alert_level = rank_alert(signals)
        score = build_signal_score(signals, None, alert_level)

        self.assertEqual(alert_level, "기회후보")
        self.assertEqual(score["value"], 72)
        self.assertEqual(score["stage"], "진입검토")

    def test_held_bearish_volume_with_low_rsi_remains_risk(self) -> None:
        closes = [100 + index * 0.1 for index in range(210)] + [118, 115, 111, 106, 101, 96, 91, 86, 81, 77]
        volumes = [1_000_000] * (len(closes) - 1) + [3_000_000]
        config = self.base_config()
        config["positions"] = [
            {
                "symbol": "TEST",
                "held": True,
                "average_entry_price": 100,
                "quantity": 10,
                "entry_date": "2026-01-01",
                "stop_loss_pct": -7,
                "trailing_stop_pct": -8,
            }
        ]
        result = analyze_symbol("TEST", make_bars(closes, volumes=volumes), config)
        bearish_volume = next(signal for signal in result["signals"] if signal["type"] == "BEARISH_VOLUME_SPIKE")

        self.assertEqual(bearish_volume["level"], "위험")
        self.assertEqual(result["alert_level"], "위험")
        self.assertEqual(result["score"]["mode"], "position")
        self.assertGreaterEqual(result["score"]["value"], 84)

    def test_position_profit_signal_uses_only_highest_band(self) -> None:
        closes = [100 + index * 0.12 for index in range(220)]
        config = self.base_config()
        config["positions"] = [
            {
                "symbol": "TEST",
                "held": True,
                "average_entry_price": 85,
                "quantity": 10,
                "entry_date": "2026-01-01",
                "stop_loss_pct": -7,
                "trailing_stop_pct": -8,
            }
        ]

        result = analyze_symbol("TEST", make_bars(closes), config)
        signal_types = {signal["type"] for signal in result["signals"]}

        self.assertIn("PROFIT_30", signal_types)
        self.assertNotIn("PROFIT_10", signal_types)
        self.assertNotIn("PROFIT_20", signal_types)
        self.assertEqual(result["position"]["suggested_action"], "수익보호")

    def test_position_score_stage_uses_trim_language(self) -> None:
        self.assertEqual(score_stage(25, True), "매우안정")
        self.assertEqual(score_stage(40, True), "안정보유")
        self.assertEqual(score_stage(80, True), "관리강화")
        self.assertEqual(score_stage(90, True), "강한관리")

    def test_stable_position_score_can_drop_below_50(self) -> None:
        closes = [100 + index * 0.015 + math.sin((index + 3) / 4 * 6.28318) * 0.2 for index in range(220)]
        config = self.base_config()
        config["positions"] = [
            {
                "symbol": "TEST",
                "held": True,
                "average_entry_price": 100,
                "quantity": 10,
                "entry_date": "2026-01-01",
                "stop_loss_pct": -7,
                "trailing_stop_pct": -8,
            }
        ]

        result = analyze_symbol("TEST", make_bars(closes), config)

        self.assertLess(result["score"]["value"], 50)
        self.assertEqual(result["score"]["stage"], "안정보유")

    def test_alert_preference_can_turn_off_signal(self) -> None:
        closes = [100 + index * 0.1 for index in range(210)] + [118, 115, 111, 106, 101, 96, 91, 86, 81, 77]
        config = self.base_config()
        config["alert_preferences"] = {"RSI_DEEP_OVERSOLD": "off", "RSI_OVERSOLD": "off"}
        result = analyze_symbol("TEST", make_bars(closes), config)
        visible_types = {signal["type"] for signal in result["signals"]}
        all_types = {signal["type"] for signal in result["all_signals"]}
        self.assertFalse({"RSI_OVERSOLD", "RSI_DEEP_OVERSOLD"} & visible_types)
        self.assertTrue({"RSI_OVERSOLD", "RSI_DEEP_OVERSOLD"} & all_types)

    def test_position_stop_review_signal(self) -> None:
        closes = [100 + index * 0.05 for index in range(150)] + [106, 104, 101, 98, 95, 92]
        config = self.base_config()
        config["positions"] = [
            {
                "symbol": "TEST",
                "held": True,
                "average_entry_price": 100,
                "quantity": 10,
                "entry_date": "2026-01-01",
                "stop_loss_pct": -7,
                "trailing_stop_pct": -8,
            }
        ]
        result = analyze_symbol("TEST", make_bars(closes), config)
        signal_types = {signal["type"] for signal in result["signals"]}
        self.assertIn("STOP_REVIEW", signal_types)
        self.assertLessEqual(result["position"]["return_pct"], -7)
        self.assertAlmostEqual(result["position"]["stop_price"], 93.0)
        self.assertLessEqual(result["position"]["stop_buffer_pct"], 0)

    def test_position_stop_buffer_warning_before_stop(self) -> None:
        closes = [100 + index * 0.01 for index in range(150)] + [95.0]
        config = self.base_config()
        config["positions"] = [
            {
                "symbol": "TEST",
                "held": True,
                "average_entry_price": 100,
                "quantity": 10,
                "entry_date": "2026-05-31",
                "stop_loss_pct": -7,
                "trailing_stop_pct": -8,
            }
        ]

        result = analyze_symbol("TEST", make_bars(closes), config)
        signal_types = {signal["type"] for signal in result["signals"]}

        self.assertIn("STOP_BUFFER_REVIEW", signal_types)
        self.assertGreater(result["position"]["stop_buffer_pct"], 0)
        self.assertLessEqual(result["position"]["stop_buffer_pct"], 3)
        self.assertEqual(result["position"]["suggested_action"], "위험선근접")

    def test_position_support_breakdown_feeds_defense_component(self) -> None:
        closes = [100 + index * 0.01 for index in range(150)] + [95.0]
        config = self.base_config()
        config["positions"] = [
            {
                "symbol": "TEST",
                "held": True,
                "average_entry_price": 100,
                "quantity": 10,
                "entry_date": "2026-01-01",
                "stop_loss_pct": -7,
                "trailing_stop_pct": -8,
            }
        ]

        result = analyze_symbol("TEST", make_bars(closes), config)
        signal_types = {signal["type"] for signal in result["signals"]}
        components = {component["key"]: component for component in result["score"]["components"]}

        self.assertIn("POSITION_SUPPORT_BREAKDOWN", signal_types)
        self.assertIn("POSITION_STRUCTURE_EXIT_REVIEW", signal_types)
        self.assertEqual(result["position"]["suggested_action"], "위험축소검토")
        self.assertGreaterEqual(components["defense"]["value"], 75)

    def test_vix_fear_downgrades_opportunity_signals(self) -> None:
        config = self.base_config()
        config["fear"] = {
            "elevated_threshold": 20,
            "fear_threshold": 25,
            "panic_threshold": 30,
            "spike_5d_pct": 20,
            "calming_5d_pct": -12,
        }
        results = [
            {"symbol": "SPY", "price": 500, "sma": {"120": 480}, "signals": [], "alert_level": "정상", "summary": "SPY"},
            {"symbol": "QQQ", "price": 420, "sma": {"120": 410}, "signals": [], "alert_level": "정상", "summary": "QQQ"},
            {"symbol": "TEST", "price": 100, "sma": {"120": 95}, "signals": [], "alert_level": "기회후보", "summary": "TEST"},
        ]
        vix_history = {
            "source": "demo",
            "fallback": False,
            "bars": [
                {"time": "2026-01-01", "close": 20},
                {"time": "2026-01-02", "close": 22},
                {"time": "2026-01-05", "close": 23},
                {"time": "2026-01-06", "close": 24},
                {"time": "2026-01-07", "close": 25},
                {"time": "2026-01-08", "close": 28},
            ],
        }

        market = apply_market_regime(results, config, vix_history)
        market_signal_types = {signal["type"] for signal in market["signals"]}
        test_signal_types = {signal["type"] for signal in results[2]["signals"]}

        self.assertEqual(market["vix"]["label"], "공포")
        self.assertIn("VIX_FEAR", market_signal_types)
        self.assertEqual(market["spy_ma120_distance_pct"], 4.17)
        self.assertEqual(market["qqq_ma120_distance_pct"], 2.44)
        self.assertEqual(results[2]["alert_level"], "주의")
        self.assertIn("MARKET_FILTER_DOWNGRADE", test_signal_types)

    def test_vix_state_explains_daily_close_freshness(self) -> None:
        config = self.base_config()
        vix = build_vix_state(
            {
                "source": "cboe",
                "fallback": False,
                "bars": [
                    {"time": "2026-01-01", "close": 17.0},
                    {"time": "2026-01-02", "close": 18.0},
                    {"time": "2026-01-05", "close": 19.0},
                    {"time": "2026-01-06", "close": 20.0},
                    {"time": "2026-01-07", "close": 21.0},
                    {"time": "2026-01-08", "close": 22.0},
                ],
            },
            config,
        )

        self.assertIsNotNone(vix)
        self.assertEqual(vix["cadence"], "daily_close")
        self.assertIn("CBOE 공식 일봉", vix["data_note"])
        self.assertIn("장중 실시간 아님", vix["data_note"])
        self.assertTrue(vix["freshness_label"])

    def test_vix_default_interpretation_uses_20_30_40_boundaries(self) -> None:
        config = self.base_config()
        expected = [
            (19.9, "보통", "정상"),
            (20.0, "주의", "주의"),
            (30.0, "공포", "위험"),
            (40.0, "극단공포", "위험"),
        ]

        for value, label, level in expected:
            with self.subTest(value=value):
                vix = build_vix_state(
                    {
                        "source": "fred",
                        "fallback": False,
                        "bars": [{"time": "2026-01-08", "close": value}],
                    },
                    config,
                )
                self.assertIsNotNone(vix)
                self.assertEqual(vix["label"], label)
                self.assertEqual(vix["level"], level)
                self.assertEqual(vix["thresholds"], {"elevated": 20.0, "fear": 30.0, "panic": 40.0})

    def test_vix_fear_adds_position_risk_signal(self) -> None:
        config = self.base_config()
        config["fear"] = {
            "elevated_threshold": 20,
            "fear_threshold": 25,
            "panic_threshold": 30,
            "spike_5d_pct": 20,
            "calming_5d_pct": -12,
        }
        results = [
            {"symbol": "SPY", "price": 500, "sma": {"120": 480}, "signals": [], "alert_level": "정상", "summary": "SPY"},
            {"symbol": "QQQ", "price": 420, "sma": {"120": 410}, "signals": [], "alert_level": "정상", "summary": "QQQ"},
            {
                "symbol": "TEST",
                "price": 100,
                "sma": {"120": 95},
                "signals": [],
                "alert_level": "정상",
                "summary": "TEST",
                "position": {"held": True, "symbol": "TEST"},
            },
        ]
        vix_history = {
            "source": "demo",
            "fallback": False,
            "bars": [{"time": f"2026-01-{day:02d}", "close": value} for day, value in enumerate([18, 19, 20, 21, 24, 31], start=1)],
        }

        apply_market_regime(results, config, vix_history)
        signal_types = {signal["type"] for signal in results[2]["signals"]}

        self.assertIn("VIX_POSITION_RISK", signal_types)
        self.assertEqual(results[2]["alert_level"], "위험")


if __name__ == "__main__":
    unittest.main()
