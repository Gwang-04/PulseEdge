from __future__ import annotations

import base64
import json
import time
import unittest
import urllib.error
from unittest.mock import patch

from auth_service import AuthError, SupabaseAuthAdmin, SupabaseAuthVerifier, bearer_token


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def fake_token(expiry: float) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"exp": expiry}).encode("utf-8")).decode("ascii").rstrip("=")
    return f"header.{payload}.signature"


class AuthServiceTests(unittest.TestCase):
    def test_bearer_token_parsing(self) -> None:
        self.assertEqual(bearer_token("Bearer abc.def"), "abc.def")
        self.assertEqual(bearer_token(None), "")
        with self.assertRaises(AuthError):
            bearer_token("Basic abc")

    def test_supabase_user_endpoint_is_validated_and_cached(self) -> None:
        verifier = SupabaseAuthVerifier("https://project.supabase.co", "publishable-key")
        payload = {
            "id": "user-123",
            "email": "USER@example.com",
            "app_metadata": {"provider": "google"},
            "user_metadata": {"full_name": "Pulse User"},
        }
        token = fake_token(time.time() + 600)
        with patch("auth_service.urllib.request.urlopen", return_value=FakeResponse(payload)) as urlopen:
            first = verifier.verify(token)
            second = verifier.verify(token)

        self.assertEqual(first.subject, "user-123")
        self.assertEqual(first.email, "user@example.com")
        self.assertEqual(first.provider, "google")
        self.assertEqual(first.display_name, "Pulse User")
        self.assertEqual(second, first)
        self.assertEqual(urlopen.call_count, 1)

    def test_supabase_admin_deletes_user_with_new_secret_key(self) -> None:
        admin = SupabaseAuthAdmin("https://project.supabase.co", "sb_secret_server-key")

        with patch("auth_service.urllib.request.urlopen", return_value=FakeResponse({})) as urlopen:
            admin.delete_user("user-123")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "DELETE")
        self.assertEqual(request.full_url, "https://project.supabase.co/auth/v1/admin/users/user-123")
        self.assertEqual(request.headers["Apikey"], "sb_secret_server-key")
        self.assertNotIn("Authorization", request.headers)

    def test_supabase_admin_supports_legacy_service_role_jwt(self) -> None:
        admin = SupabaseAuthAdmin("https://project.supabase.co", "service-role-key")

        with patch("auth_service.urllib.request.urlopen", return_value=FakeResponse({})) as urlopen:
            admin.delete_user("user-123")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers["Apikey"], "service-role-key")
        self.assertEqual(request.headers["Authorization"], "Bearer service-role-key")

    def test_supabase_admin_treats_already_deleted_user_as_success(self) -> None:
        admin = SupabaseAuthAdmin("https://project.supabase.co", "service-role-key")
        missing = urllib.error.HTTPError("https://project.supabase.co", 404, "missing", {}, None)

        with patch("auth_service.urllib.request.urlopen", side_effect=missing):
            admin.delete_user("already-deleted")


if __name__ == "__main__":
    unittest.main()
