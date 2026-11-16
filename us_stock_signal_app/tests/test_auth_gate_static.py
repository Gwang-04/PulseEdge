from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AuthGateStaticTests(unittest.TestCase):
    def test_login_first_markup_and_guest_escape_exist(self) -> None:
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")

        self.assertIn('id="authGate"', html)
        self.assertIn('id="authGateEmail"', html)
        self.assertIn('id="authGateEmailButton"', html)
        self.assertIn('id="authGateGuestButton"', html)
        self.assertIn('<main class="app-shell" inert aria-hidden="true">', html)

    def test_login_gate_tracks_guest_and_authenticated_states(self) -> None:
        script = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

        self.assertIn('const GUEST_ACCESS_STORAGE_KEY = "pulseedgeGuestAccess";', script)
        self.assertIn("function renderAuthGate()", script)
        self.assertIn("function continueAsGuest()", script)
        self.assertIn('localStorage.removeItem(GUEST_ACCESS_STORAGE_KEY);', script)
        self.assertIn('document.querySelectorAll(".app-shell, .bottom-nav")', script)

    def test_account_delete_requires_email_confirmation(self) -> None:
        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="deleteAccountButton"', html)
        self.assertIn('id="accountDeleteEmail"', html)
        self.assertIn('id="accountDeleteConfirmButton"', html)
        self.assertIn('apiPost("/api/account/delete", { confirmation })', script)
        self.assertIn("function clearPulseEdgeLocalData()", script)


if __name__ == "__main__":
    unittest.main()
