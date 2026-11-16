from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from user_store import UserDataStore

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
USER_CONFIG_DIR = APP_DIR / "user_data"
DATABASE_PATH = USER_CONFIG_DIR / "pulseedge.sqlite3"
ENV_PATH = APP_DIR / ".env"
DEFAULT_CLIENT_ID = "local"
CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{7,63}$")
MIN_AUTO_REFRESH_MINUTES = 15

SIGNAL_GROUPS: dict[str, list[str]] = {
    "RSI": [
        "RSI_OVERSOLD",
        "RSI_DEEP_OVERSOLD",
        "RSI_RECOVERY",
        "RSI_OVERHEATED",
        "RSI_OVERHEAT_COOLING",
    ],
    "VOLUME": [
        "VOLUME_SPIKE",
        "VOLUME_SPIKE_LARGE_CAP",
        "BULLISH_VOLUME_SPIKE",
        "BEARISH_VOLUME_SPIKE",
    ],
    "MOVING_AVERAGE": [
        "MA20_BREAKDOWN",
        "MA60_BREAKDOWN",
        "MA120_BREAKDOWN",
        "MA20_RECOVERY",
        "MA60_RECOVERY",
        "MA120_RECOVERY",
        "MA20_OVERSOLD_DISTANCE",
        "MA60_OVERSOLD_DISTANCE",
        "MA120_OVERSOLD_DISTANCE",
        "MA20_OVEREXTENDED",
        "MA60_OVEREXTENDED",
        "GOLDEN_CROSS_20_60",
        "DEAD_CROSS_20_60",
    ],
    "BREAKOUT": [
        "HIGH_60_BREAKOUT",
        "LOW_60_BREAKDOWN",
        "HIGH_120_BREAKOUT",
        "LOW_120_BREAKDOWN",
        "VOLUME_CONFIRMED_BREAKOUT",
    ],
    "GAP": [
        "GAP_UP",
        "GAP_DOWN",
        "GAP_DOWN_VOLUME_SPIKE",
    ],
    "CHART": [
        "BOLLINGER_LOWER_TOUCH",
        "BOLLINGER_LOWER_RECOVERY",
        "ICHIMOKU_CLOUD_RECOVERY",
        "ICHIMOKU_CLOUD_BREAKDOWN",
    ],
    "POSITION": [
        "LOSS_WARNING",
        "STOP_REVIEW",
        "RISK_EXIT_REVIEW",
        "STOP_BUFFER_WARNING",
        "STOP_BUFFER_REVIEW",
        "POSITION_SUPPORT_BUFFER_WARNING",
        "POSITION_SUPPORT_BREAKDOWN",
        "POSITION_SUPPORT_VOLUME_BREAKDOWN",
        "POSITION_MA60_CONFIRM_BREAKDOWN",
        "POSITION_STRUCTURE_EXIT_REVIEW",
        "VIX_POSITION_RISK",
        "POSITION_MA20_BREAKDOWN",
        "POSITION_MA60_BREAKDOWN",
        "POSITION_MA120_BREAKDOWN",
        "PROFIT_10",
        "PROFIT_20",
        "PROFIT_30",
        "TRAILING_STOP_WARNING",
        "TRAILING_STOP_REVIEW",
        "TRAILING_BUFFER_WARNING",
        "RSI_OVERHEAT_COOLING_HELD",
    ],
    "EARNINGS": [
        "EARNINGS_7D",
        "EARNINGS_1D",
        "EARNINGS_TODAY",
        "EARNINGS_AFTER",
    ],
    "MARKET": [
        "SPY_BELOW_MA120",
        "QQQ_BELOW_MA120",
        "MARKET_RISK_ON",
        "MARKET_RISK_OFF",
        "MARKET_FILTER_DOWNGRADE",
        "VIX_ELEVATED",
        "VIX_FEAR",
        "VIX_PANIC",
        "VIX_SPIKE",
        "VIX_CALMING",
    ],
}

