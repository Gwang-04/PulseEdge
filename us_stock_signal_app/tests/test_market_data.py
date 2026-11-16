from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import market_data
from app import analyze_watchlist, summarize_data_freshness


def base_config() -> dict:
    return {
        "provider": "demo",
        "watchlist": ["AAPL"],
        "positions": [{"symbol": "AAPL", "held": True}],
        "alpaca": {"feed": "iex", "timeframe": "1Day", "adjustment": "split", "lookback_days": 260},
    }


def sample_bars() -> list[dict]:
    return [
        {"time": "2026-09-14T04:00:00Z", "open": 99, "high": 101, "low": 98, "close": 100, "volume": 1000},
        {"time": "2026-09-15T04:00:00Z", "open": 100, "high": 103, "low": 99, "close": 102, "volume": 1200},
    ]


class MarketDataCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        market_data._BAR_CACHE.clear()
        market_data._BAR_STATUS.clear()
        market_data._VIX_CACHE.clear()
        market_data.reset_market_data_usage()

    def tearDown(self) -> None:
        market_data._BAR_CACHE.clear()
        market_data._BAR_STATUS.clear()
        market_data._VIX_CACHE.clear()
        market_data.reset_market_data_usage()

    def test_fetch_bars_reuses_cache_and_returns_copy(self) -> None:
        with patch("market_data.generate_demo_bars", return_value=sample_bars()) as generate:
            first = market_data.fetch_bars("AAPL", base_config())
            first[0]["close"] = 999
            second = market_data.fetch_bars("AAPL", base_config())

        self.assertEqual(generate.call_count, 1)
        self.assertEqual(second[0]["close"], 100)
        usage = market_data.market_data_usage_snapshot()
        self.assertEqual(usage["bar_cache"]["hits"], 1)
        self.assertEqual(usage["bar_cache"]["misses"], 1)
        self.assertEqual(usage["bar_cache"]["hit_rate_pct"], 50.0)
        self.assertEqual(usage["demo_generations"], 1)
        status = market_data.bar_data_status("AAPL", base_config())
        self.assertEqual(status["state"], "fresh")
        self.assertTrue(status["served_from_cache"])
        self.assertFalse(status["stale"])

    def test_cache_key_changes_when_feed_changes(self) -> None:
        config = base_config()
        other_config = base_config()
        other_config["alpaca"]["feed"] = "delayed_sip"

        with patch("market_data.generate_demo_bars", return_value=sample_bars()) as generate:
            market_data.fetch_bars("AAPL", config)
            market_data.fetch_bars("AAPL", other_config)

        self.assertEqual(generate.call_count, 2)

    def test_cache_key_changes_when_adjustment_changes(self) -> None:
        config = base_config()
        other_config = base_config()
        other_config["alpaca"]["adjustment"] = "raw"

        self.assertNotEqual(market_data.bars_cache_key("AAPL", config), market_data.bars_cache_key("AAPL", other_config))

    def test_alpaca_error_uses_recent_stale_cache(self) -> None:
        config = base_config()
        config["provider"] = "alpaca"
        cache_key = market_data.bars_cache_key("AAPL", config)
        market_data.store_bars_cache(cache_key, sample_bars())
        market_data._BAR_CACHE[cache_key]["stored_at"] -= market_data.BAR_CACHE_TTL_SECONDS + 1

        with patch("market_data.fetch_alpaca_bars", side_effect=RuntimeError("temporary outage")):
            bars = market_data.fetch_bars("AAPL", config)

        self.assertEqual(bars, sample_bars())
        self.assertEqual(market_data.market_data_usage_snapshot()["bar_cache"]["stale_fallbacks"], 1)
        status = market_data.bar_data_status("AAPL", config)
        self.assertEqual(status["state"], "stale")
        self.assertTrue(status["served_from_cache"])
        self.assertTrue(status["stale"])

    def test_completed_daily_end_excludes_open_session_bar(self) -> None:
        before_close = datetime(2026, 9, 22, 15, 0, tzinfo=timezone.utc)
        after_close = datetime(2026, 9, 22, 21, 0, tzinfo=timezone.utc)

        self.assertEqual(
            market_data.completed_daily_bars_end(before_close),
            datetime(2026, 9, 22, 3, 59, 59, 999999, tzinfo=timezone.utc),
        )
        self.assertEqual(
            market_data.completed_daily_bars_end(after_close),
            datetime(2026, 9, 23, 3, 59, 59, 999999, tzinfo=timezone.utc),
        )

    def test_usage_snapshot_counts_vix_cache(self) -> None:
        config = base_config()
        config["fear"] = {"source": "demo", "lookback_days": 30}

        first = market_data.fetch_vix_history(config)
        second = market_data.fetch_vix_history(config)
        usage = market_data.market_data_usage_snapshot()

        self.assertEqual(first, second)
        self.assertEqual(usage["vix"]["cache_misses"], 1)
        self.assertEqual(usage["vix"]["cache_hits"], 1)
        self.assertEqual(usage["vix"]["hit_rate_pct"], 50.0)

    def test_vix_cache_reuses_daily_data_for_one_hour(self) -> None:
        config = base_config()
        config["fear"] = {"source": "demo", "lookback_days": 30}

        with patch("market_data.generate_demo_vix_history", return_value=[{"time": "2026-09-28", "close": 16.07}]) as generate:
            market_data.fetch_vix_history(config)
            market_data._VIX_CACHE["demo:30"]["stored_at"] -= 30 * 60
            market_data.fetch_vix_history(config)
            market_data._VIX_CACHE["demo:30"]["stored_at"] -= 31 * 60
            market_data.fetch_vix_history(config)

        self.assertEqual(generate.call_count, 2)

    def test_cboe_vix_parser_uses_close_and_iso_date(self) -> None:
        csv_text = "DATE,OPEN,HIGH,LOW,CLOSE\n09/25/2026,15.61,15.94,14.68,14.87\n09/28/2026,16.16,16.62,15.68,16.07\n"

        with patch("market_data.fetch_remote_text", return_value=csv_text):
            bars = market_data.fetch_cboe_vix_history(30)

        self.assertEqual(bars[-1], {"time": "2026-09-28", "close": 16.07})

    def test_cboe_failure_falls_back_to_fred_without_demo(self) -> None:
        config = base_config()
        config["fear"] = {"source": "cboe", "lookback_days": 30, "fallback_to_demo": True}
        fred_bars = [{"time": "2026-09-28", "close": 16.07}]

        with (
            patch("market_data.fetch_cboe_vix_history", side_effect=RuntimeError("cboe down")),
            patch("market_data.fetch_fred_vix_history", return_value=fred_bars),
        ):
            payload = market_data.fetch_vix_history(config)

        self.assertEqual(payload["source"], "fred")
        self.assertTrue(payload["fallback"])
        self.assertEqual(payload["fallback_from"], "cboe")
        self.assertEqual(payload["bars"], fred_bars)
        self.assertNotIn("error", payload)


