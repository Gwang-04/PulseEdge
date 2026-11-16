from __future__ import annotations

import csv
import io
import json
import math
import random
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, time, timedelta, timezone
from threading import Lock
from typing import Any
from zoneinfo import ZoneInfo

from settings import alpaca_credentials

ALPACA_BARS_URL = "https://data.alpaca.markets/v2/stocks/{symbol}/bars"
CBOE_VIX_URL = "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
FRED_VIX_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
BAR_CACHE_TTL_SECONDS = 8 * 60
BAR_STALE_MAX_SECONDS = 24 * 60 * 60
VIX_CACHE_TTL_SECONDS = 60 * 60
NEW_YORK_TZ = ZoneInfo("America/New_York")
_BAR_CACHE: dict[str, Any] = {}
_BAR_STATUS: dict[str, Any] = {}
_VIX_CACHE: dict[str, Any] = {}
_CACHE_LOCK = Lock()
_METRICS: dict[str, Any] = {}


def reset_market_data_usage() -> None:
    with _CACHE_LOCK:
        _METRICS.clear()
        _METRICS.update(
            {
                "started_at": datetime.now(timezone.utc).isoformat(),
                "bar_cache_hits": 0,
                "bar_cache_misses": 0,
                "bar_stale_fallbacks": 0,
                "demo_generations": 0,
                "alpaca_requests": 0,
                "alpaca_errors": 0,
                "alpaca_rate_limited": 0,
                "alpaca_rate_limit": {},
                "vix_cache_hits": 0,
                "vix_cache_misses": 0,
                "vix_requests": 0,
                "vix_errors": 0,
            }
        )


reset_market_data_usage()