DEFAULT_ALERT_PREFERENCES: dict[str, str] = {
    "RSI_OVERSOLD": "summary",
    "RSI_DEEP_OVERSOLD": "summary",
    "RSI_RECOVERY": "summary",
    "RSI_OVERHEATED": "log",
    "RSI_OVERHEAT_COOLING": "summary",
    "VOLUME_SPIKE": "summary",
    "VOLUME_SPIKE_LARGE_CAP": "log",
    "BULLISH_VOLUME_SPIKE": "summary",
    "BEARISH_VOLUME_SPIKE": "summary",
    "MA20_BREAKDOWN": "summary",
    "MA60_BREAKDOWN": "summary",
    "MA120_BREAKDOWN": "summary",
    "MA20_RECOVERY": "summary",
    "MA60_RECOVERY": "summary",
    "MA120_RECOVERY": "summary",
    "MA20_OVERSOLD_DISTANCE": "log",
    "MA60_OVERSOLD_DISTANCE": "summary",
    "MA120_OVERSOLD_DISTANCE": "summary",
    "MA20_OVEREXTENDED": "log",
    "MA60_OVEREXTENDED": "summary",
    "GOLDEN_CROSS_20_60": "summary",
    "DEAD_CROSS_20_60": "summary",
    "HIGH_60_BREAKOUT": "summary",
    "LOW_60_BREAKDOWN": "summary",
    "HIGH_120_BREAKOUT": "summary",
    "LOW_120_BREAKDOWN": "summary",
    "VOLUME_CONFIRMED_BREAKOUT": "summary",
    "GAP_UP": "summary",
    "GAP_DOWN": "summary",
    "GAP_DOWN_VOLUME_SPIKE": "push",
    "BOLLINGER_LOWER_TOUCH": "summary",
    "BOLLINGER_LOWER_RECOVERY": "summary",
    "ICHIMOKU_CLOUD_RECOVERY": "summary",
    "ICHIMOKU_CLOUD_BREAKDOWN": "summary",
    "LOSS_WARNING": "push",
    "STOP_REVIEW": "push",
    "RISK_EXIT_REVIEW": "push",
    "STOP_BUFFER_WARNING": "summary",
    "STOP_BUFFER_REVIEW": "push",
    "POSITION_SUPPORT_BUFFER_WARNING": "summary",
    "POSITION_SUPPORT_BREAKDOWN": "push",
    "POSITION_SUPPORT_VOLUME_BREAKDOWN": "push",
    "POSITION_MA60_CONFIRM_BREAKDOWN": "push",
    "POSITION_STRUCTURE_EXIT_REVIEW": "push",
    "VIX_POSITION_RISK": "summary",
    "POSITION_MA20_BREAKDOWN": "summary",
    "POSITION_MA60_BREAKDOWN": "push",
    "POSITION_MA120_BREAKDOWN": "push",
    "PROFIT_10": "summary",
    "PROFIT_20": "summary",
    "PROFIT_30": "push",
    "TRAILING_STOP_WARNING": "summary",
    "TRAILING_STOP_REVIEW": "push",
    "TRAILING_BUFFER_WARNING": "summary",
    "RSI_OVERHEAT_COOLING_HELD": "push",
    "EARNINGS_7D": "summary",
    "EARNINGS_1D": "push",
    "EARNINGS_TODAY": "push",
    "EARNINGS_AFTER": "summary",
    "SPY_BELOW_MA120": "summary",
    "QQQ_BELOW_MA120": "summary",
    "MARKET_RISK_ON": "log",
    "MARKET_RISK_OFF": "push",
    "MARKET_FILTER_DOWNGRADE": "summary",
    "VIX_ELEVATED": "summary",
    "VIX_FEAR": "push",
    "VIX_PANIC": "push",
    "VIX_SPIKE": "summary",
    "VIX_CALMING": "summary",
}

