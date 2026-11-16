from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from functools import lru_cache
import json
import mimetypes
import socket
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import perf_counter
from typing import Any

from auth_service import AuthAdminError, AuthError, AuthIdentity, SupabaseAuthAdmin, SupabaseAuthVerifier, bearer_token
from backtest_engine import DEFAULT_RULE_KEY, backtest_symbol_signals
from market_data import bar_data_status, fetch_bars, fetch_vix_history, market_data_usage_snapshot
from settings import (
    APP_DIR,
    SIGNAL_GROUPS,
    config_profile,
    credential_status,
    delete_legacy_client_files,
    load_config,
    normalize_client_id,
    normalize_symbols,
    save_config,
    supabase_auth_config,
    supabase_admin_config,
    user_data_store,
)
from signal_engine import analyze_symbol, apply_market_regime, build_vix_state

STATIC_DIR = APP_DIR / "static"
ANALYZE_MAX_WORKERS = 6


class StockSignalHandler(BaseHTTPRequestHandler):
    server_version = "PulseEdge/0.1"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/config":
            self.handle_config_get()
            return
        if parsed.path == "/api/auth/config":
            self.send_json({"auth": supabase_auth_config()})
            return
        if parsed.path == "/api/install-info":
            self.send_json(install_info(self.server.server_address))
            return
        if parsed.path == "/api/data-health":
            self.handle_data_health(parsed)
            return
        if parsed.path == "/api/usage":
            self.send_json({"usage": market_data_usage_snapshot()})
            return
        if parsed.path == "/api/analyze":
            self.handle_analyze(parsed)
            return
        if parsed.path == "/api/backtest":
            self.handle_backtest(parsed)
            return
        if parsed.path == "/":
            self.serve_file(STATIC_DIR / "index.html")
            return
        path = (STATIC_DIR / parsed.path.lstrip("/")).resolve()
        if not str(path).startswith(str(STATIC_DIR.resolve())):
            self.send_error(403)
            return
        self.serve_file(path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/config":
            self.handle_config_save()
            return
        if parsed.path == "/api/auth/session":
            self.handle_auth_session()
            return
        if parsed.path == "/api/account/delete":
            self.handle_account_delete()
            return
        self.send_error(404)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        return payload if isinstance(payload, dict) else {}

    def guest_client_id(self) -> str:
        return normalize_client_id(self.headers.get("X-PulseEdge-Client-Id"))

    def auth_identity(self) -> AuthIdentity | None:
        token = bearer_token(self.headers.get("Authorization"))
        if not token:
            return None
        auth = supabase_auth_config()
        if not auth["enabled"]:
            raise AuthError("로그인 서버가 아직 설정되지 않았습니다.")
        return cached_auth_verifier(auth["project_url"], auth["publishable_key"]).verify(token)

    def client_id(self) -> str:
        guest_id = self.guest_client_id()
        identity = self.auth_identity()
        if identity is None:
            return guest_id
        return user_data_store().link_authenticated_user(
            guest_id,
            "supabase",
            identity.subject,
            identity.provider,
            identity.email,
            identity.display_name,
        )

    def handle_auth_session(self) -> None:
        try:
            if self.auth_identity() is None:
                raise AuthError("로그인이 필요합니다.")
            account_id = self.client_id()
            self.send_json({"profile": config_profile(account_id)})
        except AuthError as exc:
            self.send_json({"error": str(exc)}, status=401)

    def handle_account_delete(self) -> None:
        try:
            identity = self.auth_identity()
            if identity is None:
                raise AuthError("로그인이 필요합니다.")
            payload = self.read_json_body()
            confirmation = str(payload.get("confirmation", "")).strip().lower()
            if not identity.email or confirmation != identity.email.lower():
                self.send_json({"error": "로그인 이메일을 정확히 입력해 주세요."}, status=400)
                return
            admin = supabase_admin_config()
            if not admin["enabled"]:
                self.send_json({"error": "계정 삭제 서버 설정이 아직 완료되지 않았습니다."}, status=503)
                return
            SupabaseAuthAdmin(admin["project_url"], admin["server_key"]).delete_user(identity.subject)
            deleted_public_ids = user_data_store().delete_authenticated_user("supabase", identity.subject)
            delete_legacy_client_files(deleted_public_ids)
            self.send_json({"deleted": True})
        except AuthError as exc:
            self.send_json({"error": str(exc)}, status=401)
        except AuthAdminError as exc:
            self.send_json({"error": str(exc)}, status=502)
        except Exception:
            self.send_json({"error": "계정 데이터 삭제를 완료하지 못했습니다. 고객지원에 문의해 주세요."}, status=500)

    def handle_config_get(self) -> None:
        try:
            client_id = self.client_id()
            self.send_json(
                {
                    "config": load_config(client_id),
                    "credentials": credential_status(),
                    "signal_groups": SIGNAL_GROUPS,
                    "profile": config_profile(client_id),
                }
            )
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=400)

    def handle_config_save(self) -> None:
        try:
            client_id = self.client_id()
            payload = self.read_json_body()
            saved = save_config(payload, client_id)
            self.send_json(
                {
                    "config": saved,
                    "credentials": credential_status(),
                    "signal_groups": SIGNAL_GROUPS,
                    "profile": config_profile(client_id),
                }
            )
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def handle_data_health(self, parsed: urllib.parse.ParseResult) -> None:
        try:
            query = urllib.parse.parse_qs(parsed.query)
            symbol = normalize_symbols(query_value(query, "symbol", "AAPL"))[0]
            self.send_json(build_data_health(symbol, load_config(self.client_id())))
        except ValueError as exc:
            self.send_json({"error": str(exc), "credentials": credential_status()}, status=400)

    def handle_analyze(self, parsed: urllib.parse.ParseResult) -> None:
        started_at = perf_counter()
        query = urllib.parse.parse_qs(parsed.query)
        try:
            client_id = self.client_id()
            config = load_config(client_id)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=400)
            return
        watch_config = watch_only_config(config)
        if "symbols" in query:
            try:
                config["watchlist"] = normalize_symbols(query["symbols"][0])
                watch_config["watchlist"] = config["watchlist"]
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=400)
                return
        results, watch_results = analyze_watchlist(config["watchlist"], config, watch_config)
        vix_history = fetch_vix_history(config)
        market = apply_market_regime(results, config, vix_history)
        apply_market_regime(watch_results, watch_config, vix_history)
        elapsed_ms = round((perf_counter() - started_at) * 1000)
        data_freshness = summarize_data_freshness(results)
        self.send_json(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "provider": config.get("provider", "demo"),
                "feed": stock_feed(config),
                "elapsed_ms": elapsed_ms,
                "symbols": len(config["watchlist"]),
                "worker_count": worker_count(config["watchlist"]),
                "profile": config_profile(client_id),
                "usage": market_data_usage_snapshot(),
                "data_freshness": data_freshness,
                "market": market,
                "results": results,
                "watch_results": watch_results,
            }
        )

    def handle_backtest(self, parsed: urllib.parse.ParseResult) -> None:
        try:
            query = urllib.parse.parse_qs(parsed.query)
            config = load_config(self.client_id())
            default_symbol = config["watchlist"][0]
            symbol = normalize_symbols(query_value(query, "symbol", default_symbol))[0]
            min_score = query_int(query, "min_score", 70, 0, 100)
            lookback = query_int(query, "lookback", 252, 60, 720)
            cooldown_days = query_int(query, "cooldown_days", 10, 1, 60)
            rule_key = query_value(query, "rule", DEFAULT_RULE_KEY)
            bars = fetch_bars(symbol, config)
            payload = backtest_symbol_signals(symbol, bars, config, min_score, lookback, cooldown_days, rule_key)
            payload["generated_at"] = datetime.now(timezone.utc).isoformat()
            payload["provider"] = config.get("provider", "demo")
            payload["feed"] = stock_feed(config)
            payload["data_status"] = bar_data_status(symbol, config)
            self.send_json(payload)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def watch_only_config(config: dict[str, Any]) -> dict[str, Any]:
    output = deepcopy(config)
    output["positions"] = []
    return output