def fetch_bars(symbol: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    cache_key = bars_cache_key(symbol, config)
    cached = cached_bars(cache_key)
    if cached is not None:
        increment_metric("bar_cache_hits")
        record_bar_status(cache_key, cached, state="fresh", served_from_cache=True)
        return cached
    increment_metric("bar_cache_misses")

    provider = str(config.get("provider", "demo")).lower()
    if provider == "alpaca":
        try:
            bars = fetch_alpaca_bars(symbol, config)
        except Exception:
            stale = cached_bars(cache_key, allow_stale=True)
            if stale is None:
                raise
            increment_metric("bar_stale_fallbacks")
            record_bar_status(cache_key, stale, state="stale", served_from_cache=True)
            return stale
    else:
        increment_metric("demo_generations")
        bars = generate_demo_bars(symbol, int(config["alpaca"].get("lookback_days", 420)))
    store_bars_cache(cache_key, bars)
    record_bar_status(cache_key, bars, state="fresh", served_from_cache=False)
    return copy_bars(bars)


def bars_cache_key(symbol: str, config: dict[str, Any]) -> str:
    alpaca = config.get("alpaca", {})
    provider = str(config.get("provider", "demo")).lower()
    feed = str(alpaca.get("feed", "iex")).lower()
    timeframe = str(alpaca.get("timeframe", "1Day"))
    adjustment = str(alpaca.get("adjustment", "split")).lower()
    lookback_days = int(alpaca.get("lookback_days", 420))
    return f"{provider}:{symbol.upper()}:{feed}:{timeframe}:{adjustment}:{lookback_days}"


def cached_bars(cache_key: str, allow_stale: bool = False) -> list[dict[str, Any]] | None:
    now_ts = datetime.now(timezone.utc).timestamp()
    with _CACHE_LOCK:
        cached = _BAR_CACHE.get(cache_key)
        if not cached:
            return None
        age_seconds = now_ts - cached["stored_at"]
        if age_seconds >= BAR_STALE_MAX_SECONDS:
            _BAR_CACHE.pop(cache_key, None)
            _BAR_STATUS.pop(cache_key, None)
            return None
        if age_seconds >= BAR_CACHE_TTL_SECONDS and not allow_stale:
            return None
        return copy_bars(cached["bars"])


def store_bars_cache(cache_key: str, bars: list[dict[str, Any]]) -> None:
    with _CACHE_LOCK:
        _BAR_CACHE[cache_key] = {
            "stored_at": datetime.now(timezone.utc).timestamp(),
            "bars": copy_bars(bars),
        }


def copy_bars(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(bar) for bar in bars]


def record_bar_status(
    cache_key: str,
    bars: list[dict[str, Any]],
    state: str,
    served_from_cache: bool,
) -> None:
    now = datetime.now(timezone.utc)
    with _CACHE_LOCK:
        cached = _BAR_CACHE.get(cache_key, {})
        fetched_at = float(cached.get("stored_at", now.timestamp()))
        _BAR_STATUS[cache_key] = {
            "state": state,
            "served_from_cache": served_from_cache,
            "fetched_at": fetched_at,
            "checked_at": now.timestamp(),
            "last_bar": str(bars[-1].get("time", "")) if bars else "",
        }


def bar_data_status(symbol: str, config: dict[str, Any]) -> dict[str, Any]:
    cache_key = bars_cache_key(symbol, config)
    now = datetime.now(timezone.utc)
    with _CACHE_LOCK:
        status = dict(_BAR_STATUS.get(cache_key, {}))
        cached = _BAR_CACHE.get(cache_key)
        if not status and cached:
            stored_at = float(cached.get("stored_at", now.timestamp()))
            status = {
                "state": "fresh" if now.timestamp() - stored_at < BAR_CACHE_TTL_SECONDS else "stale",
                "served_from_cache": True,
                "fetched_at": stored_at,
                "checked_at": now.timestamp(),
                "last_bar": str(cached.get("bars", [{}])[-1].get("time", "")) if cached.get("bars") else "",
            }

    fetched_timestamp = status.get("fetched_at")
    checked_timestamp = status.get("checked_at")
    return {
        "state": status.get("state", "unknown"),
        "stale": status.get("state") == "stale",
        "served_from_cache": bool(status.get("served_from_cache", False)),
        "fetched_at": datetime.fromtimestamp(fetched_timestamp, timezone.utc).isoformat() if fetched_timestamp else "",
        "checked_at": datetime.fromtimestamp(checked_timestamp, timezone.utc).isoformat() if checked_timestamp else "",
        "age_seconds": max(0, round(now.timestamp() - float(fetched_timestamp))) if fetched_timestamp else None,
        "last_bar": status.get("last_bar", ""),
    }


def increment_metric(key: str, amount: int = 1) -> None:
    with _CACHE_LOCK:
        _METRICS[key] = int(_METRICS.get(key, 0)) + amount


def record_alpaca_rate_limit_headers(headers: Any) -> None:
    rate_limit = {
        "limit": headers.get("X-RateLimit-Limit") if headers else None,
        "remaining": headers.get("X-RateLimit-Remaining") if headers else None,
        "reset": headers.get("X-RateLimit-Reset") if headers else None,
    }
    if not any(rate_limit.values()):
        return
    with _CACHE_LOCK:
        _METRICS["alpaca_rate_limit"] = rate_limit


def market_data_usage_snapshot() -> dict[str, Any]:
    with _CACHE_LOCK:
        metrics = dict(_METRICS)
        bar_entries = len(_BAR_CACHE)
        vix_entries = len(_VIX_CACHE)
    bar_total = int(metrics.get("bar_cache_hits", 0)) + int(metrics.get("bar_cache_misses", 0))
    vix_total = int(metrics.get("vix_cache_hits", 0)) + int(metrics.get("vix_cache_misses", 0))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": metrics.get("started_at"),
        "bar_cache": {
            "entries": bar_entries,
            "ttl_seconds": BAR_CACHE_TTL_SECONDS,
            "stale_max_seconds": BAR_STALE_MAX_SECONDS,
            "hits": int(metrics.get("bar_cache_hits", 0)),
            "misses": int(metrics.get("bar_cache_misses", 0)),
            "stale_fallbacks": int(metrics.get("bar_stale_fallbacks", 0)),
            "hit_rate_pct": round((int(metrics.get("bar_cache_hits", 0)) / bar_total) * 100, 1) if bar_total else None,
        },
        "alpaca": {
            "requests": int(metrics.get("alpaca_requests", 0)),
            "errors": int(metrics.get("alpaca_errors", 0)),
            "rate_limited": int(metrics.get("alpaca_rate_limited", 0)),
            "last_rate_limit": metrics.get("alpaca_rate_limit", {}),
        },
        "vix": {
            "cache_entries": vix_entries,
            "cache_hits": int(metrics.get("vix_cache_hits", 0)),
            "cache_misses": int(metrics.get("vix_cache_misses", 0)),
            "hit_rate_pct": round((int(metrics.get("vix_cache_hits", 0)) / vix_total) * 100, 1) if vix_total else None,
            "requests": int(metrics.get("vix_requests", 0)),
            "errors": int(metrics.get("vix_errors", 0)),
        },
        "demo_generations": int(metrics.get("demo_generations", 0)),
    }