DEFAULT_CONFIG: dict[str, Any] = {
    "provider": "demo",
    "watchlist": ["AAPL", "MSFT", "NVDA", "TSLA", "QQQ", "SPY"],
    "positions": [],
    "alpaca": {
        "feed": "iex",
        "timeframe": "1Day",
        "adjustment": "split",
        "lookback_days": 900,
    },
    "chart": {
        "default_timeframe": "D",
        "default_range": "6M",
        "zoom_enabled": True,
    },
    "fear": {
        "source": "cboe",
        "lookback_days": 180,
        "elevated_threshold": 20.0,
        "fear_threshold": 30.0,
        "panic_threshold": 40.0,
        "spike_5d_pct": 20.0,
        "calming_5d_pct": -12.0,
        "fallback_to_demo": True,
    },
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
        "high_low_periods": [60, 120],
        "ma_distance_pct": {
            "20_oversold": -7.0,
            "60_oversold": -12.0,
            "120_oversold": -20.0,
            "20_overextended": 12.0,
            "60_overextended": 20.0,
        },
        "auto_refresh_minutes": 30,
        "quiet_hours": {
            "enabled": False,
            "start": "23:00",
            "end": "07:00",
        },
    },
    "alert_preferences": DEFAULT_ALERT_PREFERENCES,
}

SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")
VALID_DELIVERY_MODES = {"push", "summary", "log", "off"}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def normalize_symbols(symbols: list[str] | str) -> list[str]:
    if isinstance(symbols, str):
        raw = re.split(r"[\s,]+", symbols)
    else:
        raw = symbols
    normalized: list[str] = []
    seen: set[str] = set()
    for symbol in raw:
        ticker = str(symbol).strip().upper()
        if not ticker:
            continue
        if not SYMBOL_RE.match(ticker):
            raise ValueError(f"Invalid ticker symbol: {symbol}")
        if ticker not in seen:
            normalized.append(ticker)
            seen.add(ticker)
    if not normalized:
        raise ValueError("Watchlist cannot be empty")
    return normalized[:30]


def all_signal_types() -> list[str]:
    output: list[str] = []
    for signal_types in SIGNAL_GROUPS.values():
        output.extend(signal_types)
    return output


def load_config(client_id: str | None = None) -> dict[str, Any]:
    if client_id is not None:
        return load_client_config(client_id)
    return normalize_config(read_config_file(CONFIG_PATH))


def save_config(config: dict[str, Any], client_id: str | None = None) -> dict[str, Any]:
    normalized = normalize_config(config)
    if client_id is not None:
        normalized_client_id = normalize_client_id(client_id)
        user_data_store().save_config(normalized_client_id, normalized)
    else:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return normalized


def read_config_file(path: Path) -> dict[str, Any]:
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
            return config if isinstance(config, dict) else {}
    return {}


def load_client_config(client_id: str) -> dict[str, Any]:
    normalized_client_id = normalize_client_id(client_id)
    store = user_data_store()
    stored = store.load_config(normalized_client_id)
    if stored is not None:
        return normalize_config(stored)

    legacy_path = client_config_path(normalized_client_id)
    if legacy_path.exists():
        normalized = normalize_config(read_config_file(legacy_path))
        store.save_config(normalized_client_id, normalized)
        return normalized
    return normalize_config(read_config_file(CONFIG_PATH))


def user_data_store() -> UserDataStore:
    return cached_user_data_store(str(DATABASE_PATH.resolve()))


@lru_cache(maxsize=8)
def cached_user_data_store(database_path: str) -> UserDataStore:
    return UserDataStore(Path(database_path))


def client_config_path(client_id: str | None) -> Path:
    normalized_client_id = normalize_client_id(client_id)
    if normalized_client_id == DEFAULT_CLIENT_ID:
        return CONFIG_PATH
    return USER_CONFIG_DIR / "guests" / f"{normalized_client_id}.json"


def normalize_client_id(client_id: str | None) -> str:
    value = str(client_id or "").strip()
    if not value:
        return DEFAULT_CLIENT_ID
    if not CLIENT_ID_RE.match(value):
        raise ValueError("Invalid client id")
    return value


