from __future__ import annotations

import json
import hashlib
import sqlite3
import threading
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 3
_SCHEMA_LOCK = threading.Lock()


class UserDataStore:
    """SQLite-backed storage for guest and future account-scoped user data."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.initialize()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with _SCHEMA_LOCK, self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    public_id TEXT NOT NULL UNIQUE,
                    account_kind TEXT NOT NULL DEFAULT 'guest',
                    email TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    settings_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS watchlist_items (
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    sort_order INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, symbol),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS positions (
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    held INTEGER NOT NULL DEFAULT 0,
                    average_entry_price REAL,
                    quantity REAL,
                    entry_date TEXT NOT NULL DEFAULT '',
                    target_return_pct REAL NOT NULL,
                    stop_loss_pct REAL NOT NULL,
                    trailing_stop_pct REAL NOT NULL,
                    holding_style TEXT NOT NULL DEFAULT 'swing',
                    next_earnings_date TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, symbol),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS consent_records (
                    user_id INTEGER NOT NULL,
                    consent_key TEXT NOT NULL,
                    version TEXT NOT NULL,
                    accepted_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    PRIMARY KEY (user_id, consent_key),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS auth_identities (
                    user_id INTEGER NOT NULL UNIQUE,
                    auth_service TEXT NOT NULL,
                    auth_subject TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    email TEXT,
                    display_name TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(auth_service, auth_subject),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS guest_account_links (
                    guest_user_id INTEGER NOT NULL,
                    account_user_id INTEGER NOT NULL,
                    linked_at TEXT NOT NULL,
                    PRIMARY KEY (guest_user_id, account_user_id),
                    FOREIGN KEY (guest_user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (account_user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS deleted_auth_identities (
                    auth_service TEXT NOT NULL,
                    auth_subject TEXT NOT NULL,
                    deleted_at TEXT NOT NULL,
                    PRIMARY KEY (auth_service, auth_subject)
                );

                CREATE INDEX IF NOT EXISTS idx_watchlist_symbol
                    ON watchlist_items(symbol);
                CREATE INDEX IF NOT EXISTS idx_positions_symbol
                    ON positions(symbol);
                CREATE INDEX IF NOT EXISTS idx_auth_identity_subject
                    ON auth_identities(auth_service, auth_subject);
                """
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def load_config(self, public_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            user = connection.execute(
                "SELECT id FROM users WHERE public_id = ?",
                (public_id,),
            ).fetchone()
            if user is None:
                return None

            user_id = int(user["id"])
            settings_row = connection.execute(
                "SELECT settings_json FROM user_settings WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            settings = json.loads(settings_row["settings_json"]) if settings_row else {}
            if not isinstance(settings, dict):
                settings = {}

            watchlist = [
                row["symbol"]
                for row in connection.execute(
                    "SELECT symbol FROM watchlist_items WHERE user_id = ? ORDER BY sort_order, symbol",
                    (user_id,),
                ).fetchall()
            ]
            positions = [
                {
                    "symbol": row["symbol"],
                    "held": bool(row["held"]),
                    "average_entry_price": row["average_entry_price"],
                    "quantity": row["quantity"],
                    "entry_date": row["entry_date"],
                    "target_return_pct": row["target_return_pct"],
                    "stop_loss_pct": row["stop_loss_pct"],
                    "trailing_stop_pct": row["trailing_stop_pct"],
                    "holding_style": row["holding_style"],
                    "next_earnings_date": row["next_earnings_date"],
                    "notes": row["notes"],
                }
                for row in connection.execute(
                    "SELECT * FROM positions WHERE user_id = ? ORDER BY rowid",
                    (user_id,),
                ).fetchall()
            ]
            settings["watchlist"] = watchlist
            settings["positions"] = positions
            return settings

    def save_config(self, public_id: str, config: dict[str, Any], account_kind: str = "guest") -> None:
        now = _utc_now()
        settings = deepcopy(config)
        watchlist = list(settings.pop("watchlist", []))
        positions = list(settings.pop("positions", []))

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO users(public_id, account_kind, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(public_id) DO UPDATE SET
                        account_kind = CASE
                            WHEN users.account_kind = 'authenticated' THEN users.account_kind
                            ELSE excluded.account_kind
                        END,
                        updated_at = excluded.updated_at
                    """,
                    (public_id, account_kind, now, now),
                )
                user_id = int(
                    connection.execute(
                        "SELECT id FROM users WHERE public_id = ?",
                        (public_id,),
                    ).fetchone()["id"]
                )
                connection.execute(
                    """
                    INSERT INTO user_settings(user_id, settings_json, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        settings_json = excluded.settings_json,
                        updated_at = excluded.updated_at
                    """,
                    (user_id, json.dumps(settings, ensure_ascii=False, separators=(",", ":")), now),
                )

                connection.execute("DELETE FROM watchlist_items WHERE user_id = ?", (user_id,))
                connection.executemany(
                    """
                    INSERT INTO watchlist_items(user_id, symbol, sort_order, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    [(user_id, symbol, index, now) for index, symbol in enumerate(watchlist)],
                )

                connection.execute("DELETE FROM positions WHERE user_id = ?", (user_id,))
                connection.executemany(
                    """
                    INSERT INTO positions(
                        user_id, symbol, held, average_entry_price, quantity, entry_date,
                        target_return_pct, stop_loss_pct, trailing_stop_pct, holding_style,
                        next_earnings_date, notes, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            user_id,
                            position["symbol"],
                            int(bool(position.get("held", False))),
                            position.get("average_entry_price"),
                            position.get("quantity"),
                            position.get("entry_date", ""),
                            position.get("target_return_pct", 15.0),
                            position.get("stop_loss_pct", -7.0),
                            position.get("trailing_stop_pct", -8.0),
                            position.get("holding_style", "swing"),
                            position.get("next_earnings_date", ""),
                            position.get("notes", ""),
                            now,
                        )
                        for position in positions
                    ],
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def link_authenticated_user(
        self,
        guest_public_id: str,
        auth_service: str,
        auth_subject: str,
        provider: str,
        email: str = "",
        display_name: str = "",
    ) -> str:
        service = str(auth_service or "").strip().lower()
        subject = str(auth_subject or "").strip()
        if not service or not subject or len(subject) > 128:
            raise ValueError("Invalid authenticated user")

        now = _utc_now()
        account_public_id = _account_public_id(service, subject)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                deleted = connection.execute(
                    "SELECT 1 FROM deleted_auth_identities WHERE auth_service = ? AND auth_subject = ?",
                    (service, subject),
                ).fetchone()
                if deleted is not None:
                    raise ValueError("Deleted authenticated user")
                identity = connection.execute(
                    """
                    SELECT users.id, users.public_id
                    FROM auth_identities
                    JOIN users ON users.id = auth_identities.user_id
                    WHERE auth_identities.auth_service = ? AND auth_identities.auth_subject = ?
                    """,
                    (service, subject),
                ).fetchone()
                if identity is None:
                    connection.execute(
                        """
                        INSERT INTO users(public_id, account_kind, email, created_at, updated_at)
                        VALUES (?, 'authenticated', ?, ?, ?)
                        ON CONFLICT(public_id) DO UPDATE SET
                            account_kind = 'authenticated',
                            email = excluded.email,
                            updated_at = excluded.updated_at
                        """,
                        (account_public_id, email or None, now, now),
                    )
                    account_id = int(
                        connection.execute(
                            "SELECT id FROM users WHERE public_id = ?",
                            (account_public_id,),
                        ).fetchone()["id"]
                    )
                    connection.execute(
                        """
                        INSERT INTO auth_identities(
                            user_id, auth_service, auth_subject, provider, email,
                            display_name, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (account_id, service, subject, provider, email or None, display_name or None, now, now),
                    )
                else:
                    account_id = int(identity["id"])
                    account_public_id = str(identity["public_id"])
                    connection.execute(
                        "UPDATE users SET account_kind = 'authenticated', email = ?, updated_at = ? WHERE id = ?",
                        (email or None, now, account_id),
                    )
                    connection.execute(
                        """
                        UPDATE auth_identities
                        SET provider = ?, email = ?, display_name = ?, updated_at = ?
                        WHERE user_id = ?
                        """,
                        (provider, email or None, display_name or None, now, account_id),
                    )

                guest = connection.execute(
                    "SELECT id FROM users WHERE public_id = ?",
                    (guest_public_id,),
                ).fetchone()
                if guest is not None and int(guest["id"]) != account_id:
                    guest_id = int(guest["id"])
                    already_linked = connection.execute(
                        """
                        SELECT 1 FROM guest_account_links
                        WHERE guest_user_id = ? AND account_user_id = ?
                        """,
                        (guest_id, account_id),
                    ).fetchone()
                    if already_linked is None:
                        self._merge_guest_data(connection, guest_id, account_id, now)
                        connection.execute(
                            """
                            INSERT INTO guest_account_links(guest_user_id, account_user_id, linked_at)
                            VALUES (?, ?, ?)
                            """,
                            (guest_id, account_id, now),
                        )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return account_public_id

    def delete_authenticated_user(self, auth_service: str, auth_subject: str) -> list[str]:
        service = str(auth_service or "").strip().lower()
        subject = str(auth_subject or "").strip()
        if not service or not subject or len(subject) > 128:
            raise ValueError("Invalid authenticated user")

        deleted_public_ids: list[str] = []
        now = _utc_now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                identity = connection.execute(
                    """
                    SELECT users.id, users.public_id
                    FROM auth_identities
                    JOIN users ON users.id = auth_identities.user_id
                    WHERE auth_identities.auth_service = ? AND auth_identities.auth_subject = ?
                    """,
                    (service, subject),
                ).fetchone()
                connection.execute(
                    """
                    INSERT INTO deleted_auth_identities(auth_service, auth_subject, deleted_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(auth_service, auth_subject) DO UPDATE SET deleted_at = excluded.deleted_at
                    """,
                    (service, subject, now),
                )
                if identity is not None:
                    account_id = int(identity["id"])
                    deleted_public_ids.append(str(identity["public_id"]))
                    guests = connection.execute(
                        """
                        SELECT users.id, users.public_id
                        FROM guest_account_links
                        JOIN users ON users.id = guest_account_links.guest_user_id
                        WHERE guest_account_links.account_user_id = ?
                        """,
                        (account_id,),
                    ).fetchall()
                    connection.execute("DELETE FROM users WHERE id = ?", (account_id,))
                    for guest in guests:
                        guest_id = int(guest["id"])
                        still_linked = connection.execute(
                            "SELECT 1 FROM guest_account_links WHERE guest_user_id = ? LIMIT 1",
                            (guest_id,),
                        ).fetchone()
                        if still_linked is None:
                            connection.execute("DELETE FROM users WHERE id = ?", (guest_id,))
                            deleted_public_ids.append(str(guest["public_id"]))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return deleted_public_ids

    def profile(self, public_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT users.public_id, users.account_kind, users.email,
                       auth_identities.provider, auth_identities.display_name
                FROM users
                LEFT JOIN auth_identities ON auth_identities.user_id = users.id
                WHERE users.public_id = ?
                """,
                (public_id,),
            ).fetchone()
        if row is None:
            return None
        authenticated = row["account_kind"] == "authenticated"
        return {
            "client_id": row["public_id"],
            "storage": "sqlite",
            "account_kind": row["account_kind"],
            "server_side": True,
            "authenticated": authenticated,
            "email": row["email"] or "",
            "provider": row["provider"] or "",
            "display_name": row["display_name"] or "",
        }

    def _merge_guest_data(
        self,
        connection: sqlite3.Connection,
        guest_id: int,
        account_id: int,
        now: str,
    ) -> None:
        account_settings = connection.execute(
            "SELECT 1 FROM user_settings WHERE user_id = ?",
            (account_id,),
        ).fetchone()
        if account_settings is None:
            guest_settings = connection.execute(
                "SELECT settings_json FROM user_settings WHERE user_id = ?",
                (guest_id,),
            ).fetchone()
            if guest_settings is not None:
                connection.execute(
                    "INSERT INTO user_settings(user_id, settings_json, updated_at) VALUES (?, ?, ?)",
                    (account_id, guest_settings["settings_json"], now),
                )

        existing_symbols = {
            row["symbol"]
            for row in connection.execute(
                "SELECT symbol FROM watchlist_items WHERE user_id = ?",
                (account_id,),
            ).fetchall()
        }
        next_order = len(existing_symbols)
        guest_symbols = connection.execute(
            "SELECT symbol FROM watchlist_items WHERE user_id = ? ORDER BY sort_order, symbol",
            (guest_id,),
        ).fetchall()
        for row in guest_symbols:
            symbol = row["symbol"]
            if symbol in existing_symbols:
                continue
            connection.execute(
                """
                INSERT INTO watchlist_items(user_id, symbol, sort_order, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (account_id, symbol, next_order, now),
            )
            existing_symbols.add(symbol)
            next_order += 1

        connection.execute(
            """
            INSERT OR IGNORE INTO positions(
                user_id, symbol, held, average_entry_price, quantity, entry_date,
                target_return_pct, stop_loss_pct, trailing_stop_pct, holding_style,
                next_earnings_date, notes, updated_at
            )
            SELECT ?, symbol, held, average_entry_price, quantity, entry_date,
                   target_return_pct, stop_loss_pct, trailing_stop_pct, holding_style,
                   next_earnings_date, notes, ?
            FROM positions WHERE user_id = ?
            """,
            (account_id, now, guest_id),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO consent_records(
                user_id, consent_key, version, accepted_at, metadata_json
            )
            SELECT ?, consent_key, version, accepted_at, metadata_json
            FROM consent_records WHERE user_id = ?
            """,
            (account_id, guest_id),
        )

    def save_consent(
        self,
        public_id: str,
        consent_key: str,
        version: str,
        accepted_at: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        now = _utc_now()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO users(public_id, account_kind, created_at, updated_at)
                    VALUES (?, 'guest', ?, ?)
                    ON CONFLICT(public_id) DO UPDATE SET updated_at = excluded.updated_at
                    """,
                    (public_id, now, now),
                )
                user_id = int(
                    connection.execute(
                        "SELECT id FROM users WHERE public_id = ?",
                        (public_id,),
                    ).fetchone()["id"]
                )
                connection.execute(
                    """
                    INSERT INTO consent_records(user_id, consent_key, version, accepted_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, consent_key) DO UPDATE SET
                        version = excluded.version,
                        accepted_at = excluded.accepted_at,
                        metadata_json = excluded.metadata_json
                    """,
                    (
                        user_id,
                        consent_key,
                        version,
                        accepted_at,
                        json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":")),
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _account_public_id(auth_service: str, auth_subject: str) -> str:
    digest = hashlib.sha256(f"{auth_service}:{auth_subject}".encode("utf-8")).hexdigest()[:32]
    return f"account-{digest}"
