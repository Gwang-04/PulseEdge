from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from user_store import UserDataStore


class UserStoreAuthTests(unittest.TestCase):
    def test_guest_data_is_copied_to_authenticated_account(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UserDataStore(Path(temp_dir) / "pulseedge.sqlite3")
            store.save_config(
                "guest-browser01",
                {
                    "provider": "demo",
                    "watchlist": ["AAPL", "SPY"],
                    "positions": [
                        {
                            "symbol": "AAPL",
                            "held": True,
                            "average_entry_price": 190,
                            "quantity": 2,
                        }
                    ],
                },
            )

            account_id = store.link_authenticated_user(
                "guest-browser01",
                "supabase",
                "auth-user-1",
                "google",
                "person@example.com",
                "Pulse User",
            )
            account = store.load_config(account_id)
            profile = store.profile(account_id)

        self.assertEqual(account["watchlist"], ["AAPL", "SPY"])
        self.assertEqual(account["positions"][0]["average_entry_price"], 190.0)
        self.assertTrue(profile["authenticated"])
        self.assertEqual(profile["email"], "person@example.com")
        self.assertEqual(profile["provider"], "google")

    def test_second_guest_merges_once_without_overwriting_account_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UserDataStore(Path(temp_dir) / "pulseedge.sqlite3")
            store.save_config(
                "guest-first001",
                {
                    "provider": "demo",
                    "watchlist": ["AAPL"],
                    "positions": [],
                    "alerts": {"rsi_oversold": 28},
                },
            )
            account_id = store.link_authenticated_user(
                "guest-first001", "supabase", "shared-user", "email", "shared@example.com"
            )
            store.save_config(
                account_id,
                {
                    "provider": "demo",
                    "watchlist": ["MSFT"],
                    "positions": [],
                    "alerts": {"rsi_oversold": 27},
                },
            )
            store.save_config(
                "guest-second02",
                {
                    "provider": "demo",
                    "watchlist": ["NVDA"],
                    "positions": [{"symbol": "NVDA", "held": True, "average_entry_price": 120}],
                    "alerts": {"rsi_oversold": 20},
                },
            )

            same_account_id = store.link_authenticated_user(
                "guest-second02", "supabase", "shared-user", "email", "shared@example.com"
            )
            store.link_authenticated_user(
                "guest-second02", "supabase", "shared-user", "email", "shared@example.com"
            )
            account = store.load_config(account_id)
            profile = store.profile(account_id)

        self.assertEqual(same_account_id, account_id)
        self.assertEqual(account["watchlist"], ["MSFT", "NVDA"])
        self.assertEqual(account["alerts"]["rsi_oversold"], 27)
        self.assertEqual(len(account["positions"]), 1)
        self.assertEqual(profile["account_kind"], "authenticated")

    def test_account_delete_removes_linked_data_and_blocks_stale_token_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UserDataStore(Path(temp_dir) / "pulseedge.sqlite3")
            store.save_config(
                "guest-delete01",
                {
                    "provider": "demo",
                    "watchlist": ["AAPL"],
                    "positions": [{"symbol": "AAPL", "held": True, "average_entry_price": 190}],
                },
            )
            account_id = store.link_authenticated_user(
                "guest-delete01", "supabase", "delete-user", "email", "delete@example.com"
            )
            store.save_consent(account_id, "investment-risk", "v1", "2026-09-29T00:00:00+00:00")

            deleted_ids = store.delete_authenticated_user("supabase", "delete-user")

            self.assertIn(account_id, deleted_ids)
            self.assertIn("guest-delete01", deleted_ids)
            self.assertIsNone(store.profile(account_id))
            self.assertIsNone(store.load_config(account_id))
            self.assertIsNone(store.load_config("guest-delete01"))
            with self.assertRaises(ValueError):
                store.link_authenticated_user(
                    "guest-newtoken1", "supabase", "delete-user", "email", "delete@example.com"
                )


if __name__ == "__main__":
    unittest.main()