def config_profile(client_id: str | None) -> dict[str, Any]:
    normalized_client_id = normalize_client_id(client_id)
    stored_profile = user_data_store().profile(normalized_client_id)
    if stored_profile is not None:
        return stored_profile
    return {
        "client_id": normalized_client_id,
        "storage": "sqlite",
        "account_kind": "local" if normalized_client_id == DEFAULT_CLIENT_ID else "guest",
        "server_side": True,
        "authenticated": False,
        "email": "",
        "provider": "",
        "display_name": "",
    }


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = deep_merge(DEFAULT_CONFIG, config)
    # Market data is selected by the server environment, never by browser input.
    # Public deployments stay on demo unless the operator explicitly enables a provider.
    merged["provider"] = server_market_data_provider()

    positions = normalize_positions(merged.get("positions", []))
    watchlist = normalize_symbols(merged.get("watchlist", []))
    for position in positions:
        if position["symbol"] not in watchlist:
            watchlist.append(position["symbol"])
    for market_symbol in ("SPY", "QQQ"):
        if market_symbol not in watchlist:
            watchlist.append(market_symbol)
    merged["watchlist"] = watchlist[:30]
    merged["positions"] = positions

    alerts = merged["alerts"]
    alerts["rsi_period"] = max(2, int(alerts.get("rsi_period", 14)))
    alerts["rsi_oversold"] = min(50, max(1, float(alerts.get("rsi_oversold", 30))))
    alerts["rsi_deep_oversold"] = min(alerts["rsi_oversold"], max(1, float(alerts.get("rsi_deep_oversold", 25))))
    alerts["rsi_recovery"] = min(70, max(alerts["rsi_oversold"], float(alerts.get("rsi_recovery", 35))))
    alerts["rsi_overheated"] = min(99, max(50, float(alerts.get("rsi_overheated", 70))))
    alerts["ma_periods"] = [20, 60, 120]
    alerts["volume_period"] = max(2, int(alerts.get("volume_period", 20)))
    alerts["volume_spike_multiple"] = max(1.0, float(alerts.get("volume_spike_multiple", 2.0)))
    alerts["large_cap_volume_spike_multiple"] = max(1.0, float(alerts.get("large_cap_volume_spike_multiple", 1.5)))
    alerts["gap_pct"] = max(0.5, float(alerts.get("gap_pct", 3.0)))
    alerts["high_low_periods"] = [60, 120]
    alerts["auto_refresh_minutes"] = max(MIN_AUTO_REFRESH_MINUTES, int(alerts.get("auto_refresh_minutes", 30)))
    distance = deep_merge(DEFAULT_CONFIG["alerts"]["ma_distance_pct"], alerts.get("ma_distance_pct", {}))
    alerts["ma_distance_pct"] = {key: float(value) for key, value in distance.items()}
    quiet_hours = deep_merge(DEFAULT_CONFIG["alerts"]["quiet_hours"], alerts.get("quiet_hours", {}))
    quiet_hours["enabled"] = bool(quiet_hours.get("enabled", False))
    alerts["quiet_hours"] = quiet_hours

    alpaca = merged["alpaca"]
    alpaca["feed"] = str(alpaca.get("feed", "iex")).lower()
    alpaca["timeframe"] = str(alpaca.get("timeframe", "1Day"))
    alpaca["adjustment"] = str(alpaca.get("adjustment", "split")).lower()
    if alpaca["adjustment"] not in {"raw", "split", "dividend", "spin-off", "all"}:
        alpaca["adjustment"] = "split"
    alpaca["lookback_days"] = max(180, min(1000, int(alpaca.get("lookback_days", 900))))

    chart = deep_merge(DEFAULT_CONFIG["chart"], merged.get("chart", {}))
    chart["default_timeframe"] = str(chart.get("default_timeframe", "D")).upper()
    if chart["default_timeframe"] not in {"D", "W"}:
        chart["default_timeframe"] = "D"
    chart["default_range"] = str(chart.get("default_range", "6M")).upper()
    if chart["default_range"] not in {"3M", "6M", "1Y", "ALL"}:
        chart["default_range"] = "6M"
    chart["zoom_enabled"] = bool(chart.get("zoom_enabled", True))
    merged["chart"] = chart

    fear = deep_merge(DEFAULT_CONFIG["fear"], merged.get("fear", {}))
    fear["source"] = str(fear.get("source", "cboe")).lower()
    if fear["source"] == "fred":
        fear["source"] = "cboe"
    if fear["source"] not in {"cboe", "demo", "off"}:
        fear["source"] = "cboe"
    fear["lookback_days"] = max(30, min(1000, int(fear.get("lookback_days", 180))))
    fear["elevated_threshold"] = max(10.0, float(fear.get("elevated_threshold", 20.0)))
    fear["fear_threshold"] = max(fear["elevated_threshold"], float(fear.get("fear_threshold", 30.0)))
    fear["panic_threshold"] = max(fear["fear_threshold"], float(fear.get("panic_threshold", 40.0)))
    fear["spike_5d_pct"] = max(5.0, float(fear.get("spike_5d_pct", 20.0)))
    fear["calming_5d_pct"] = min(-1.0, float(fear.get("calming_5d_pct", -12.0)))
    fear["fallback_to_demo"] = bool(fear.get("fallback_to_demo", True))
    merged["fear"] = fear

    preferences = dict(DEFAULT_ALERT_PREFERENCES)
    if isinstance(merged.get("alert_preferences"), dict):
        for signal_type, mode in merged["alert_preferences"].items():
            normalized_mode = str(mode).lower()
            if signal_type in preferences and normalized_mode in VALID_DELIVERY_MODES:
                preferences[signal_type] = normalized_mode
    merged["alert_preferences"] = preferences
    return merged


