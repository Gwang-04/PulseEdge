# PulseEdge Feature Specification

## 1. Product Direction

PulseEdge is a mobile-first US stock signal app for short swing trades and multi-month position monitoring.

The app does not place trades in version 1. It watches selected tickers, analyzes price/volume/indicator changes, and sends configurable alerts that help the user review risk, opportunity, and existing positions.

## 2. Target User

- A retail investor watching US stocks and ETFs.
- Main holding period: several days to several months.
- Wants alerts for technical changes without staring at charts all day.
- Wants position-aware alerts based on average entry price and current profit/loss.

## 3. MVP Goals

- Track a user-defined watchlist.
- Track held positions separately from unowned watchlist tickers.
- Keep the user-facing app minimal: `Home`, `Watch`, `Hold`, `Signals`, and `Settings`.
- Show unowned tickers with no active setup as `대기` instead of `정상`.
- Interpret unowned tickers from a buy-candidate perspective and held tickers from a risk-management perspective.
- Score every ticker from 0-100: `진입점수` for unowned tickers and `관리강도` for held tickers.
- Use 50 as the neutral `진입점수` baseline. Positive confirmation pushes the score toward 100, while overheated, breakdown, or market-risk conditions push it toward 0.
- Use careful entry-score language: `관찰`, `반등체크`, `자리검토`, and `진입검토` instead of implying that a candidate is an automatic buy.
- For held tickers, let stable trend, wide stop buffer, and cloud-above conditions reduce `관리강도` below 50 so calm holdings can land in the 30-49 range.
- Add non-alert score context for normal indicator states: RSI bands, volume ratio bands, moving-average trend, moving-average distance, Bollinger band position, and Ichimoku cloud position.
- Detect automatic support/resistance from recent pivot highs/lows plus 60/120-day highs/lows for unowned tickers.
- For held tickers, calculate support/resistance from the entry date forward and include post-entry high/low, entry-day high/low, and average entry as anchored position levels.
- Let the Watch view filter by buy review, rebound check, interest, caution, or hiding waiting tickers, and sort by score, support proximity, resistance proximity, RSI, volume, daily move, or symbol.
- Treat an Ichimoku cloud recovery by itself as a rebound candidate. Upgrade it to an opportunity only when RSI is in a healthy recovery zone, volume confirms the move, and the price is not overextended from moving averages.
- Keep signal backtesting as an internal validation tool and report artifact, not a main user-facing app tab.
- Use the 90-trading-day hold rule as the default backtest baseline: enter at the next trading day's open and hold for 90 trading days without interim profit taking or stop exits.
- Keep the growth backtest rule available for comparison: enter at the next trading day's open, stop at -8%, take 25% profit at +15%, take another 25% at +25%, trail the remaining position by -10% from the post-entry high, and close any remaining position after 90 trading days.
- Keep the balanced backtest rule available for comparison: -7% stop, +12%/+20% partial profit taking, -8% trailing stop, and 60 trading-day max hold.
- Calculate daily technical signals.
- Show a mobile-friendly chart view with candlesticks, moving averages, volume, RSI, and signal markers.
- Send only the alerts enabled by the user.
- Explain each alert in plain Korean.
- Show concise risk/disclaimer copy: PulseEdge is an investment-support analysis tool, not a guarantee, order instruction, or personalized investment advisory service.
- Keep a collapsible Settings risk notice covering loss risk, signal limits, no personalized advisory, no order execution, alert delay/missing-alert risk, and user final-check responsibility.
- Require one-time first-run risk acknowledgement, stored locally with a consent version and timestamp.
- Avoid automatic trading until signals are backtested and observed.

## 4. Non-Goals For MVP

- No live order placement.
- No margin, options, futures, or short-selling workflows.
- No high-frequency or scalping workflow.
- No public social/community features.
- No full fundamental valuation model in version 1.
- No app-store release until the PWA is useful and stable.

## 5. Data Sources

### Primary MVP Source

- Alpaca Basic, using the free equities feed.
- Default timeframe: daily bars.
- Default feed: `iex`.

### Data Source Constraints

- Free data is suitable for app testing and daily/swing monitoring.
- It should not be treated as complete institutional-grade real-time market coverage.
- The app should show a visible data-source label so the user knows whether analysis is based on demo data, IEX data, delayed SIP, or a future paid feed.
- IEX mode should be labeled as a single-exchange feed that may differ from full US market trades and volume.
- Delayed SIP mode should be labeled as roughly 15-minute delayed consolidated data.
- VIX can use FRED `VIXCLS` daily close data without a separate API key, with demo fallback when offline. Label this clearly as daily close data, not intraday real-time VIX.