@lru_cache(maxsize=4)
def cached_auth_verifier(project_url: str, publishable_key: str) -> SupabaseAuthVerifier:
    return SupabaseAuthVerifier(project_url, publishable_key)


def analyze_watchlist(
    symbols: list[str],
    config: dict[str, Any],
    watch_config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not symbols:
        return [], []

    results: list[dict[str, Any] | None] = [None] * len(symbols)
    watch_results: list[dict[str, Any] | None] = [None] * len(symbols)
    workers = worker_count(symbols)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(analyze_watchlist_symbol, index, symbol, config, watch_config)
            for index, symbol in enumerate(symbols)
        ]
        for future in as_completed(futures):
            index, result, watch_result = future.result()
            results[index] = result
            watch_results[index] = watch_result

    return [result for result in results if result is not None], [result for result in watch_results if result is not None]


def analyze_watchlist_symbol(
    index: int,
    symbol: str,
    config: dict[str, Any],
    watch_config: dict[str, Any],
) -> tuple[int, dict[str, Any], dict[str, Any]]:
    try:
        bars = fetch_bars(symbol, config)
        data_status = bar_data_status(symbol, config)
        result = analyze_symbol(symbol, bars, config)
        watch_result = analyze_symbol(symbol, bars, watch_config)
        result["data_status"] = data_status
        watch_result["data_status"] = data_status
        return index, result, watch_result
    except Exception as exc:
        error_result = {"symbol": symbol, "error": str(exc), "alert_level": "오류", "signals": []}
        return index, error_result, dict(error_result)


def worker_count(symbols: list[str]) -> int:
    return max(1, min(ANALYZE_MAX_WORKERS, len(symbols)))


