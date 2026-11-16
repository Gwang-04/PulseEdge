from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class AuthError(ValueError):
    pass


class AuthAdminError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthIdentity:
    provider: str
    subject: str
    email: str
    display_name: str


class SupabaseAuthVerifier:
    """Validate Supabase access tokens without storing user credentials."""

    def __init__(self, project_url: str, publishable_key: str, timeout: float = 8.0) -> None:
        self.project_url = project_url.rstrip("/")
        self.publishable_key = publishable_key
        self.timeout = timeout
        self._cache: dict[str, tuple[float, AuthIdentity]] = {}
        self._lock = threading.Lock()

    def verify(self, access_token: str) -> AuthIdentity:
        token = str(access_token or "").strip()
        if not token:
            raise AuthError("로그인이 필요합니다.")

        cache_key = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = time.time()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and cached[0] > now:
                return cached[1]

        request = urllib.request.Request(
            f"{self.project_url}/auth/v1/user",
            headers={
                "apikey": self.publishable_key,
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise AuthError("로그인이 만료되었거나 인증 서버에 연결할 수 없습니다.") from exc

        identity = _identity_from_payload(payload)
        expires_at = min(_jwt_expiry(token) or now + 300, now + 300)
        with self._lock:
            self._cache[cache_key] = (max(now + 15, expires_at), identity)
            if len(self._cache) > 512:
                self._cache = {
                    key: value for key, value in self._cache.items() if value[0] > now
                }
        return identity


class SupabaseAuthAdmin:
    """Perform server-only Supabase Auth administration."""

    def __init__(self, project_url: str, server_key: str, timeout: float = 8.0) -> None:
        self.project_url = project_url.rstrip("/")
        self.server_key = server_key
        self.timeout = timeout

    def delete_user(self, user_id: str) -> None:
        subject = str(user_id or "").strip()
        if not subject or len(subject) > 128:
            raise AuthAdminError("삭제할 인증 사용자 정보가 올바르지 않습니다.")
        headers = {
            "apikey": self.server_key,
            "Accept": "application/json",
        }
        # Legacy service_role keys are JWTs. New sb_secret keys are not and must
        # be sent only as an API key, according to Supabase's key migration guide.
        if not self.server_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self.server_key}"
        request = urllib.request.Request(
            f"{self.project_url}/auth/v1/admin/users/{urllib.parse.quote(subject, safe='')}",
            method="DELETE",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout):
                return
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return
            raise AuthAdminError("인증 계정을 삭제하지 못했습니다. 잠시 후 다시 시도해 주세요.") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AuthAdminError("인증 계정을 삭제하지 못했습니다. 잠시 후 다시 시도해 주세요.") from exc


def bearer_token(authorization_header: str | None) -> str:
    value = str(authorization_header or "").strip()
    if not value:
        return ""
    scheme, separator, token = value.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise AuthError("인증 헤더 형식이 올바르지 않습니다.")
    return token.strip()


def _identity_from_payload(payload: Any) -> AuthIdentity:
    if not isinstance(payload, dict):
        raise AuthError("인증 사용자 정보를 확인할 수 없습니다.")
    subject = str(payload.get("id") or "").strip()
    if not subject or len(subject) > 128:
        raise AuthError("인증 사용자 식별자가 올바르지 않습니다.")
    app_metadata = payload.get("app_metadata") if isinstance(payload.get("app_metadata"), dict) else {}
    user_metadata = payload.get("user_metadata") if isinstance(payload.get("user_metadata"), dict) else {}
    provider = str(app_metadata.get("provider") or "supabase").strip().lower()[:32]
    email = str(payload.get("email") or "").strip().lower()[:254]
    display_name = str(user_metadata.get("full_name") or user_metadata.get("name") or "").strip()[:120]
    return AuthIdentity(provider=provider, subject=subject, email=email, display_name=display_name)


def _jwt_expiry(token: str) -> float | None:
    try:
        payload_segment = token.split(".")[1]
        padded = payload_segment + "=" * (-len(payload_segment) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        expiry = float(payload.get("exp", 0))
        return expiry if expiry > 0 else None
    except (IndexError, ValueError, TypeError, json.JSONDecodeError):
        return None