### Future Sources

- Earnings calendar: Alpha Vantage, Finnhub, or another earnings-calendar provider.
- SEC EDGAR: official filing and XBRL facts for deeper post-earnings analysis.

## 6. Core Screens

### 6.1 Home

Purpose: show the most important items today.

Content:

- Market regime card for `SPY` and `QQQ`.
- VIX fear index level and 5-day volatility change.
- Top 3 stocks to review today, ranked from the Watch buy-candidate view.
- Compact alert digest for immediate and summary alerts, grouped by position, market, and watchlist.
- Notification permission state in the header, with clear enabled, blocked, unsupported, and not-yet-enabled states.
- Position risk summary.
- Opportunity candidates.
- Daily summary after US market close.

### 6.2 Watchlist

Purpose: monitor unowned or candidate stocks.

Held tickers should remain visible here in the all-watchlist view because a holding is still part of the user's watchlist. In Watchlist, analyze held tickers as if they are unowned so the card shows the normal buy-candidate view. Use the real position-aware management view only in Positions/Hold.

Each ticker card shows:

- Ticker
- Optional "Watch basis" marker when the ticker is also held
- Last price
- Buy score
- 1D, 5D, 20D return
- RSI 14
- Volume ratio
- Alert level
- Latest 1-4 signals
- No inline chart; tap the ticker to open the full detail chart.

Watchlist editing:

- Add one or more tickers directly from the Watch screen.
- Quick-added tickers save and re-run analysis immediately.
- Non-position watch tickers can be removed from the Watch card.
- SPY/QQQ stay protected as market filter tickers.
- Held tickers must be unmarked in Hold/Settings before quick removal.

### 6.3 Positions

Purpose: monitor holdings with average entry price.

Each position card shows:

- Ticker
- Holding status
- Management score
- Average entry price
- Quantity, optional
- Entry date, optional
- Current price
- Profit/loss percent
- Profit/loss amount, if quantity is entered
- Highest close since entry
- Drawdown from post-entry high
- Position alert level
- Suggested review action
- No inline chart; tap the ticker to open the full detail chart.

### 6.4 Chart

Purpose: inspect one ticker in detail.

Chart requirements:

- TradingView Advanced Chart widget as the default detail chart
- Ticker detail sheet with larger chart
- Daily, weekly, and other supported intervals through the TradingView toolbar
- Range selection, zoom, pan, indicators, and drawing tools through the TradingView widget
- RSI, moving averages, Bollinger Bands, and Ichimoku Cloud available from the widget indicator menu
- TradingView attribution must remain visible
- PulseEdge scores, support/resistance, holdings, and signal reasons remain separate panels below the chart
- TradingView widget data is display-only and must not be read back for PulseEdge score calculations
- Existing PulseEdge canvas chart remains as a fallback when the external widget cannot load
- Dark mode first
- Pinch/scroll friendly on mobile

### 6.5 Signals

Purpose: review alert history.

Content:

- Today
- Last 7 days
- Filter by ticker
- Filter by alert category
- Filter by alert level
- Show whether an alert was pushed or only recorded silently

### 6.6 Backtest

Purpose: check whether the score rules are useful before trusting alerts.

Content:

- Ticker selector from the current watchlist.
- Minimum buy score threshold.
- Lookback period selector.
- Cooldown setting so repeated signals during one setup are not over-counted.
- Rule preset selector for growth versus balanced exits.
- Summary of signal count, rule win rate, average rule return, average maximum drawdown, and stop count.
- Recent historical signal rows with rule return, exit reason, maximum drawdown, and fixed 20/60 trading-day comparison returns.
- Version 1 backtest is based on individual ticker technical scores; full historical SPY/QQQ/VIX regime replay can be added later.

### 6.7 Settings

Purpose: control data, alerts, and app behavior.

Settings groups:

- Data provider
- Data server status and connection test for Alpaca stock bars and FRED VIX
- Minimal data-status banner for missing API keys, analysis failure, partial ticker failure, and VIX fallback/staleness
- Default chart timeframe and range
- Collapsible score guide for Watch entry score and Hold management intensity
- Watchlist
- Positions
- Alert categories
- Alert delivery mode
- Quiet hours
- Daily summary time
- Theme

## 7. Ticker Model

Each ticker should support:

```json
{
  "symbol": "NVDA",
  "watching": true,
  "held": true,
  "average_entry_price": 125.5,
  "quantity": 10,
  "entry_date": "2026-08-01",
  "target_return_pct": 15,
  "stop_loss_pct": -7,
  "trailing_stop_pct": -8,
  "holding_style": "swing",
  "notes": "Bought for AI momentum after pullback near 60-day MA."
}
```