def normalize_positions(positions: Any) -> list[dict[str, Any]]:
    if isinstance(positions, dict):
        iterable = list(positions.values())
    elif isinstance(positions, list):
        iterable = positions
    else:
        iterable = []

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in iterable:
        if not isinstance(raw, dict):
            continue
        symbol = str(raw.get("symbol", "")).strip().upper()
        if not symbol:
            continue
        if not SYMBOL_RE.match(symbol):
            raise ValueError(f"Invalid ticker symbol: {symbol}")
        if symbol in seen:
            continue
        seen.add(symbol)
        normalized.append(
            {
                "symbol": symbol,
                "held": bool(raw.get("held", False)),
                "average_entry_price": _optional_float(raw.get("average_entry_price")),
                "quantity": _optional_float(raw.get("quantity")),
                "entry_date": str(raw.get("entry_date", "") or ""),
                "target_return_pct": _float_or_default(raw.get("target_return_pct"), 15.0),
                "stop_loss_pct": _float_or_default(raw.get("stop_loss_pct"), -7.0),
                "trailing_stop_pct": _float_or_default(raw.get("trailing_stop_pct"), -8.0),
                "holding_style": str(raw.get("holding_style", "swing") or "swing"),
                "next_earnings_date": str(raw.get("next_earnings_date", "") or ""),
                "notes": str(raw.get("notes", "") or ""),
            }
        )
    return normalized[:30]


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    parsed = float(value)
    if parsed <= 0:
        return None
    return parsed


def _float_or_default(value: Any, default: float) -> float:
    if value in (None, ""):
        return default
    return float(value)


def read_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_PATH.exists():
        return values
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def save_alpaca_credentials(key_id: str, secret: str) -> None:
    key_id = str(key_id or "").strip()
    secret = str(secret or "").strip()
    if not key_id or not secret:
        raise ValueError("Alpaca API Key ID와 Secret Key를 모두 입력해주세요.")
    if any(char in key_id + secret for char in "\r\n"):
        raise ValueError("Alpaca API 키는 한 줄 문자열이어야 합니다.")
    write_env_values(
        {
            "APCA_API_KEY_ID": key_id,
            "APCA_API_SECRET_KEY": secret,
        }
    )