def summarize_data_freshness(results: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [result.get("data_status", {}) for result in results if result.get("data_status")]
    known = [status for status in statuses if status.get("state") in {"fresh", "stale"}]
    stale_symbols = [
        result.get("symbol", "")
        for result in results
        if result.get("data_status", {}).get("stale")
    ]
    fetched_times = sorted(status.get("fetched_at") for status in known if status.get("fetched_at"))
    last_bars = sorted(status.get("last_bar") for status in known if status.get("last_bar"))
    state = "stale" if stale_symbols else "fresh" if known else "unknown"
    return {
        "state": state,
        "stale": state == "stale",
        "stale_symbols": stale_symbols,
        "fresh_symbols": len(known) - len(stale_symbols),
        "symbol_count": len(known),
        "served_from_cache_count": sum(1 for status in known if status.get("served_from_cache")),
        "fetched_at": fetched_times[0] if fetched_times else "",
        "last_bar": last_bars[0] if last_bars else "",
    }


def stock_feed(config: dict[str, Any]) -> str:
    if str(config.get("provider", "demo")).lower() != "alpaca":
        return "sample"
    return str(config.get("alpaca", {}).get("feed", "iex")).lower()


def build_data_health(symbol: str = "AAPL", config: dict[str, Any] | None = None) -> dict[str, Any]:
    active_config = deepcopy(config) if config is not None else load_config()
    provider = str(active_config.get("provider", "demo")).lower()
    credentials = credential_status()
    stock = {
        "ok": False,
        "symbol": symbol,
        "provider": provider,
        "feed": stock_feed(active_config),
        "timeframe": "1Day",
        "bars": 0,
        "latest_close": None,
        "latest_time": "",
        "error": "",
    }
    try:
        bars = fetch_bars(symbol, active_config)
        latest = bars[-1]
        stock.update(
            {
                "ok": True,
                "bars": len(bars),
                "latest_close": latest["close"],
                "latest_time": latest["time"],
                "data_status": bar_data_status(symbol, active_config),
            }
        )
    except Exception as exc:
        stock["error"] = str(exc)

    fear = active_config.get("fear", {})
    vix_source = str(fear.get("source", "cboe")).lower()
    vix: dict[str, Any] = {
        "ok": False,
        "source": vix_source,
        "fallback": False,
        "value": None,
        "label": "",
        "level": "",
        "latest_time": "",
        "freshness_label": "",
        "data_note": "",
        "error": "",
    }
    try:
        if vix_source == "off":
            vix.update({"ok": True, "label": "꺼짐", "level": "정상", "data_note": "VIX 필터 꺼짐"})
        else:
            vix_history = fetch_vix_history(active_config)
            vix_state = build_vix_state(vix_history, active_config)
            if not vix_state:
                raise RuntimeError("VIX 값 없음")
            vix.update({"ok": True, **vix_state})
    except Exception as exc:
        vix["error"] = str(exc)

    if stock["ok"] and stock.get("data_status", {}).get("stale"):
        health_level = "warning"
    elif stock["ok"] and vix["ok"] and not vix.get("fallback"):
        health_level = "ok"
    elif stock["ok"] or vix["ok"]:
        health_level = "warning"
    else:
        health_level = "error"

    return {
        "ok": health_level != "error",
        "health_level": health_level,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "credentials": credentials,
        "stock": stock,
        "vix": vix,
        "usage": market_data_usage_snapshot(),
    }


def query_value(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    if not values:
        return default
    return values[0] or default


def query_int(query: dict[str, list[str]], key: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(float(query_value(query, key, str(default))))
    except ValueError:
        value = default
    return min(maximum, max(minimum, value))


def install_info(server_address: tuple[Any, ...]) -> dict[str, Any]:
    host = str(server_address[0])
    port = int(server_address[1])
    local_urls = [f"http://{ip}:{port}/" for ip in local_ipv4_addresses()]
    phone_ready = host in {"0.0.0.0", "::"} or (host not in {"127.0.0.1", "localhost"} and not host.startswith("127."))
    return {
        "listening_host": host,
        "port": port,
        "localhost_url": f"http://127.0.0.1:{port}/",
        "local_urls": local_urls,
        "phone_ready": phone_ready and bool(local_urls),
    }


def local_ipv4_addresses() -> list[str]:
    addresses: list[str] = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            addresses.append(probe.getsockname()[0])
    except OSError:
        pass
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            addresses.append(info[4][0])
    except OSError:
        pass
    unique: list[str] = []
    for address in addresses:
        if address.startswith("127.") or address.startswith("169.254.") or address in unique:
            continue
        unique.append(address)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PulseEdge web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), StockSignalHandler)
    print(f"PulseEdge running at http://{args.host}:{args.port}")
    if args.host in {"0.0.0.0", "::"}:
        for url in install_info(server.server_address)["local_urls"]:
            print(f"Phone URL on same Wi-Fi: {url}")
    elif args.host.startswith("127.") or args.host == "localhost":
        print("For phone access, restart with --host 0.0.0.0 and open the PC Wi-Fi IP address.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