## 8. Signal Categories

### 8.1 RSI Signals

- `RSI_OVERSOLD`: RSI 14 <= 30.
- `RSI_DEEP_OVERSOLD`: RSI 14 <= 25.
- `RSI_RECOVERY`: RSI was below 30 and recovered to 35 or higher.
- `RSI_OVERHEATED`: RSI 14 >= 70.
- `RSI_OVERHEAT_COOLING`: RSI was above 70 and fell below 70.

Default push behavior:

- Watchlist: record or daily summary.
- Positions: push if combined with loss, trend break, or profit-protection condition.

### 8.2 Volume Signals

- `VOLUME_SPIKE`: current volume >= 2.0x 20-day average volume.
- `VOLUME_SPIKE_LARGE_CAP`: current volume >= 1.5x 20-day average volume for ETFs/large caps.
- `BULLISH_VOLUME_SPIKE`: green day plus volume spike.
- `BEARISH_VOLUME_SPIKE`: red day plus volume spike.

Default push behavior:

- Push `BEARISH_VOLUME_SPIKE` for held positions.
- Push `BULLISH_VOLUME_SPIKE` only when paired with breakout or recovery.

### 8.3 Moving Average Signals

Default moving averages:

- 20-day MA: short-term trend.
- 60-day MA: swing trend.
- 120-day MA: larger trend.

Signals:

- `MA20_BREAKDOWN`
- `MA60_BREAKDOWN`
- `MA120_BREAKDOWN`
- `MA20_RECOVERY`
- `MA60_RECOVERY`
- `MA120_RECOVERY`

Default push behavior:

- Push MA60 and MA120 breakdowns for held positions.
- Push MA20 breakdown for held positions if profit is being protected.
- Watchlist recoveries can be daily-summary items unless paired with RSI recovery or volume.

### 8.4 Moving Average Distance Signals

Signals:

- `MA20_OVERSOLD_DISTANCE`: price <= 7% below 20-day MA.
- `MA60_OVERSOLD_DISTANCE`: price <= 12% below 60-day MA.
- `MA120_OVERSOLD_DISTANCE`: price <= 20% below 120-day MA.
- `MA20_OVEREXTENDED`: price >= 12% above 20-day MA.
- `MA60_OVEREXTENDED`: price >= 20% above 60-day MA.

Default push behavior:

- Record by default.
- Push only when held and combined with profit protection or deep loss.

### 8.5 Cross Signals

- `GOLDEN_CROSS_20_60`: 20-day MA crosses above 60-day MA.
- `DEAD_CROSS_20_60`: 20-day MA crosses below 60-day MA.
- Future: 60/120 cross.

Default push behavior:

- Push `DEAD_CROSS_20_60` for held positions.
- Record `GOLDEN_CROSS_20_60` unless paired with price strength.

### 8.6 Breakout And Breakdown Signals

- `HIGH_60_BREAKOUT`: close breaks above 60-day high.
- `LOW_60_BREAKDOWN`: close breaks below 60-day low.
- `HIGH_120_BREAKOUT`: close breaks above 120-day high.
- `LOW_120_BREAKDOWN`: close breaks below 120-day low.
- `VOLUME_CONFIRMED_BREAKOUT`: 60-day high breakout plus volume >= 1.5x average.

Default push behavior:

- Push volume-confirmed breakouts.
- Push 60/120-day breakdowns for held positions.

### 8.7 Gap Signals

- `GAP_UP`: open >= 3% above previous close.
- `GAP_DOWN`: open <= 3% below previous close.
- `GAP_DOWN_VOLUME_SPIKE`: gap down plus elevated volume.

Default push behavior:

- Push gap-down signals for held positions.
- Record gap-up signals unless paired with breakout.

### 8.8 Market Regime Signals

Market proxies:

- `SPY`
- `QQQ`

Signals:

- `SPY_BELOW_MA120`
- `QQQ_BELOW_MA120`
- `MARKET_RISK_ON`: SPY and QQQ above 120-day MA.
- `MARKET_RISK_OFF`: SPY and QQQ below 120-day MA.

Behavior:

- If `SPY` is below MA120, lower bullish signal scores.
- If `QQQ` is below MA120, lower bullish signal scores for growth and technology tickers.
- If both are below MA120, watchlist buy-style alerts should become lower-priority review items.

## 9. Position-Aware Sell And Risk Signals

These only apply when `held = true`.

### 9.1 Loss Control

