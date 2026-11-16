from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from market_data import fetch_bars
from settings import load_config, normalize_symbols
from signal_engine import analyze_symbol


DEFAULT_SYMBOLS = "AAPL,MSFT,PLTR,SPY,QQQ"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PulseEdge daily indicator inputs and outputs.")
    parser.add_argument("--symbols", default=DEFAULT_SYMBOLS, help="Comma-separated US stock symbols.")
    parser.add_argument("--provider", choices=("demo", "alpaca"), default="alpaca")
    args = parser.parse_args()

    symbols = normalize_symbols(args.symbols.split(","))
    config = load_config()
    config["provider"] = args.provider
    config["positions"] = []

    rows: list[dict] = []
    for symbol in symbols:
        bars = fetch_bars(symbol, config)
        result = analyze_symbol(symbol, bars, config)
        support = result["support_resistance"].get("nearest_support") or {}
        resistance = result["support_resistance"].get("nearest_resistance") or {}
        rows.append(
            {
                "symbol": symbol,
                "date": str(result["last_bar"])[:10],
                "price": result["price"],
                "rsi": result["rsi14"],
                "d20": result["ma_distance_pct"]["20"],
                "d60": result["ma_distance_pct"]["60"],
                "d120": result["ma_distance_pct"]["120"],
                "s1": support.get("price"),
                "s1_pct": support.get("distance_pct"),
                "r1": resistance.get("price"),
                "r1_pct": resistance.get("distance_pct"),
            }
        )

    print("| Symbol | Date | Close | RSI14 | vs SMA20 | vs SMA60 | vs SMA120 | S1 | S1 gap | R1 | R1 gap |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        print(
            f"| {row['symbol']} | {row['date']} | {money(row['price'])} | {number(row['rsi'])} | "
            f"{percent(row['d20'])} | {percent(row['d60'])} | {percent(row['d120'])} | "
            f"{money(row['s1'])} | {percent(row['s1_pct'])} | {money(row['r1'])} | {percent(row['r1_pct'])} |"
        )
    return 0


def number(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def money(value: float | None) -> str:
    return "-" if value is None else f"${value:.2f}"


def percent(value: float | None) -> str:
    return "-" if value is None else f"{value:+.2f}%"


if __name__ == "__main__":
    raise SystemExit(main())
