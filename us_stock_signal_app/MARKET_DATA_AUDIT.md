# PulseEdge Market Data Audit

Date: 2026-09-22

## Fixed calculation contract

- Source: Alpaca historical daily bars, IEX feed, private/local mode only.
- Price adjustment: stock splits (`adjustment=split`).
- Candle policy: only completed US market daily bars; the current session is ignored until 16:15 ET.
- RSI: Wilder RSI, period 14.
- Moving averages: simple moving averages of the latest 20, 60, and 120 completed closes.
- MA distance: `(close / SMA - 1) * 100`.
- Support/resistance: clustered pivots from the latest 180 completed bars plus 60/120-day extremes.
- Failure policy: use the last successful in-memory bars for up to 24 hours when a temporary provider/network error occurs.
- Freshness display: every analyzed symbol exposes its last completed bar, fetch time, and cache state. Fresh server-cache hits stay quiet; stale fallback data produces a visible warning with affected symbols.
- VIX: CBOE's official daily close CSV is primary. FRED VIXCLS is the automatic fallback, and demo VIX is used only when both official sources fail.
- Distribution note: the public CBOE history page offers the daily file for site visitors, but commercial app redistribution rights must be confirmed separately before public release.

## 2026-09-21 close snapshot

| Symbol | Close | RSI14 | vs SMA20 | vs SMA60 | vs SMA120 | S1 gap | R1 gap |
|---|---:|---:|---:|---:|---:|---:|---:|
| AAPL | $339.00 | 66.19 | +4.59% | +6.75% | +12.42% | -1.48% | +1.64% |
| MSFT | $501.64 | 57.07 | +0.65% | +10.79% | +16.87% | -3.36% | +2.86% |
| PLTR | $183.08 | 61.16 | +4.00% | +19.09% | +25.67% | -0.79% | +2.77% |
| SPY | $773.52 | 58.48 | +1.16% | +2.09% | +4.48% | -2.38% | +0.56% |
| QQQ | $741.41 | 65.65 | +3.74% | +4.16% | +6.20% | -2.05% | +0.47% |

This snapshot was refreshed after split adjustment and completed-candle filtering were enabled. The values did not change because no relevant split occurred in the active indicator windows.

Re-run the audit command below whenever the data contract changes.

```powershell
C:\Users\dlrhk\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\audit_market_data.py
```

## TradingView comparison rule

Compare the same symbol, exchange, daily timeframe, regular session, completed candle date, and split-adjustment setting. IEX and TradingView may still differ slightly because their underlying trade feeds are not identical. Large differences indicate a mismatched candle date, exchange/feed, session, or adjustment setting rather than an RSI formula problem.

### Manual parity check

On 2026-09-22, the AAPL daily chart was checked visually against the embedded TradingView widget for the completed 2026-09-21 candle:

| Source | Close | RSI14 |
|---|---:|---:|
| PulseEdge / Alpaca IEX | $339.00 | 66.19 |
| TradingView widget | about $338.98 | 66.32 |

The differences were $0.02 for close and 0.13 RSI points. This is within the expected small feed-level variation and does not indicate a formula mismatch.