- `LOSS_WARNING`: price is 5% below average entry.
- `STOP_BUFFER_WARNING`: price is within 6% above the configured stop price.
- `STOP_BUFFER_REVIEW`: price is within 3% above the configured stop price.
- `STOP_REVIEW`: price is 7% below average entry.
- `RISK_EXIT_REVIEW`: price is 10% below average entry and below MA60.
- Position cards and detail views show three separate guardrails: `방어선` for the nearest active structure line, `위험선` for the configured stop price, and `수익보호` for the trailing stop when profitable.
- If a recent position structure line has already broken, the `방어선` slot should prioritize the broken line and show it as an exited line before showing the next lower support.

### 9.2 Trend Exit

- `POSITION_MA20_BREAKDOWN`: held ticker closes below MA20.
- `POSITION_MA60_BREAKDOWN`: held ticker closes below MA60.
- `POSITION_MA120_BREAKDOWN`: held ticker closes below MA120.

### 9.3 Profit Protection

- `PROFIT_10`: position reaches +10%.
- `PROFIT_20`: position reaches +20%.
- `PROFIT_30`: position reaches +30%.
- Profit bands are exclusive for held positions. Apply only the highest reached band so +30% does not also stack +10% and +20%.
- `TRAILING_STOP_WARNING`: price falls 7% from highest close since entry.
- `TRAILING_STOP_REVIEW`: price falls 10% from highest close since entry.
- `TRAILING_BUFFER_WARNING`: profitable position is within 3% above the trailing stop price.
- `RSI_OVERHEAT_COOLING_HELD`: RSI was above 70 and falls below 70 while position is profitable.

### 9.4 Suggested Review Labels

The app should avoid saying "sell now."

Use labels:

- `수익관리`
- `수익보호검토`
- `비중점검`
- `방어검토`
- `위험축소검토`

## 10. Earnings Features

### MVP Scope

Earnings should be included as a planned feature and light workflow, not full deep analysis.

MVP can support manual earnings dates:

- User can enter next earnings date.
- Alert 7 days before earnings.
- Alert 1 day before earnings.
- Alert on earnings date.
- Alert the trading day after earnings.

Post-earnings technical check:

- Gap up/down
- Volume spike
- Close above or below 20/60/120-day MA
- Position P/L impact

### Version 2 Scope

Add earnings API integration:

- Upcoming earnings date
- EPS actual vs estimate
- Revenue actual vs estimate
- Earnings surprise
- Post-earnings 1D, 5D, 20D reaction
- Guidance notes, if a reliable source is available

## 11. Alert Levels

### Unowned Watchlist Levels

These labels are used when the user does not hold the ticker.

- `대기`: no active buy setup.
- `관심`: early observation setup.
- `공포관심`: panic/pullback candidate, such as low RSI with bearish high volume or a deep moving-average distance.
- `반등후보`: rebound signs appeared, but the user should still check whether the rebound holds.
- `기회후보`: stronger entry-review setup.
- `돌파후보`: breakout setup.

### Held Position Levels

These labels are used when the user holds the ticker.

- `보유점검`: no urgent action, keep checking.
- `수익관리`: profitable or improving position that may need profit management.
- `주의`: position risk is rising.
- `수익보호검토`: profit protection review.
- `방어검토`: defense/reduce review, without saying to sell immediately.
- `위험`: high-priority risk management.

### Normal

No meaningful signal.

### Interest

Korean label: `관심`

Examples:

- RSI oversold.
- Volume increase.
- Price near key moving average.

### Caution

Korean label: `주의`

Examples:

- MA20/MA60 breakdown.
- Overextended price.
- Gap event.

### Risk

Korean label: `위험`

Examples:

- MA120 breakdown.
- 60/120-day low breakdown.
- Bearish volume spike.
- Held position near or beyond stop review.

### Opportunity Candidate

Korean label: `기회후보`

Examples:

- RSI recovery above 35.
- MA20 or MA60 recovery.
- Price remains above MA120.
- Volume confirms recovery.

### Breakout Candidate

Korean label: `돌파후보`

Examples:

- 60-day high breakout.
- Volume >= 1.5x average.
- Market regime is not risk-off.

## 12. Alert Settings

Every signal category must be user-selectable.

Settings should include:

- Enable/disable whole category.
- Enable/disable individual signal.
- Delivery mode per category:
  - Push immediately
  - Daily summary
  - App log only
  - Off
- Held positions can override watchlist rules.
- Same ticker and same signal should not push more than once per trading day.
- Signal identity is `scope + ticker + signal type + trading date`, where scope is watch, held position, or market.
- First analysis after opening the app can write the log, but should not trigger browser/mobile push.
- Held-position risk/profit signals should be processed before market signals, then watchlist entry signals.
- User can mute a ticker for 1 day, 3 days, 1 week, or until manually unmuted.