def fetch_alpaca_bars(symbol: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    key_id, secret = alpaca_credentials()
    if not key_id or not secret:
        raise RuntimeError("서버 환경변수에 Alpaca API 키가 없습니다.")

    alpaca = config["alpaca"]
    end = completed_daily_bars_end()
    start = end - timedelta(days=int(alpaca.get("lookback_days", 420)))
    params = {
        "timeframe": alpaca.get("timeframe", "1Day"),
        "start": start.isoformat().replace("+00:00", "Z"),
        "end": end.isoformat().replace("+00:00", "Z"),
        "limit": "1000",
        "sort": "asc",
        "feed": alpaca.get("feed", "iex"),
        "adjustment": alpaca.get("adjustment", "split"),
    }
    url = ALPACA_BARS_URL.format(symbol=urllib.parse.quote(symbol)) + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret,
            "User-Agent": "pulseedge/0.1",
        },
    )
    increment_metric("alpaca_requests")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            record_alpaca_rate_limit_headers(response.headers)
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        record_alpaca_rate_limit_headers(exc.headers)
        increment_metric("alpaca_errors")
        if exc.code == 429:
            increment_metric("alpaca_rate_limited")
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Alpaca request failed for {symbol}: HTTP {exc.code} {body[:250]}") from exc
    except urllib.error.URLError as exc:
        increment_metric("alpaca_errors")
        raise RuntimeError(f"Alpaca request failed for {symbol}: {exc.reason}") from exc

    bars = payload.get("bars", [])
    if not bars:
        increment_metric("alpaca_errors")
        raise RuntimeError(f"No bars returned for {symbol}")
    return [
        {
            "time": item["t"],
            "open": float(item["o"]),
            "high": float(item["h"]),
            "low": float(item["l"]),
            "close": float(item["c"]),
            "volume": float(item.get("v", 0)),
        }
        for item in bars
    ]


def completed_daily_bars_end(now_utc: datetime | None = None) -> datetime:
    current_utc = now_utc or datetime.now(timezone.utc)
    if current_utc.tzinfo is None:
        current_utc = current_utc.replace(tzinfo=timezone.utc)
    current_et = current_utc.astimezone(NEW_YORK_TZ)
    completed_date = current_et.date() if current_et.time() >= time(16, 15) else current_et.date() - timedelta(days=1)
    next_midnight_et = datetime.combine(completed_date + timedelta(days=1), time.min, tzinfo=NEW_YORK_TZ)
    return (next_midnight_et - timedelta(microseconds=1)).astimezone(timezone.utc)


def fetch_vix_history(config: dict[str, Any]) -> dict[str, Any] | None:
    fear = config.get("fear", {})
    source = str(fear.get("source", "cboe")).lower()
    if source == "off":
        return None
    lookback_days = int(fear.get("lookback_days", 180))
    cache_key = f"{source}:{lookback_days}"
    now_ts = datetime.now(timezone.utc).timestamp()
    cached = _VIX_CACHE.get(cache_key)
    if cached and now_ts - cached["stored_at"] < VIX_CACHE_TTL_SECONDS:
        increment_metric("vix_cache_hits")
        return cached["payload"]
    increment_metric("vix_cache_misses")
    if source == "demo":
        payload = {"source": "demo", "fallback": False, "bars": generate_demo_vix_history(lookback_days)}
        _VIX_CACHE[cache_key] = {"stored_at": now_ts, "payload": payload}
        return payload
    errors: list[str] = []
    if source == "cboe":
        try:
            payload = {"source": "cboe", "fallback": False, "bars": fetch_cboe_vix_history(lookback_days)}
        except Exception as exc:
            increment_metric("vix_errors")
            errors.append(f"CBOE: {exc}")
            try:
                payload = {
                    "source": "fred",
                    "fallback": True,
                    "fallback_from": "cboe",
                    "fallback_reason": str(exc),
                    "bars": fetch_fred_vix_history(lookback_days),
                }
            except Exception as fred_exc:
                increment_metric("vix_errors")
                errors.append(f"FRED: {fred_exc}")
                payload = None
    else:
        try:
            payload = {"source": "fred", "fallback": False, "bars": fetch_fred_vix_history(lookback_days)}
        except Exception as exc:
            increment_metric("vix_errors")
            errors.append(f"FRED: {exc}")
            payload = None
    if payload is None:
        message = "; ".join(errors)
        if not fear.get("fallback_to_demo", True):
            raise RuntimeError(f"VIX 데이터를 가져오지 못했습니다: {message}")
        payload = {
            "source": "demo",
            "fallback": True,
            "fallback_from": source,
            "fallback_reason": message,
            "error": message,
            "bars": generate_demo_vix_history(lookback_days),
        }
    _VIX_CACHE[cache_key] = {"stored_at": now_ts, "payload": payload}
    return payload


