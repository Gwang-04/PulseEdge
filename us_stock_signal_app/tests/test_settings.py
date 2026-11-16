from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import settings
from app import build_data_health, watch_only_config


class AlpacaCredentialTests(unittest.TestCase):
    def test_save_and_delete_alpaca_credentials_in_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("OTHER=value\n", encoding="utf-8")

            with patch.object(settings, "ENV_PATH", env_path), patch.dict("os.environ", {}, clear=True):
                settings.save_alpaca_credentials("PKTEST1234", "SECRET5678")
                key_id, secret = settings.alpaca_credentials()
                self.assertEqual(key_id, "PKTEST1234")
                self.assertEqual(secret, "SECRET5678")
                self.assertIn("OTHER=value", env_path.read_text(encoding="utf-8"))

                status = settings.credential_status()
                self.assertTrue(status["alpaca_key_id_present"])
                self.assertTrue(status["alpaca_secret_present"])
                self.assertTrue(status["market_data_server_ready"])
                self.assertTrue(status["server_managed"])
                self.assertNotIn("alpaca_key_preview", status)

                settings.delete_alpaca_credentials()
                key_id, secret = settings.alpaca_credentials()
                self.assertEqual(key_id, "")
                self.assertEqual(secret, "")
                self.assertIn("OTHER=value", env_path.read_text(encoding="utf-8"))

    def test_rejects_missing_alpaca_credentials(self) -> None:
        with self.assertRaises(ValueError):
            settings.save_alpaca_credentials("", "SECRET")

    def test_watch_only_config_removes_positions_without_mutating_original(self) -> None:
        config = {"watchlist": ["PLTR"], "positions": [{"symbol": "PLTR", "held": True}], "alerts": {"rsi_period": 14}}

        output = watch_only_config(config)

        self.assertEqual(output["positions"], [])
        self.assertEqual(config["positions"], [{"symbol": "PLTR", "held": True}])

    def test_legacy_fred_vix_config_migrates_to_cboe(self) -> None:
        config = settings.normalize_config({"fear": {"source": "fred"}})

        self.assertEqual(config["fear"]["source"], "cboe")

    def test_data_health_summarizes_stock_and_vix_sources(self) -> None:
        config = settings.normalize_config({"provider": "alpaca", "watchlist": ["AAPL"], "positions": []})
        bars = [
            {"time": "2026-09-09T04:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000},
            {"time": "2026-09-10T04:00:00Z", "open": 101, "high": 103, "low": 100, "close": 102.25, "volume": 1200},
        ]
        vix_history = {
            "source": "fred",
            "fallback": False,
            "bars": [
                {"time": "2026-09-01", "close": 17.0},
                {"time": "2026-09-02", "close": 18.0},
                {"time": "2026-09-03", "close": 19.0},
                {"time": "2026-09-04", "close": 18.5},
                {"time": "2026-09-08", "close": 17.8},
                {"time": "2026-09-09", "close": 16.46},
            ],
        }

        with (
            patch("app.credential_status", return_value={"market_data_server_ready": True, "server_managed": True}),
            patch("app.fetch_bars", return_value=bars),
            patch("app.fetch_vix_history", return_value=vix_history),
        ):
            payload = build_data_health("AAPL", config)

        self.assertTrue(payload["ok"])
        self.assertEqual(config["provider"], "demo")
        self.assertEqual(payload["health_level"], "ok")
        self.assertEqual(payload["stock"]["symbol"], "AAPL")
        self.assertEqual(payload["stock"]["bars"], 2)
        self.assertEqual(payload["stock"]["latest_close"], 102.25)
        self.assertEqual(payload["vix"]["value"], 16.46)
        self.assertEqual(payload["vix"]["source"], "fred")
        self.assertFalse(payload["vix"]["fallback"])

    def test_client_config_isolated_by_guest_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            user_config_dir = Path(temp_dir) / "user_data"
            database_path = user_config_dir / "pulseedge.sqlite3"
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text('{"provider":"demo","watchlist":["SPY"],"positions":[]}', encoding="utf-8")

            with (
                patch.object(settings, "USER_CONFIG_DIR", user_config_dir),
                patch.object(settings, "DATABASE_PATH", database_path),
                patch.object(settings, "CONFIG_PATH", config_path),
            ):
                settings.save_config({"provider": "demo", "watchlist": ["AAPL"], "positions": []}, "guest-alpha01")
                settings.save_config({"provider": "demo", "watchlist": ["MSFT"], "positions": []}, "guest-bravo02")

                alpha = settings.load_config("guest-alpha01")
                bravo = settings.load_config("guest-bravo02")
                fresh = settings.load_config("guest-charlie03")

        self.assertIn("AAPL", alpha["watchlist"])
        self.assertNotIn("MSFT", alpha["watchlist"])
        self.assertIn("MSFT", bravo["watchlist"])
        self.assertNotIn("AAPL", bravo["watchlist"])
        self.assertIn("SPY", fresh["watchlist"])

    def test_legacy_guest_json_is_migrated_without_deleting_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            user_config_dir = root / "user_data"
            guest_dir = user_config_dir / "guests"
            guest_dir.mkdir(parents=True)
            database_path = user_config_dir / "pulseedge.sqlite3"
            config_path = root / "config.json"
            config_path.write_text('{"provider":"demo","watchlist":["SPY"],"positions":[]}', encoding="utf-8")
            legacy_path = guest_dir / "guest-legacy01.json"
            legacy_path.write_text(
                '{"provider":"demo","watchlist":["PLTR"],"positions":[{"symbol":"PLTR","held":true,"average_entry_price":100,"quantity":2}]}',
                encoding="utf-8",
            )

            with (
                patch.object(settings, "USER_CONFIG_DIR", user_config_dir),
                patch.object(settings, "DATABASE_PATH", database_path),
                patch.object(settings, "CONFIG_PATH", config_path),
            ):
                migrated = settings.load_config("guest-legacy01")
                legacy_path.write_text('{"provider":"demo","watchlist":["MSFT"],"positions":[]}', encoding="utf-8")
                loaded_again = settings.load_config("guest-legacy01")

            self.assertTrue(database_path.exists())
            self.assertTrue(legacy_path.exists())
            self.assertIn("PLTR", migrated["watchlist"])
            self.assertEqual(migrated["positions"][0]["average_entry_price"], 100.0)
            self.assertIn("PLTR", loaded_again["watchlist"])
            self.assertNotIn("MSFT", loaded_again["watchlist"])

    def test_sqlite_schema_and_replacement_are_user_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            user_config_dir = root / "user_data"
            database_path = user_config_dir / "pulseedge.sqlite3"
            config_path = root / "config.json"
            config_path.write_text('{"provider":"demo","watchlist":["SPY"],"positions":[]}', encoding="utf-8")

            with (
                patch.object(settings, "USER_CONFIG_DIR", user_config_dir),
                patch.object(settings, "DATABASE_PATH", database_path),
                patch.object(settings, "CONFIG_PATH", config_path),
            ):
                settings.save_config(
                    {
                        "provider": "demo",
                        "watchlist": ["AAPL", "NVDA"],
                        "positions": [
                            {
                                "symbol": "AAPL",
                                "held": True,
                                "average_entry_price": 190,
                                "quantity": 3,
                            }
                        ],
                    },
                    "guest-replace01",
                )
                settings.save_config(
                    {"provider": "demo", "watchlist": ["MSFT"], "positions": []},
                    "guest-replace01",
                )
                loaded = settings.load_config("guest-replace01")
                settings.user_data_store().save_consent(
                    "guest-replace01",
                    "investment-risk",
                    "1",
                    "2026-09-17T00:00:00+00:00",
                )

            self.assertIn("MSFT", loaded["watchlist"])
            self.assertNotIn("AAPL", loaded["watchlist"])
            self.assertEqual(loaded["positions"], [])

            with closing(sqlite3.connect(database_path)) as connection:
                table_names = {
                    row[0]
                    for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
                }
                users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                consents = connection.execute("SELECT COUNT(*) FROM consent_records").fetchone()[0]

            self.assertTrue({"users", "user_settings", "watchlist_items", "positions", "consent_records"} <= table_names)
            self.assertEqual(users, 1)
            self.assertEqual(consents, 1)

    def test_one_hundred_guest_profiles_remain_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database_path = root / "user_data" / "pulseedge.sqlite3"
            config_path = root / "config.json"
            config_path.write_text('{"provider":"demo","watchlist":["SPY"],"positions":[]}', encoding="utf-8")

            with (
                patch.object(settings, "DATABASE_PATH", database_path),
                patch.object(settings, "CONFIG_PATH", config_path),
            ):
                for index in range(100):
                    symbol = "AAPL" if index % 2 == 0 else "MSFT"
                    settings.save_config(
                        {
                            "provider": "demo",
                            "watchlist": [symbol],
                            "positions": [
                                {
                                    "symbol": symbol,
                                    "held": True,
                                    "average_entry_price": 100 + index,
                                    "quantity": index + 1,
                                    "notes": f"user-{index}",
                                }
                            ],
                        },
                        f"guest-load-{index:03d}",
                    )

                first = settings.load_config("guest-load-000")
                last = settings.load_config("guest-load-099")

            self.assertEqual(first["positions"][0]["notes"], "user-0")
            self.assertEqual(first["positions"][0]["quantity"], 1.0)
            self.assertEqual(last["positions"][0]["notes"], "user-99")
            self.assertEqual(last["positions"][0]["quantity"], 100.0)

            with closing(sqlite3.connect(database_path)) as connection:
                user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                position_count = connection.execute("SELECT COUNT(*) FROM positions").fetchone()[0]

            self.assertEqual(user_count, 100)
            self.assertEqual(position_count, 100)

    def test_rejects_invalid_client_id(self) -> None:
        with self.assertRaises(ValueError):
            settings.load_config("../bad-client")

    def test_auto_refresh_has_public_beta_floor(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            config = settings.normalize_config({"provider": "alpaca", "watchlist": ["AAPL"], "alerts": {"auto_refresh_minutes": 1}})

        self.assertEqual(config["alerts"]["auto_refresh_minutes"], 15)
        self.assertEqual(config["provider"], "demo")

    def test_private_server_can_enable_alpaca_provider(self) -> None:
        with patch.dict("os.environ", {"PULSEEDGE_MARKET_DATA_PROVIDER": "alpaca"}, clear=True):
            config = settings.normalize_config({"provider": "demo", "watchlist": ["AAPL"]})

        self.assertEqual(config["provider"], "alpaca")

    def test_unknown_server_provider_falls_back_to_demo(self) -> None:
        with patch.dict("os.environ", {"PULSEEDGE_MARKET_DATA_PROVIDER": "unknown"}, clear=True):
            config = settings.normalize_config({"provider": "alpaca", "watchlist": ["AAPL"]})

        self.assertEqual(config["provider"], "demo")

    def test_supabase_auth_config_is_optional_and_uses_publishable_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "SUPABASE_URL=https://project.supabase.co\n"
                "SUPABASE_PUBLISHABLE_KEY=public-key\n"
                "SUPABASE_SECRET_KEY=sb_secret_server-secret\n"
                "SUPABASE_EMAIL_ENABLED=true\n"
                "SUPABASE_GOOGLE_ENABLED=false\n",
                encoding="utf-8",
            )
            with patch.object(settings, "ENV_PATH", env_path), patch.dict("os.environ", {}, clear=True):
                config = settings.supabase_auth_config()
                admin = settings.supabase_admin_config()

        self.assertTrue(config["enabled"])
        self.assertTrue(config["email_enabled"])
        self.assertFalse(config["google_enabled"])
        self.assertEqual(config["publishable_key"], "public-key")
        self.assertTrue(config["account_deletion_enabled"])
        self.assertNotIn("sb_secret_server-secret", str(config))
        self.assertTrue(admin["enabled"])
        self.assertEqual(admin["server_key"], "sb_secret_server-secret")

    def test_supabase_admin_config_keeps_legacy_service_role_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "SUPABASE_URL=https://project.supabase.co\n"
                "SUPABASE_PUBLISHABLE_KEY=public-key\n"
                "SUPABASE_SERVICE_ROLE_KEY=legacy-server-secret\n",
                encoding="utf-8",
            )
            with patch.object(settings, "ENV_PATH", env_path), patch.dict("os.environ", {}, clear=True):
                admin = settings.supabase_admin_config()

        self.assertTrue(admin["enabled"])
        self.assertEqual(admin["server_key"], "legacy-server-secret")


if __name__ == "__main__":
    unittest.main()