Default settings:

- Push held-position risk signals.
- Push high-priority held-position profit-protection signals, such as +30% profit, trailing review, and RSI overheated cooling while held.
- Push major market danger only: risk-off, VIX fear, and VIX panic.
- Use daily summary for watchlist entry signals, simple moving-average breakdowns, volume spikes, VIX spikes, and +20% profit.
- Keep normal market state and weak context-only signals as app log only.
- App log only for simple RSI oversold unless held.

## 13. Analysis Copy Style

Alert text should be short and actionable without pretending to be financial advice.

Good examples:

- `NVDA 보유 중. 현재 +14.2%. RSI가 74에서 68로 내려왔고, 고점 대비 -6.1%입니다. 수익 보호 구간입니다.`
- `TSLA 보유 중. 현재 -7.8%. 종가가 60일선 아래이고 거래량이 평균의 2.4배입니다. 방어/비중점검 신호입니다.`
- `AAPL 관심종목. RSI가 30 아래였고 오늘 35를 회복했습니다. 120일선 위라 기회후보로 분류합니다.`

Avoid:

- `무조건 매수`
- `무조건 매도`
- `확정 수익`
- `안전한 종목`

## 14. Design Direction

### Brand

- App name: PulseEdge.
- Tone: sharp, calm, modern, signal-focused.
- Korean UI first, with English ticker/signal identifiers available in detail views.

### Visual Style

- Mobile-first dark mode.
- Dense but readable trading-app layout.
- Candlestick-first chart experience.
- Clear color coding:
  - Green/teal for constructive signals.
  - Yellow/amber for caution.
  - Red for risk.
  - Blue for neutral information.
- Avoid decorative dashboards that make the app feel like a landing page.

### Navigation

Bottom tabs:

- Home
- Watchlist
- Positions
- Signals
- Settings

Chart can open from Watchlist or Positions as a detail screen.
Backtests remain available as an internal API/tooling path, not as a primary bottom tab.
Signals is the user's compact signal history. It should stay minimal and support quick filtering by all, immediate alerts, buy-style signals, held-position signals, market signals, and risk signals.

## 15. PWA Requirements

- Installable to phone home screen.
- Responsive mobile layout.
- Local settings persistence.
- Offline shell screen.
- 192/512px PNG icons plus iOS apple-touch-icon.
- Settings install panel with current app status and local phone test URL when available.
- Browser notifications where supported.
- Later migration path to Expo React Native.

## 16. Technical Roadmap

### Phase 1: PWA Foundation

- Convert current prototype into a mobile-first PWA.
- Add bottom navigation.
- Add dark theme.
- Add candlestick chart with indicators.
- Add local storage for settings, watchlist, and positions.

### Phase 2: Signal Engine

- Implement full signal set.
- Add alert-level scoring.
- Add market-regime filter.
- Add VIX fear index filter.
- Add position-aware sell/risk signals.
- Add alert settings.

### Phase 3: Real Data

- User-facing API-key fields are removed, and public API credential mutations are blocked.
- Improve Alpaca integration.
- Keep market-data API keys server-side for public release; users should not enter Alpaca API keys.
- Add operator-only API-key setup UX.
- Add connection test before switching from demo to real data.
- Cache historical bars.
- Handle API errors clearly.
- Add market calendar awareness.

### Phase 3.5: Account Model

- Login is optional for the first local/free PWA test.
- Add login before cloud sync, cross-device watchlists, durable push alerts, paid subscriptions, or account-level signal history.
- Support a guest/local mode if possible so basic app value is visible before sign-up.
- If account creation exists, include in-app account deletion, data deletion flow, and a clear privacy policy.

### Phase 4: Earnings

- Manual earnings dates first.
- Add earnings reminders.
- Add post-earnings technical review.
- Evaluate earnings calendar provider.

### Phase 5: Signal Quality

- Store signal history.
- Measure 1D, 5D, 20D forward returns after each signal.
- Show which signals are useful and which are noisy.
- Add simple backtest reports for score thresholds and signal combinations.

## 17. Success Criteria

The first useful version is successful when:

- User can manage watchlist and positions on mobile.
- User can add and remove tickers without editing raw config files.
- User can see clear signal status per ticker.
- User can open a ticker detail view with a larger chart and signal reasoning.
- User can enable only the alerts they care about.
- Held positions generate risk/profit-protection alerts.
- Charts are readable enough to inspect trend, RSI, volume, signal points, weekly trend, and zoomed price action.
- The app helps avoid impulsive trades rather than encouraging more trades.