def delete_alpaca_credentials() -> None:
    remove_env_keys({"APCA_API_KEY_ID", "APCA_API_SECRET_KEY", "ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"})


def write_env_values(updates: dict[str, str]) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    written: set[str] = set()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            output.append(f"{key}={updates[key]}")
            written.add(key)
        else:
            output.append(line)
    for key, value in updates.items():
        if key not in written:
            output.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def remove_env_keys(keys: set[str]) -> None:
    if not ENV_PATH.exists():
        return
    output: list[str] = []
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in keys:
                continue
        output.append(line)
    ENV_PATH.write_text("\n".join(output).rstrip() + ("\n" if output else ""), encoding="utf-8")


def alpaca_credentials() -> tuple[str, str]:
    file_env = read_env_file()
    key_id = os.getenv("APCA_API_KEY_ID") or os.getenv("ALPACA_API_KEY_ID") or file_env.get("APCA_API_KEY_ID") or file_env.get("ALPACA_API_KEY_ID") or ""
    secret = os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_API_SECRET_KEY") or file_env.get("APCA_API_SECRET_KEY") or file_env.get("ALPACA_API_SECRET_KEY") or ""
    return key_id, secret


def server_market_data_provider() -> str:
    file_env = read_env_file()
    provider = (
        os.getenv("PULSEEDGE_MARKET_DATA_PROVIDER")
        or file_env.get("PULSEEDGE_MARKET_DATA_PROVIDER")
        or "demo"
    ).strip().lower()
    return provider if provider in {"demo", "alpaca"} else "demo"


def supabase_auth_config() -> dict[str, Any]:
    file_env = read_env_file()
    project_url = (
        os.getenv("SUPABASE_URL")
        or file_env.get("SUPABASE_URL")
        or ""
    ).strip().rstrip("/")
    publishable_key = (
        os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or file_env.get("SUPABASE_PUBLISHABLE_KEY")
        or file_env.get("SUPABASE_ANON_KEY")
        or ""
    ).strip()
    enabled = bool(project_url and publishable_key)
    partially_configured = bool(project_url or publishable_key) and not enabled
    server_key = _supabase_server_key(file_env)
    return {
        "enabled": enabled,
        "provider": "supabase",
        "project_url": project_url if enabled else "",
        "publishable_key": publishable_key if enabled else "",
        "email_enabled": enabled and _env_flag("SUPABASE_EMAIL_ENABLED", file_env, True),
        "google_enabled": enabled and _env_flag("SUPABASE_GOOGLE_ENABLED", file_env, False),
        "account_deletion_enabled": enabled and bool(server_key),
        "status": "ready" if enabled else "misconfigured" if partially_configured else "not_configured",
    }


def supabase_admin_config() -> dict[str, Any]:
    file_env = read_env_file()
    auth = supabase_auth_config()
    server_key = _supabase_server_key(file_env)
    enabled = bool(auth["enabled"] and server_key)
    return {
        "enabled": enabled,
        "project_url": auth["project_url"] if enabled else "",
        "server_key": server_key if enabled else "",
    }


def delete_legacy_client_files(public_ids: list[str]) -> None:
    for public_id in public_ids:
        try:
            path = client_config_path(public_id)
        except ValueError:
            continue
        if path != CONFIG_PATH:
            path.unlink(missing_ok=True)


def _supabase_server_key(file_env: dict[str, str]) -> str:
    return (
        os.getenv("SUPABASE_SECRET_KEY")
        or file_env.get("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or file_env.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()


def _env_flag(name: str, file_env: dict[str, str], default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        raw = file_env.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def credential_status() -> dict[str, bool | str]:
    key_id, secret = alpaca_credentials()
    ready = bool(key_id and secret)
    return {
        "active_market_data_provider": server_market_data_provider(),
        "market_data_server_ready": ready,
        "server_managed": True,
        "alpaca_key_id_present": bool(key_id),
        "alpaca_secret_present": bool(secret),
    }