class AnalyzeWatchlistTests(unittest.TestCase):
    def test_parallel_analysis_preserves_symbol_order_and_errors(self) -> None:
        config = base_config()
        config["watchlist"] = ["MSFT", "BAD", "AAPL"]
        watch_config = {**config, "positions": []}

        def fake_fetch_bars(symbol: str, _: dict) -> list[dict]:
            if symbol == "BAD":
                raise RuntimeError("boom")
            return sample_bars()

        def fake_analyze_symbol(symbol: str, _: list[dict], active_config: dict) -> dict:
            return {
                "symbol": symbol,
                "position_count": len(active_config.get("positions", [])),
                "alert_level": "대기",
                "signals": [],
            }

        with (
            patch("app.fetch_bars", side_effect=fake_fetch_bars),
            patch("app.analyze_symbol", side_effect=fake_analyze_symbol),
        ):
            results, watch_results = analyze_watchlist(config["watchlist"], config, watch_config)

        self.assertEqual([result["symbol"] for result in results], ["MSFT", "BAD", "AAPL"])
        self.assertEqual([result["symbol"] for result in watch_results], ["MSFT", "BAD", "AAPL"])
        self.assertEqual(results[1]["alert_level"], "오류")
        self.assertEqual(results[0]["position_count"], 1)
        self.assertEqual(watch_results[0]["position_count"], 0)

    def test_freshness_summary_reports_stale_symbols(self) -> None:
        summary = summarize_data_freshness(
            [
                {
                    "symbol": "AAPL",
                    "data_status": {
                        "state": "fresh",
                        "stale": False,
                        "served_from_cache": False,
                        "fetched_at": "2026-09-29T01:00:00+00:00",
                        "last_bar": "2026-09-28T04:00:00Z",
                    },
                },
                {
                    "symbol": "MSFT",
                    "data_status": {
                        "state": "stale",
                        "stale": True,
                        "served_from_cache": True,
                        "fetched_at": "2026-09-29T00:30:00+00:00",
                        "last_bar": "2026-09-28T04:00:00Z",
                    },
                },
            ]
        )

        self.assertEqual(summary["state"], "stale")
        self.assertEqual(summary["stale_symbols"], ["MSFT"])
        self.assertEqual(summary["served_from_cache_count"], 1)
        self.assertEqual(summary["fetched_at"], "2026-09-29T00:30:00+00:00")


if __name__ == "__main__":
    unittest.main()
