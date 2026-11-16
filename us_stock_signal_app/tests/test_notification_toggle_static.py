from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NotificationToggleStaticTests(unittest.TestCase):
    def test_notification_permission_and_app_toggle_are_separate(self) -> None:
        script = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

        self.assertIn('const NOTIFICATIONS_ENABLED_STORAGE_KEY = "pulseedgeNotificationsEnabled";', script)
        self.assertIn("function notificationsAppEnabled()", script)
        self.assertIn('state: "muted"', script)
        self.assertIn('button: "알림 꺼짐"', script)
        self.assertIn('button: "알림 차단됨"', script)
        self.assertIn("|| !notificationsAppEnabled()", script)


if __name__ == "__main__":
    unittest.main()