def fetch_cboe_vix_history(lookback_days: int = 180) -> list[dict[str, Any]]:
    increment_metric("vix_requests")
    text = fetch_remote_text(CBOE_VIX_URL)
    rows: list[dict[str, Any]] = []
    for row in csv.DictReader(io.StringIO(text)):
        date_text = str(row.get("DATE", "")).strip()
        value = str(row.get("CLOSE", "")).strip()
        if not date_text or not value:
            continue
        try:
            day = datetime.strptime(date_text, "%m/%d/%Y").date().isoformat()
            close = float(value)
        except ValueError:
            continue
        rows.append({"time": day, "close": close})
    if not rows:
        raise RuntimeError("CBOE VIX 응답에 유효한 종가가 없습니다.")
    return rows[-lookback_days:]


def fetch_fred_vix_history(lookback_days: int = 180) -> list[dict[str, Any]]:
    increment_metric("vix_requests")
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=max(30, lookback_days) + 14)
    params = urllib.parse.urlencode({"id": "VIXCLS", "cosd": start.isoformat(), "coed": end.isoformat()})
    url = f"{FRED_VIX_URL}?{params}"
    text = fetch_remote_text(url)
    rows: list[dict[str, Any]] = []
    for row in csv.DictReader(io.StringIO(text)):
        value = row.get("VIXCLS", ".")
        if not value or value == ".":
            continue
        rows.append({"time": row["observation_date"], "close": float(value)})
    if not rows:
        raise RuntimeError("FRED VIXCLS 응답에 유효한 값이 없습니다.")
    return rows[-lookback_days:]


def fetch_remote_text(url: str) -> str:
    try:
        return fetch_text_with_curl(url)
    except Exception as curl_exc:
        request = urllib.request.Request(
            url,
            headers={"Accept": "text/csv", "User-Agent": "pulseedge/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                return response.read().decode("utf-8-sig")
        except Exception as urllib_exc:
            raise RuntimeError(f"curl failed: {curl_exc}; urllib failed: {urllib_exc}") from urllib_exc


def fetch_text_with_curl(url: str) -> str:
    curl_path = shutil.which("curl.exe") or shutil.which("curl")
    if not curl_path:
        raise RuntimeError("curl executable not found")
    completed = subprocess.run(
        [curl_path, "-L", "--max-time", "20", "-sS", url],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or f"curl exited with {completed.returncode}"
        raise RuntimeError(message)
    if not completed.stdout.strip():
        raise RuntimeError("empty curl response")
    return completed.stdout


def generate_demo_vix_history(lookback_days: int = 180) -> list[dict[str, Any]]:
    rng = random.Random(20260901)
    now = datetime.now(timezone.utc).date()
    dates = []
    cursor = now - timedelta(days=max(30, lookback_days) * 1.6)
    while cursor <= now:
        if cursor.weekday() < 5:
            dates.append(cursor)
        cursor += timedelta(days=1)
    dates = dates[-lookback_days:]
    rows: list[dict[str, Any]] = []
    value = 18.0
    for index, day in enumerate(dates):
        cycle = math.sin(index / 15.0) * 2.4
        shock = rng.gauss(0.0, 1.1)
        if index > len(dates) - 9:
            shock += 1.5
        value = max(10.0, min(42.0, value * 0.88 + (17.5 + cycle + shock) * 0.12))
        rows.append({"time": day.isoformat(), "close": round(value, 2)})
    return rows


def generate_demo_bars(symbol: str, lookback_days: int = 900) -> list[dict[str, Any]]:
    seed = sum(ord(char) for char in symbol)
    rng = random.Random(seed)
    bars: list[dict[str, Any]] = []
    price = 80 + seed % 220
    now = datetime.now(timezone.utc).replace(hour=21, minute=0, second=0, microsecond=0)
    days = max(260, lookback_days)
    dates: list[datetime] = []
    cursor = now - timedelta(days=days * 1.55)
    while cursor <= now:
        if cursor.weekday() < 5:
            dates.append(cursor)
        cursor += timedelta(days=1)
    dates = dates[-days:]
    drift = 0.0006 if seed % 3 else -0.0002
    for index, day in enumerate(dates):
        cycle = math.sin(index / 19.0 + seed) * 0.012
        shock = rng.gauss(drift + cycle, 0.018)
        if index > len(dates) - 8 and seed % 2 == 0:
            shock -= 0.025
        open_price = price
        close = max(3.0, price * (1 + shock))
        high = max(open_price, close) * (1 + abs(rng.gauss(0.006, 0.006)))
        low = min(open_price, close) * (1 - abs(rng.gauss(0.006, 0.006)))
        volume = int(4_000_000 + rng.random() * 20_000_000)
        if index == len(dates) - 1 and seed % 5 == 0:
            volume *= 3
        bars.append(
            {
                "time": day.isoformat().replace("+00:00", "Z"),
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
            }
        )
        price = close
    return bars
