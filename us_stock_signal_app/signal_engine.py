from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from statistics import mean
from typing import Any

from settings import DEFAULT_ALERT_PREFERENCES

LARGE_CAP_OR_ETF = {
    "AAPL",
    "AMZN",
    "GOOGL",
    "GOOG",
    "META",
    "MSFT",
    "NVDA",
    "QQQ",
    "SPY",
    "TSLA",
}

LEVEL_RANK = {
    "대기": 0,
    "정상": 0,
    "관심": 1,
    "공포관심": 2,
    "반등후보": 3,
    "기회후보": 4,
    "돌파후보": 4,
    "주의": 5,
    "수익관리": 5,
    "수익보호검토": 6,
    "방어검토": 6,
    "위험": 7,
}

BUY_SCORE_POINTS = {
    "RSI_OVERSOLD": 8,
    "RSI_DEEP_OVERSOLD": 12,
    "RSI_RECOVERY": 18,
    "RSI_OVERHEATED": -18,
    "RSI_OVERHEAT_COOLING": -14,
    "VOLUME_SPIKE": 3,
    "VOLUME_SPIKE_LARGE_CAP": 2,
    "BULLISH_VOLUME_SPIKE": 14,
    "BEARISH_VOLUME_SPIKE": 8,
    "MA20_BREAKDOWN": 2,
    "MA60_BREAKDOWN": 4,
    "MA120_BREAKDOWN": -18,
    "MA20_RECOVERY": 12,
    "MA60_RECOVERY": 15,
    "MA120_RECOVERY": 12,
    "MA20_OVERSOLD_DISTANCE": 7,
    "MA60_OVERSOLD_DISTANCE": 10,
    "MA120_OVERSOLD_DISTANCE": 12,
    "MA20_OVEREXTENDED": -16,
    "MA60_OVEREXTENDED": -20,
    "GOLDEN_CROSS_20_60": 16,
    "DEAD_CROSS_20_60": -18,
    "HIGH_60_BREAKOUT": 15,
    "HIGH_120_BREAKOUT": 12,
    "LOW_60_BREAKDOWN": -16,
    "LOW_120_BREAKDOWN": -20,
    "VOLUME_CONFIRMED_BREAKOUT": 20,
    "GAP_UP": -12,
    "GAP_DOWN": 5,
    "GAP_DOWN_VOLUME_SPIKE": 10,
    "BOLLINGER_LOWER_TOUCH": 10,
    "BOLLINGER_LOWER_RECOVERY": 15,
    "ICHIMOKU_CLOUD_RECOVERY": 12,
    "ICHIMOKU_CLOUD_BREAKDOWN": -18,
    "MARKET_FILTER_DOWNGRADE": -20,
}

POSITION_SCORE_POINTS = {
    "RSI_OVERSOLD": 10,
    "RSI_DEEP_OVERSOLD": 16,
    "RSI_RECOVERY": 8,
    "RSI_OVERHEATED": 6,
    "RSI_OVERHEAT_COOLING": 12,
    "VOLUME_SPIKE": 8,
    "BULLISH_VOLUME_SPIKE": 10,
    "BEARISH_VOLUME_SPIKE": 26,
    "MA20_BREAKDOWN": 12,
    "MA60_BREAKDOWN": 22,
    "MA120_BREAKDOWN": 32,
    "MA20_RECOVERY": 6,
    "MA60_RECOVERY": 8,
    "MA120_RECOVERY": 10,
    "MA20_OVERSOLD_DISTANCE": 12,
    "MA60_OVERSOLD_DISTANCE": 22,
    "MA120_OVERSOLD_DISTANCE": 30,
    "MA20_OVEREXTENDED": 10,
    "MA60_OVEREXTENDED": 14,
    "GOLDEN_CROSS_20_60": 8,
    "DEAD_CROSS_20_60": 24,
    "LOW_60_BREAKDOWN": 28,
    "LOW_120_BREAKDOWN": 34,
    "GAP_DOWN": 16,
    "GAP_DOWN_VOLUME_SPIKE": 28,
    "LOSS_WARNING": 18,
    "STOP_REVIEW": 32,
    "RISK_EXIT_REVIEW": 42,
    "STOP_BUFFER_WARNING": 18,
    "STOP_BUFFER_REVIEW": 26,
    "POSITION_SUPPORT_BUFFER_WARNING": 14,
    "POSITION_SUPPORT_BREAKDOWN": 26,
    "POSITION_SUPPORT_VOLUME_BREAKDOWN": 34,
    "POSITION_MA60_CONFIRM_BREAKDOWN": 30,
    "POSITION_STRUCTURE_EXIT_REVIEW": 44,
    "POSITION_MA20_BREAKDOWN": 12,
    "POSITION_MA60_BREAKDOWN": 24,
    "POSITION_MA120_BREAKDOWN": 34,
    "PROFIT_10": 3,
    "PROFIT_20": 5,
    "PROFIT_30": 8,
    "TRAILING_STOP_WARNING": 12,
    "TRAILING_STOP_REVIEW": 20,
    "TRAILING_BUFFER_WARNING": 8,
    "RSI_OVERHEAT_COOLING_HELD": 14,
    "BOLLINGER_LOWER_TOUCH": 12,
    "BOLLINGER_LOWER_RECOVERY": 6,
    "ICHIMOKU_CLOUD_RECOVERY": 8,
    "ICHIMOKU_CLOUD_BREAKDOWN": 24,
    "EARNINGS_7D": 8,
    "EARNINGS_1D": 14,
    "EARNINGS_TODAY": 22,
    "EARNINGS_AFTER": 10,
    "VIX_POSITION_RISK": 24,
}

POSITION_ACTION_RANK = {
    "보유점검": 0,
    "수익관리": 1,
    "수익보호": 2,
    "비중조정": 3,
    "방어선확인": 4,
    "수익보호검토": 6,
    "방어검토": 7,
    "위험선근접": 8,
    "비중점검": 7,
    "구조방어검토": 9,
    "위험축소검토": 10,
    "평단입력": 99,
}

POSITION_EVENT_TYPES = {
    "EARNINGS_7D",
    "EARNINGS_1D",
    "EARNINGS_TODAY",
    "EARNINGS_AFTER",
    "VIX_POSITION_RISK",
}


def sma(values: list[float], period: int) -> list[float | None]:
    output: list[float | None] = []
    rolling_sum = 0.0
    for index, value in enumerate(values):
        rolling_sum += value
        if index >= period:
            rolling_sum -= values[index - period]
        output.append(rolling_sum / period if index >= period - 1 else None)
    return output


def rolling_std(values: list[float], period: int) -> list[float | None]:
    output: list[float | None] = []
    for index in range(len(values)):
        if index < period - 1:
            output.append(None)
            continue
        window = values[index - period + 1 : index + 1]
        average = sum(window) / period
        variance = sum((value - average) ** 2 for value in window) / period
        output.append(variance ** 0.5)
    return output


def bollinger_bands(values: list[float], period: int = 20, deviations: float = 2.0) -> dict[str, list[float | None]]:
    middle = sma(values, period)
    standard_deviation = rolling_std(values, period)
    upper: list[float | None] = []
    lower: list[float | None] = []
    for average, deviation in zip(middle, standard_deviation):
        if average is None or deviation is None:
            upper.append(None)
            lower.append(None)
            continue
        upper.append(average + deviation * deviations)
        lower.append(average - deviation * deviations)
    return {"middle": middle, "upper": upper, "lower": lower}


def range_midpoint(highs: list[float], lows: list[float], period: int) -> list[float | None]:
    output: list[float | None] = []
    for index in range(len(highs)):
        if index < period - 1:
            output.append(None)
            continue
        window_high = max(highs[index - period + 1 : index + 1])
        window_low = min(lows[index - period + 1 : index + 1])
        output.append((window_high + window_low) / 2)
    return output


def ichimoku_lines(highs: list[float], lows: list[float]) -> dict[str, list[float | None]]:
    tenkan = range_midpoint(highs, lows, 9)
    kijun = range_midpoint(highs, lows, 26)
    span_b = range_midpoint(highs, lows, 52)
    span_a: list[float | None] = []
    for tenkan_value, kijun_value in zip(tenkan, kijun):
        if tenkan_value is None or kijun_value is None:
            span_a.append(None)
        else:
            span_a.append((tenkan_value + kijun_value) / 2)
    return {
        "tenkan": tenkan,
        "kijun": kijun,
        "span_a": span_a,
        "span_b": span_b,
    }


def ema(values: list[float], period: int) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) < period:
        return output
    alpha = 2 / (period + 1)
    current = mean(values[:period])
    output[period - 1] = current
    for index in range(period, len(values)):
        current = values[index] * alpha + current * (1 - alpha)
        output[index] = current
    return output


def rsi(values: list[float], period: int = 14) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return output
    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, period + 1):
        delta = values[index] - values[index - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    output[period] = _rsi_value(avg_gain, avg_loss)
    for index in range(period + 1, len(values)):
        delta = values[index] - values[index - 1]
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        output[index] = _rsi_value(avg_gain, avg_loss)
    return output


def _rsi_value(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def crossed_below(previous_value: float | None, previous_line: float | None, current_value: float | None, current_line: float | None) -> bool:
    return previous_value is not None and previous_line is not None and current_value is not None and current_line is not None and previous_value >= previous_line and current_value < current_line


def crossed_above(previous_value: float | None, previous_line: float | None, current_value: float | None, current_line: float | None) -> bool:
    return previous_value is not None and previous_line is not None and current_value is not None and current_line is not None and previous_value <= previous_line and current_value > current_line


def low_rsi(value: float | None, alerts: dict[str, Any]) -> bool:
    return value is not None and value <= float(alerts.get("rsi_oversold", 30))


def analyze_symbol(symbol: str, bars: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    if len(bars) < 140:
        raise ValueError(f"{symbol} needs at least 140 bars")

    alerts = config["alerts"]
    position = position_for_symbol(symbol, config)
    closes = [float(bar["close"]) for bar in bars]
    opens = [float(bar["open"]) for bar in bars]
    highs = [float(bar["high"]) for bar in bars]
    lows = [float(bar["low"]) for bar in bars]
    volumes = [float(bar["volume"]) for bar in bars]
    rsi_values = rsi(closes, int(alerts.get("rsi_period", 14)))
    ma_periods = [20, 60, 120]
    sma_values = {period: sma(closes, period) for period in ma_periods}
    volume_sma = sma(volumes, int(alerts.get("volume_period", 20)))
    ema_12 = ema(closes, 12)
    ema_26 = ema(closes, 26)
    macd = [
        (fast - slow) if fast is not None and slow is not None else None
        for fast, slow in zip(ema_12, ema_26)
    ]
    macd_signal = _ema_sparse(macd, 9)
    bollinger = bollinger_bands(closes)
    ichimoku = ichimoku_lines(highs, lows)

    latest_index = len(bars) - 1
    previous_index = latest_index - 1
    latest_close = closes[latest_index]
    previous_close = closes[previous_index]
    latest_open = opens[latest_index]
    latest_rsi = rsi_values[latest_index]
    previous_rsi = rsi_values[previous_index]
    latest_volume_average = volume_sma[latest_index]
    volume_ratio = volumes[latest_index] / latest_volume_average if latest_volume_average else None
    signals: list[dict[str, Any]] = []
    held = position is not None
    support_entry_date = position.get("entry_date") if position else None
    support_average_entry = position.get("average_entry_price") if position else None
    support_resistance = support_resistance_levels(
        symbol,
        bars,
        latest_close,
        entry_date=support_entry_date,
        average_entry_price=support_average_entry,
    )

    add_rsi_signals(symbol, signals, rsi_values, alerts, held)
    add_volume_signals(symbol, signals, latest_close, previous_close, latest_rsi, volume_ratio, alerts, held)
    add_moving_average_signals(signals, closes, sma_values, latest_index, previous_index, latest_rsi, alerts, held)
    add_breakout_signals(signals, closes, highs, lows, latest_index, latest_rsi, volume_ratio, alerts, held)
    add_gap_signals(signals, latest_open, previous_close, latest_rsi, volume_ratio, alerts, held)
    add_chart_overlay_signals(symbol, signals, closes, sma_values, bollinger, ichimoku, latest_index, previous_index, latest_rsi, volume_ratio, alerts, held)
    position_metrics = add_position_signals(symbol, signals, position, bars, closes, sma_values, latest_rsi, previous_rsi, volume_ratio, support_resistance)
    add_earnings_signals(symbol, signals, position)
    apply_alert_preferences(signals, config)

    active_signals = [signal for signal in signals if signal["delivery"] != "off"]
    alert_level = rank_alert(active_signals)
    if not position_metrics and alert_level == "정상":
        alert_level = "대기"
    score_context = build_score_context(symbol, closes, sma_values, bollinger, ichimoku, support_resistance, latest_index, latest_rsi, volume_ratio, position_metrics)
    score = build_signal_score(active_signals, position_metrics, alert_level, score_context)
    indicators = attach_indicators(bars, rsi_values, sma_values, volume_sma, macd, macd_signal, bollinger, ichimoku, signals)
    ma_snapshot = {
        str(period): round(sma_values[period][latest_index], 4) if sma_values[period][latest_index] is not None else None
        for period in ma_periods
    }
    return {
        "symbol": symbol,
        "provider": config.get("provider", "demo"),
        "last_bar": bars[-1]["time"],
        "price": round(latest_close, 4),
        "change_pct_1d": round((latest_close / previous_close - 1) * 100, 2),
        "change_pct_5d": change_pct(closes, 5),
        "change_pct_20d": change_pct(closes, 20),
        "rsi14": round(latest_rsi, 2) if latest_rsi is not None else None,
        "sma": ma_snapshot,
        "ma_distance_pct": ma_distance(latest_close, ma_snapshot),
        "volume_ratio": round(volume_ratio, 2) if volume_ratio is not None else None,
        "support_resistance": support_resistance,
        "macd": round(macd[latest_index], 4) if macd[latest_index] is not None else None,
        "macd_signal": round(macd_signal[latest_index], 4) if macd_signal[latest_index] is not None else None,
        "alert_level": alert_level,
        "signals": active_signals,
        "all_signals": signals,
        "position": position_metrics,
        "score": score,
        "score_context": score_context,
        "summary": build_summary(symbol, latest_close, latest_rsi, ma_snapshot, volume_ratio, alert_level, position_metrics),
        "bars": indicators[-720:],
    }


def position_for_symbol(symbol: str, config: dict[str, Any]) -> dict[str, Any] | None:
    for position in config.get("positions", []):
        if position.get("symbol") == symbol and position.get("held"):
            return position
    return None


def add_rsi_signals(symbol: str, signals: list[dict[str, Any]], rsi_values: list[float | None], alerts: dict[str, Any], held: bool) -> None:
    latest = rsi_values[-1]
    previous = rsi_values[-2]
    if latest is None:
        return
    oversold = float(alerts.get("rsi_oversold", 30))
    deep = float(alerts.get("rsi_deep_oversold", 25))
    recovery = float(alerts.get("rsi_recovery", 35))
    overheated = float(alerts.get("rsi_overheated", 70))
    recent = [value for value in rsi_values[-8:-1] if value is not None]

    if latest <= deep:
        level = "주의" if held else "공포관심"
        message = f"{symbol} 보유종목 RSI가 {latest:.1f}로 깊은 약세입니다." if held else f"{symbol} RSI가 {latest:.1f}로 공포성 과매도 후보입니다."
        signals.append(make_signal("RSI_DEEP_OVERSOLD", level, "RSI", message, "risk" if held else "review"))
    elif latest <= oversold:
        level = "주의" if held else "관심"
        message = f"{symbol} 보유종목 RSI가 {latest:.1f}로 약세입니다." if held else f"{symbol} RSI가 {latest:.1f}로 과매도 관심 구간입니다."
        signals.append(make_signal("RSI_OVERSOLD", level, "RSI", message, "risk" if held else "review"))
    if previous is not None and previous < recovery <= latest and recent and min(recent) <= oversold:
        level = "수익관리" if held else "반등후보"
        message = f"{symbol} 보유종목 RSI가 과매도 이후 {latest:.1f}까지 회복했습니다." if held else f"{symbol} RSI가 과매도 이후 {latest:.1f}까지 회복해 반등 후보입니다."
        signals.append(make_signal("RSI_RECOVERY", level, "RSI", message, "profit" if held else "opportunity"))
    if latest >= overheated:
        level = "수익관리" if held else "주의"
        message = f"{symbol} 보유종목 RSI가 {latest:.1f}로 수익 관리 구간입니다." if held else f"{symbol} RSI가 {latest:.1f}로 추격 진입 주의 구간입니다."
        signals.append(make_signal("RSI_OVERHEATED", level, "RSI", message, "profit" if held else "risk"))
    if previous is not None and previous >= overheated > latest:
        level = "수익관리" if held else "주의"
        message = f"{symbol} 보유종목 RSI 과열이 식기 시작했습니다." if held else f"{symbol} RSI 과열이 식어 신규 진입은 신중히 봅니다."
        signals.append(make_signal("RSI_OVERHEAT_COOLING", level, "RSI", message, "profit" if held else "risk"))


def add_volume_signals(
    symbol: str,
    signals: list[dict[str, Any]],
    latest_close: float,
    previous_close: float,
    latest_rsi: float | None,
    volume_ratio: float | None,
    alerts: dict[str, Any],
    held: bool,
) -> None:
    if volume_ratio is None:
        return
    spike = float(alerts.get("volume_spike_multiple", 2.0))
    large_cap_spike = float(alerts.get("large_cap_volume_spike_multiple", 1.5))
    is_up = latest_close > previous_close
    is_down = latest_close < previous_close
    if symbol in LARGE_CAP_OR_ETF and volume_ratio >= large_cap_spike:
        level = "주의" if held and is_down else "관심"
        signals.append(make_signal("VOLUME_SPIKE_LARGE_CAP", level, "VOLUME", f"{symbol} 거래량이 20일 평균의 {volume_ratio:.1f}배입니다.", "risk" if held and is_down else "review"))
    if volume_ratio >= spike:
        level = "주의" if held and is_down else "관심"
        signals.append(make_signal("VOLUME_SPIKE", level, "VOLUME", f"{symbol} 거래량이 20일 평균의 {volume_ratio:.1f}배입니다.", "risk" if held and is_down else "review"))
        if is_up:
            level = "수익관리" if held else "기회후보"
            message = f"{symbol} 보유종목 상승에 거래량이 붙어 수익 관리 구간입니다." if held else f"{symbol} 상승일에 거래량이 강하게 붙어 진입 검토 후보입니다."
            signals.append(make_signal("BULLISH_VOLUME_SPIKE", level, "VOLUME", message, "profit" if held else "opportunity"))
        if is_down:
            if held:
                signals.append(make_signal("BEARISH_VOLUME_SPIKE", "위험", "VOLUME", f"{symbol} 보유종목 하락일에 거래량이 강하게 늘었습니다.", "risk"))
            else:
                level = "공포관심" if low_rsi(latest_rsi, alerts) else "관심"
                message = f"{symbol} 하락일 거래량이 커졌고 RSI도 낮아 공포 구간 관찰 대상입니다." if level == "공포관심" else f"{symbol} 하락일 거래량이 커져 관심 관찰 구간입니다."
                signals.append(make_signal("BEARISH_VOLUME_SPIKE", level, "VOLUME", message, "review"))


def add_moving_average_signals(
    signals: list[dict[str, Any]],
    closes: list[float],
    sma_values: dict[int, list[float | None]],
    latest_index: int,
    previous_index: int,
    latest_rsi: float | None,
    alerts: dict[str, Any],
    held: bool,
) -> None:
    latest_close = closes[latest_index]
    previous_close = closes[previous_index]
    for period in (20, 60, 120):
        current_ma = sma_values[period][latest_index]
        previous_ma = sma_values[period][previous_index]
        if crossed_below(previous_close, previous_ma, latest_close, current_ma):
            if held:
                level = "위험" if period == 120 else "방어검토" if period == 60 else "주의"
                message = f"보유 종목 종가가 {period}일선 아래로 내려와 리스크 점검 구간입니다."
            else:
                level = "주의" if period == 120 else "공포관심" if low_rsi(latest_rsi, alerts) else "관심"
                message = f"미보유 종목이 {period}일선 아래로 눌렸습니다. 반등이 유지되는지 확인할 때까지 관찰합니다."
            signals.append(make_signal(f"MA{period}_BREAKDOWN", level, "MOVING_AVERAGE", message, "risk" if held or level == "주의" else "review"))
        if crossed_above(previous_close, previous_ma, latest_close, current_ma):
            if held:
                level = "수익관리"
                message = f"보유 종목 종가가 {period}일선 위로 회복했습니다."
            else:
                level = "반등후보" if period in {20, 60} else "기회후보"
                message = f"미보유 종목 종가가 {period}일선 위로 회복해 진입 검토 후보입니다."
            signals.append(make_signal(f"MA{period}_RECOVERY", level, "MOVING_AVERAGE", message, "profit" if held else "opportunity"))

        if current_ma is None:
            continue
        distance_pct = (latest_close / current_ma - 1) * 100
        distance = alerts.get("ma_distance_pct", {})
        oversold_key = f"{period}_oversold"
        overextended_key = f"{period}_overextended"
        if oversold_key in distance and distance_pct <= float(distance[oversold_key]):
            if held:
                level = "주의" if period == 20 else "위험"
                message = f"보유 종목이 {period}일선 대비 {distance_pct:.1f}% 아래입니다."
            else:
                level = "관심" if period == 20 else "공포관심"
                message = f"미보유 종목이 {period}일선 대비 {distance_pct:.1f}% 아래라 과매도 관찰 구간입니다."
            signals.append(make_signal(f"MA{period}_OVERSOLD_DISTANCE", level, "MOVING_AVERAGE", message, "risk" if held else "review"))
        if overextended_key in distance and distance_pct >= float(distance[overextended_key]):
            level = "수익관리" if held else "주의"
            message = f"보유 종목이 {period}일선 대비 {distance_pct:.1f}% 위라 수익 관리 구간입니다." if held else f"미보유 종목이 {period}일선 대비 {distance_pct:.1f}% 위라 추격 진입 주의 구간입니다."
            signals.append(make_signal(f"MA{period}_OVEREXTENDED", level, "MOVING_AVERAGE", message, "profit" if held else "risk"))

    ma20 = sma_values[20]
    ma60 = sma_values[60]
    if crossed_above(ma20[previous_index], ma60[previous_index], ma20[latest_index], ma60[latest_index]):
        level = "수익관리" if held else "기회후보"
        message = "보유 종목 20일선이 60일선 위로 올라와 추세 회복 구간입니다." if held else "20일선이 60일선 위로 올라와 진입 검토 후보입니다."
        signals.append(make_signal("GOLDEN_CROSS_20_60", level, "MOVING_AVERAGE", message, "profit" if held else "opportunity"))
    if crossed_below(ma20[previous_index], ma60[previous_index], ma20[latest_index], ma60[latest_index]):
        level = "위험" if held else "주의"
        message = "보유 종목 20일선이 60일선 아래로 내려와 리스크 점검 구간입니다." if held else "20일선이 60일선 아래로 내려와 신규 진입은 신중히 봅니다."
        signals.append(make_signal("DEAD_CROSS_20_60", level, "MOVING_AVERAGE", message, "risk"))


def add_breakout_signals(
    signals: list[dict[str, Any]],
    closes: list[float],
    highs: list[float],
    lows: list[float],
    latest_index: int,
    latest_rsi: float | None,
    volume_ratio: float | None,
    alerts: dict[str, Any],
    held: bool,
) -> None:
    latest_close = closes[latest_index]
    for period in (60, 120):
        if latest_index < period:
            continue
        prior_high = max(highs[latest_index - period:latest_index])
        prior_low = min(lows[latest_index - period:latest_index])
        if latest_close > prior_high:
            level = "수익관리" if held else "돌파후보" if period == 60 else "기회후보"
            message = f"보유 종목이 {period}일 신고가를 종가로 돌파해 수익 관리 구간입니다." if held else f"{period}일 신고가를 종가로 돌파했습니다."
            signals.append(make_signal(f"HIGH_{period}_BREAKOUT", level, "BREAKOUT", message, "profit" if held else "opportunity"))
            if period == 60 and volume_ratio is not None and volume_ratio >= 1.5:
                level = "수익관리" if held else "돌파후보"
                signals.append(make_signal("VOLUME_CONFIRMED_BREAKOUT", level, "BREAKOUT", "60일 신고가 돌파에 거래량이 동반됐습니다.", "profit" if held else "opportunity"))
        if latest_close < prior_low:
            if held:
                signals.append(make_signal(f"LOW_{period}_BREAKDOWN", "위험", "BREAKOUT", f"보유 종목이 {period}일 신저가를 종가로 이탈했습니다.", "risk"))
            else:
                level = "공포관심" if low_rsi(latest_rsi, alerts) else "주의"
                message = f"{period}일 신저가 이탈과 낮은 RSI가 겹쳐 공포 구간 관찰 대상입니다." if level == "공포관심" else f"{period}일 신저가를 종가로 이탈해 반등이 유지되는지 확인할 때까지 대기합니다."
                signals.append(make_signal(f"LOW_{period}_BREAKDOWN", level, "BREAKOUT", message, "review" if level == "공포관심" else "risk"))


def add_gap_signals(signals: list[dict[str, Any]], latest_open: float, previous_close: float, latest_rsi: float | None, volume_ratio: float | None, alerts: dict[str, Any], held: bool) -> None:
    gap_pct = (latest_open / previous_close - 1) * 100
    threshold = float(alerts.get("gap_pct", 3.0))
    if gap_pct >= threshold:
        level = "수익관리" if held else "주의"
        message = f"보유 종목이 전일 종가 대비 {gap_pct:.1f}% 갭상승 출발했습니다." if held else f"전일 종가 대비 {gap_pct:.1f}% 갭상승 출발해 추격 진입 주의 구간입니다."
        signals.append(make_signal("GAP_UP", level, "GAP", message, "profit" if held else "review"))
    if gap_pct <= -threshold:
        if held:
            signals.append(make_signal("GAP_DOWN", "주의", "GAP", f"보유 종목이 전일 종가 대비 {gap_pct:.1f}% 갭하락 출발했습니다.", "risk"))
        else:
            level = "공포관심" if low_rsi(latest_rsi, alerts) else "관심"
            message = f"전일 종가 대비 {gap_pct:.1f}% 갭하락과 낮은 RSI가 겹친 공포 관심 구간입니다." if level == "공포관심" else f"전일 종가 대비 {gap_pct:.1f}% 갭하락 출발해 관심 관찰 구간입니다."
            signals.append(make_signal("GAP_DOWN", level, "GAP", message, "review"))
        if volume_ratio is not None and volume_ratio >= 1.5:
            level = "위험" if held else "공포관심"
            message = "보유 종목 갭하락 뒤 거래량도 평소보다 큽니다." if held else "갭하락 뒤 거래량이 커져 공포 구간 관찰 대상으로 봅니다."
            signals.append(make_signal("GAP_DOWN_VOLUME_SPIKE", level, "GAP", message, "risk" if held else "review"))


def add_chart_overlay_signals(
    symbol: str,
    signals: list[dict[str, Any]],
    closes: list[float],
    sma_values: dict[int, list[float | None]],
    bollinger: dict[str, list[float | None]],
    ichimoku: dict[str, list[float | None]],
    latest_index: int,
    previous_index: int,
    latest_rsi: float | None,
    volume_ratio: float | None,
    alerts: dict[str, Any],
    held: bool,
) -> None:
    latest_close = closes[latest_index]
    previous_close = closes[previous_index]
    lower = bollinger["lower"][latest_index]
    previous_lower = bollinger["lower"][previous_index]
    if lower is not None and latest_close <= lower:
        if held:
            signals.append(make_signal("BOLLINGER_LOWER_TOUCH", "주의", "CHART", f"{symbol} 보유종목이 볼린저밴드 하단에 닿아 약세 점검 구간입니다.", "risk"))
        else:
            level = "공포관심" if low_rsi(latest_rsi, alerts) else "관심"
            message = f"{symbol} 볼린저밴드 하단과 낮은 RSI가 겹쳐 공포 구간 관찰 대상입니다." if level == "공포관심" else f"{symbol} 볼린저밴드 하단에 닿아 과매도 관찰 구간입니다."
            signals.append(make_signal("BOLLINGER_LOWER_TOUCH", level, "CHART", message, "review"))
    if previous_lower is not None and lower is not None and previous_close < previous_lower <= latest_close:
        level = "수익관리" if held else "반등후보"
        message = f"{symbol} 보유종목이 볼린저밴드 하단 위로 복귀했습니다." if held else f"{symbol} 볼린저밴드 하단 위로 복귀해 반등 후보입니다."
        signals.append(make_signal("BOLLINGER_LOWER_RECOVERY", level, "CHART", message, "profit" if held else "opportunity"))

    span_a = ichimoku["span_a"][latest_index]
    span_b = ichimoku["span_b"][latest_index]
    previous_span_a = ichimoku["span_a"][previous_index]
    previous_span_b = ichimoku["span_b"][previous_index]
    if None in {span_a, span_b, previous_span_a, previous_span_b}:
        return
    cloud_top = max(float(span_a), float(span_b))
    cloud_bottom = min(float(span_a), float(span_b))
    previous_cloud_top = max(float(previous_span_a), float(previous_span_b))
    previous_cloud_bottom = min(float(previous_span_a), float(previous_span_b))
    if previous_close <= previous_cloud_top and latest_close > cloud_top:
        if held:
            signals.append(make_signal("ICHIMOKU_CLOUD_RECOVERY", "수익관리", "CHART", f"{symbol} 보유종목이 일목 구름 위로 회복했습니다.", "profit"))
        else:
            level, message, score_delta = ichimoku_recovery_context(symbol, latest_close, sma_values, latest_index, latest_rsi, volume_ratio)
            signals.append(make_signal("ICHIMOKU_CLOUD_RECOVERY", level, "CHART", message, "opportunity" if score_delta > 0 else "risk", score_delta))
    if previous_close >= previous_cloud_bottom and latest_close < cloud_bottom:
        level = "방어검토" if held else "주의"
        message = f"{symbol} 보유종목이 일목 구름 아래로 이탈했습니다." if held else f"{symbol} 일목 구름 아래로 이탈해 신규 진입은 신중히 봅니다."
        signals.append(make_signal("ICHIMOKU_CLOUD_BREAKDOWN", level, "CHART", message, "risk"))


def ichimoku_recovery_context(
    symbol: str,
    latest_close: float,
    sma_values: dict[int, list[float | None]],
    latest_index: int,
    latest_rsi: float | None,
    volume_ratio: float | None,
) -> tuple[str, str, int]:
    ma20 = sma_values.get(20, [None])[latest_index] if latest_index < len(sma_values.get(20, [])) else None
    ma60 = sma_values.get(60, [None])[latest_index] if latest_index < len(sma_values.get(60, [])) else None
    ma20_distance = (latest_close / ma20 - 1) * 100 if ma20 else None
    ma60_distance = (latest_close / ma60 - 1) * 100 if ma60 else None
    rsi_ok = latest_rsi is not None and 35 <= latest_rsi <= 60
    rsi_hot = latest_rsi is not None and latest_rsi >= 65
    volume_confirmed = volume_ratio is not None and volume_ratio >= 1.2
    overextended = (ma20_distance is not None and ma20_distance >= 10) or (ma60_distance is not None and ma60_distance >= 15)

    if rsi_hot or overextended:
        return (
            "주의",
            f"{symbol} 일목 구름 위로 회복했지만 RSI나 이평선 이격이 높아 추격 진입 주의 구간입니다.",
            -10,
        )
    if rsi_ok and volume_confirmed:
        return (
            "기회후보",
            f"{symbol} 일목 구름 회복에 RSI와 거래량 확인이 붙어 진입 검토 후보입니다.",
            22,
        )
    return (
        "반등후보",
        f"{symbol} 일목 구름 위로 회복했지만 거래량·RSI 확인 전이라 반등 후보로 관찰합니다.",
        12,
    )


def build_score_context(
    symbol: str,
    closes: list[float],
    sma_values: dict[int, list[float | None]],
    bollinger: dict[str, list[float | None]],
    ichimoku: dict[str, list[float | None]],
    support_resistance: dict[str, Any],
    latest_index: int,
    latest_rsi: float | None,
    volume_ratio: float | None,
    position_metrics: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    latest_close = closes[latest_index]
    previous_close = closes[latest_index - 1]
    held = bool(position_metrics)
    drivers = [
        rsi_score_context(symbol, latest_rsi, held),
        volume_score_context(symbol, latest_close, previous_close, latest_rsi, volume_ratio, held),
        moving_average_trend_context(symbol, latest_close, sma_values, latest_index, held),
        moving_average_distance_context(symbol, latest_close, sma_values, latest_index, held),
        bollinger_score_context(symbol, latest_close, bollinger, latest_index, held),
        ichimoku_score_context(symbol, latest_close, ichimoku, latest_index, held),
        support_resistance_score_context(symbol, support_resistance, held),
    ]
    if held and position_metrics:
        drivers.append(position_return_score_context(symbol, position_metrics))
        drivers.append(position_stop_score_context(symbol, position_metrics))
        drivers.append(position_trailing_score_context(symbol, position_metrics))
    return [driver for driver in drivers if driver is not None and driver["points"] != 0]


def make_score_context(kind: str, points: int, message: str, level: str = "상태", bucket: str | None = None) -> dict[str, Any]:
    context = {
        "type": kind,
        "points": points,
        "level": level,
        "message": message,
    }
    if bucket:
        context["bucket"] = bucket
    return context


def rsi_score_context(symbol: str, value: float | None, held: bool) -> dict[str, Any] | None:
    if value is None:
        return None
    if held:
        if value >= 70:
            points = 8
            message = f"{symbol} RSI {value:.1f}: 보유 수익 관리가 필요한 과열 구간입니다."
        elif value >= 60:
            points = 3
            message = f"{symbol} RSI {value:.1f}: 상승 탄력이 있어 보유 관리를 봅니다."
        elif value <= 25:
            points = 12
            message = f"{symbol} RSI {value:.1f}: 보유 종목 깊은 약세 구간입니다."
        elif value <= 30:
            points = 8
            message = f"{symbol} RSI {value:.1f}: 보유 종목 약세 점검 구간입니다."
        elif value <= 35:
            points = 5
            message = f"{symbol} RSI {value:.1f}: 보유 종목 하락 압력이 남아 있습니다."
        else:
            points = 0
            message = ""
        bucket = "profit" if value >= 60 else "defense"
        return make_score_context("RSI_STATE", points, message, bucket=bucket)

    if value <= 25:
        points = 10
        message = f"{symbol} RSI {value:.1f}: 25 이하 공포성 과매도 구간입니다."
    elif value <= 30:
        points = 8
        message = f"{symbol} RSI {value:.1f}: 30 이하 과매도 관심 구간입니다."
    elif value <= 35:
        points = 6
        message = f"{symbol} RSI {value:.1f}: 과매도에서 회복을 기다릴 구간입니다."
    elif value <= 40:
        points = 4
        message = f"{symbol} RSI {value:.1f}: 눌림 관심 구간입니다."
    elif value <= 45:
        points = 2
        message = f"{symbol} RSI {value:.1f}: 약한 눌림 구간입니다."
    elif value <= 55:
        points = 0
        message = ""
    elif value <= 60:
        points = 2
        message = f"{symbol} RSI {value:.1f}: 중립 위 회복 구간입니다."
    elif value <= 65:
        points = -3
        message = f"{symbol} RSI {value:.1f}: 신규 진입에는 약간 높은 구간입니다."
    elif value <= 70:
        points = -8
        message = f"{symbol} RSI {value:.1f}: 추격 진입 주의 구간입니다."
    else:
        points = -16
        message = f"{symbol} RSI {value:.1f}: 과열 구간이라 신규 진입 점수를 낮춥니다."
    return make_score_context("RSI_STATE", points, message)


def volume_score_context(
    symbol: str,
    latest_close: float,
    previous_close: float,
    latest_rsi: float | None,
    volume_ratio: float | None,
    held: bool,
) -> dict[str, Any] | None:
    if volume_ratio is None:
        return None
    is_up = latest_close > previous_close
    is_down = latest_close < previous_close
    if held:
        if volume_ratio >= 2 and is_down:
            points = 12
        elif volume_ratio >= 1.5 and is_down:
            points = 8
        elif volume_ratio >= 1.5 and is_up:
            points = 3
        elif volume_ratio < 0.6:
            points = -4
        elif volume_ratio < 0.8:
            points = -2
        else:
            points = 0
        message = f"{symbol} 거래량 {volume_ratio:.2f}배: 보유 관리 관점의 수급 점수입니다."
        bucket = "defense" if is_down or points < 0 else "profit" if is_up else "defense"
        return make_score_context("VOLUME_STATE", points, message, bucket=bucket)

    if volume_ratio < 0.5:
        points = -3
    elif volume_ratio < 0.8:
        points = -2
    elif volume_ratio < 1.0:
        points = -1
    elif volume_ratio < 1.2:
        points = 1
    elif volume_ratio < 1.5:
        points = 3
    elif volume_ratio < 2.0:
        points = 5
    elif is_up:
        points = 8
    elif is_down and latest_rsi is not None and latest_rsi <= 35:
        points = 6
    elif is_down:
        points = 2
    else:
        points = 5
    message = f"{symbol} 거래량 {volume_ratio:.2f}배: 1.2배부터 확인 점수를 주고, 낮으면 감점합니다."
    return make_score_context("VOLUME_STATE", points, message)


def moving_average_trend_context(symbol: str, latest_close: float, sma_values: dict[int, list[float | None]], latest_index: int, held: bool) -> dict[str, Any] | None:
    valid = []
    for period in (20, 60, 120):
        values = sma_values.get(period, [])
        current = values[latest_index] if latest_index < len(values) else None
        if current is not None:
            valid.append((period, latest_close >= current))
    if not valid:
        return None
    above_count = sum(1 for _, is_above in valid if is_above)
    if held:
        points = {3: -8, 2: 1, 1: 8, 0: 16}.get(above_count, 0)
        message = f"{symbol} 이평 추세: 20/60/120일선 중 {above_count}개 위에 있어 보유 점검 점수를 조정합니다."
        return make_score_context("MA_TREND_STATE", points, message, bucket="defense")
    points = {3: 6, 2: 3, 1: -4, 0: -10}.get(above_count, 0)
    message = f"{symbol} 이평 추세: 20/60/120일선 중 {above_count}개 위에 있어 추세 점수를 반영합니다."
    return make_score_context("MA_TREND_STATE", points, message)


def moving_average_distance_context(symbol: str, latest_close: float, sma_values: dict[int, list[float | None]], latest_index: int, held: bool) -> dict[str, Any] | None:
    points: list[int] = []
    parts: list[str] = []
    held_distance_buckets: list[str] = []
    for period in (20, 60):
        values = sma_values.get(period, [])
        current = values[latest_index] if latest_index < len(values) else None
        if current is None:
            continue
        distance = (latest_close / current - 1) * 100
        parts.append(f"{period}일선 {distance:+.1f}%")
        if held:
            if distance <= -12:
                points.append(12)
                held_distance_buckets.append("defense")
            elif distance <= -7:
                points.append(8)
                held_distance_buckets.append("defense")
            elif distance <= -3:
                points.append(4)
                held_distance_buckets.append("defense")
            elif distance >= 20:
                points.append(8)
                held_distance_buckets.append("profit")
            elif distance >= 12:
                points.append(5)
                held_distance_buckets.append("profit")
            else:
                points.append(0)
        elif period == 20:
            if distance < -12:
                points.append(-4)
            elif distance < -7:
                points.append(1)
            elif distance < -3:
                points.append(3)
            elif distance <= 4:
                points.append(4)
            elif distance <= 8:
                points.append(0)
            elif distance <= 12:
                points.append(-5)
            else:
                points.append(-10)
        else:
            if distance < -20:
                points.append(-8)
            elif distance < -12:
                points.append(-2)
            elif distance < -5:
                points.append(2)
            elif distance <= 6:
                points.append(2)
            elif distance <= 12:
                points.append(0)
            elif distance <= 20:
                points.append(-5)
            else:
                points.append(-10)
    if not points:
        return None
    score = round(sum(points) / len(points))
    message = f"{symbol} 이평 이격: {', '.join(parts)} 기준으로 너무 멀면 감점, 지지권이면 가점합니다."
    bucket = None
    if held:
        bucket = "defense" if "defense" in held_distance_buckets else "profit" if "profit" in held_distance_buckets else None
    return make_score_context("MA_DISTANCE_STATE", score, message, bucket=bucket)


def bollinger_score_context(symbol: str, latest_close: float, bollinger: dict[str, list[float | None]], latest_index: int, held: bool) -> dict[str, Any] | None:
    lower = bollinger["lower"][latest_index]
    upper = bollinger["upper"][latest_index]
    if lower is None or upper is None or upper == lower:
        return None
    percent_b = (latest_close - lower) / (upper - lower)
    if held:
        if percent_b >= 1:
            points = 6
        elif percent_b <= 0:
            points = 8
        elif percent_b <= 0.2:
            points = 4
        else:
            points = 0
    elif percent_b <= 0:
        points = 6
    elif percent_b <= 0.2:
        points = 4
    elif percent_b <= 0.4:
        points = 2
    elif percent_b <= 0.85:
        points = 0
    elif percent_b <= 1:
        points = -3
    else:
        points = -8
    message = f"{symbol} 볼린저 위치: 밴드 안 위치 {percent_b:.2f} 기준으로 과매도/과열 점수를 반영합니다."
    bucket = "profit" if held and percent_b >= 1 else "defense" if held else None
    return make_score_context("BOLLINGER_STATE", points, message, bucket=bucket)


def ichimoku_score_context(symbol: str, latest_close: float, ichimoku: dict[str, list[float | None]], latest_index: int, held: bool) -> dict[str, Any] | None:
    span_a = ichimoku["span_a"][latest_index]
    span_b = ichimoku["span_b"][latest_index]
    if span_a is None or span_b is None:
        return None
    cloud_top = max(float(span_a), float(span_b))
    cloud_bottom = min(float(span_a), float(span_b))
    if latest_close > cloud_top:
        points = -5 if held else 3
        zone = "구름 위"
    elif latest_close < cloud_bottom:
        points = 10 if held else -6
        zone = "구름 아래"
    else:
        points = 3 if held else -1
        zone = "구름 안"
    message = f"{symbol} 일목 위치: 현재 가격이 {zone}에 있어 추세 점수를 반영합니다."
    return make_score_context("ICHIMOKU_STATE", points, message, bucket="defense" if held else None)


def position_return_score_context(symbol: str, position_metrics: dict[str, Any]) -> dict[str, Any] | None:
    value = position_metrics.get("return_pct")
    if value is None:
        return None
    value = float(value)
    if value <= -10:
        points = 18
    elif value <= -7:
        points = 12
    elif value <= -5:
        points = 8
    elif value < 0:
        points = 3
    elif value >= 30:
        points = 8
    elif value >= 20:
        points = 6
    elif value >= 10:
        points = 4
    elif value >= 5:
        points = 2
    else:
        points = 0
    message = f"{symbol} 평단 대비 {value:+.1f}%: 보유 관리 점수에 손익 구간을 반영합니다."
    return make_score_context("POSITION_RETURN_STATE", points, message, bucket="defense" if value < 0 else "profit")


def position_stop_score_context(symbol: str, position_metrics: dict[str, Any]) -> dict[str, Any] | None:
    stop_buffer = position_metrics.get("stop_buffer_pct")
    points = 0
    parts: list[str] = []
    if stop_buffer is not None:
        stop_buffer = float(stop_buffer)
        if stop_buffer <= 0:
            points += 22
        elif stop_buffer <= 3:
            points += 14
        elif stop_buffer <= 6:
            points += 8
        elif stop_buffer >= 25:
            points -= 8
        elif stop_buffer >= 15:
            points -= 5
        elif stop_buffer >= 10:
            points -= 3
        parts.append(f"위험선까지 {stop_buffer:+.1f}%")
    if points == 0:
        return None
    points = int(clamp_number(points, -16, 24))
    message = f"{symbol} 고정 방어 기준: {', '.join(parts)} 남아 방어 점수에 반영합니다."
    return make_score_context("POSITION_STOP_STATE", points, message, bucket="defense")


def position_trailing_score_context(symbol: str, position_metrics: dict[str, Any]) -> dict[str, Any] | None:
    trailing_buffer = position_metrics.get("trailing_buffer_pct")
    return_pct = float(position_metrics.get("return_pct") or 0)
    if trailing_buffer is None or return_pct <= 0:
        return None
    trailing_buffer = float(trailing_buffer)
    if trailing_buffer <= 0:
        points = 18
    elif trailing_buffer <= 3:
        points = 9
    elif trailing_buffer <= 6:
        points = 4
    elif trailing_buffer >= 15:
        points = -5
    elif trailing_buffer >= 10:
        points = -3
    elif trailing_buffer >= 8:
        points = -2
    else:
        points = 0
    if points == 0:
        return None
    message = f"{symbol} 트레일링 기준: 트레일링선까지 {trailing_buffer:+.1f}% 남아 수익보호 점수에 반영합니다."
    return make_score_context("POSITION_TRAILING_STATE", points, message, bucket="profit")


def support_resistance_levels(
    symbol: str,
    bars: list[dict[str, Any]],
    latest_close: float,
    lookback: int = 180,
    entry_date: str | None = None,
    average_entry_price: float | None = None,
) -> dict[str, Any]:
    entry_index = entry_start_index(bars, entry_date)
    position_scoped = entry_index is not None and entry_index < len(bars)
    source_bars = bars[entry_index:] if position_scoped else bars
    recent = source_bars[-lookback:]
    scope = "position" if position_scoped else "chart"
    scope_label = "매수일 이후" if position_scoped else f"최근 {lookback}일"
    empty = {
        "symbol": symbol,
        "scope": scope,
        "scope_label": scope_label,
        "entry_date": entry_date or "",
        "supports": [],
        "resistances": [],
        "nearest_support": None,
        "nearest_resistance": None,
    }
    if latest_close <= 0 or (not position_scoped and len(recent) < 30) or (position_scoped and len(recent) < 3):
        return empty

    start_index = len(bars) - len(recent)
    candidates: list[dict[str, Any]] = []
    radius = 3
    for local_index in range(radius, len(recent) - radius):
        index = start_index + local_index
        window = recent[local_index - radius : local_index + radius + 1]
        high = float(recent[local_index]["high"])
        low = float(recent[local_index]["low"])
        if high >= max(float(bar["high"]) for bar in window):
            candidates.append({"price": high, "index": index, "time": recent[local_index]["time"], "source": "pivot_high", "weight": 1.0})
        if low <= min(float(bar["low"]) for bar in window):
            candidates.append({"price": low, "index": index, "time": recent[local_index]["time"], "source": "pivot_low", "weight": 1.0})

    if position_scoped:
        entry_bar = source_bars[0]
        high_local, high_bar = max(enumerate(source_bars), key=lambda item: float(item[1]["high"]))
        low_local, low_bar = min(enumerate(source_bars), key=lambda item: float(item[1]["low"]))
        candidates.append({"price": float(high_bar["high"]), "index": entry_index + high_local, "time": high_bar["time"], "source": "post_entry_high", "weight": 2.4})
        candidates.append({"price": float(low_bar["low"]), "index": entry_index + low_local, "time": low_bar["time"], "source": "post_entry_low", "weight": 2.4})
        candidates.append({"price": float(entry_bar["high"]), "index": entry_index, "time": entry_bar["time"], "source": "entry_day_high", "weight": 1.8})
        candidates.append({"price": float(entry_bar["low"]), "index": entry_index, "time": entry_bar["time"], "source": "entry_day_low", "weight": 1.8})
        if average_entry_price:
            candidates.append({"price": float(average_entry_price), "index": entry_index, "time": entry_bar["time"], "source": "entry_price", "weight": 2.2})

    for period in (60, 120):
        if len(source_bars) < period:
            continue
        window = source_bars[-period:]
        offset = len(bars) - len(window)
        high_local, high_bar = max(enumerate(window), key=lambda item: float(item[1]["high"]))
        low_local, low_bar = min(enumerate(window), key=lambda item: float(item[1]["low"]))
        candidates.append({"price": float(high_bar["high"]), "index": offset + high_local, "time": high_bar["time"], "source": f"{period}d_high", "weight": 2.0})
        candidates.append({"price": float(low_bar["low"]), "index": offset + low_local, "time": low_bar["time"], "source": f"{period}d_low", "weight": 2.0})

    clusters = cluster_price_levels(candidates, latest_close)
    levels = [format_price_level(cluster, latest_close, len(bars) - 1) for cluster in clusters]
    levels = [level for level in levels if level["touches"] >= 2 or level["source_count"] > 1 or (position_scoped and level["anchored"])]
    supports = sorted((level for level in levels if level["kind"] == "support"), key=lambda level: (abs(level["distance_pct"]), -level["strength"]))[:3]
    resistances = sorted((level for level in levels if level["kind"] == "resistance"), key=lambda level: (abs(level["distance_pct"]), -level["strength"]))[:3]
    for index, level in enumerate(supports, start=1):
        level["label"] = f"S{index}"
    for index, level in enumerate(resistances, start=1):
        level["label"] = f"R{index}"
    return {
        "symbol": symbol,
        "scope": scope,
        "scope_label": scope_label,
        "entry_date": entry_date or "",
        "supports": supports,
        "resistances": resistances,
        "nearest_support": supports[0] if supports else None,
        "nearest_resistance": resistances[0] if resistances else None,
    }


def cluster_price_levels(candidates: list[dict[str, Any]], latest_close: float) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    tolerance_pct = 1.4
    for candidate in sorted(candidates, key=lambda item: float(item["price"])):
        price = float(candidate["price"])
        nearest = None
        nearest_distance = float("inf")
        for cluster in clusters:
            distance_pct = abs(price / cluster["price"] - 1) * 100
            if distance_pct <= tolerance_pct and distance_pct < nearest_distance:
                nearest = cluster
                nearest_distance = distance_pct
        if nearest is None:
            clusters.append(
                {
                    "price": price,
                    "weight": float(candidate.get("weight", 1.0)),
                    "touches": 1,
                    "sources": {candidate["source"]},
                    "latest_index": int(candidate["index"]),
                    "latest_time": candidate["time"],
                }
            )
            continue
        weight = float(candidate.get("weight", 1.0))
        nearest["price"] = (nearest["price"] * nearest["weight"] + price * weight) / (nearest["weight"] + weight)
        nearest["weight"] += weight
        nearest["touches"] += 1
        nearest["sources"].add(candidate["source"])
        if int(candidate["index"]) > nearest["latest_index"]:
            nearest["latest_index"] = int(candidate["index"])
            nearest["latest_time"] = candidate["time"]
    return clusters


def format_price_level(cluster: dict[str, Any], latest_close: float, latest_index: int) -> dict[str, Any]:
    price = float(cluster["price"])
    distance_pct = (price / latest_close - 1) * 100
    days_since_touch = max(0, latest_index - int(cluster["latest_index"]))
    recency_bonus = 2 if days_since_touch <= 20 else 1 if days_since_touch <= 60 else 0
    source_bonus = 1 if len(cluster["sources"]) >= 2 else 0
    strength = int(clamp_number(round(cluster["touches"] + recency_bonus + source_bonus), 1, 5))
    sources = sorted(cluster["sources"])
    anchored_sources = {"entry_price", "entry_day_high", "entry_day_low", "post_entry_high", "post_entry_low"}
    return {
        "kind": "support" if price <= latest_close else "resistance",
        "price": round(price, 4),
        "distance_pct": round(distance_pct, 2),
        "touches": int(cluster["touches"]),
        "strength": strength,
        "source_count": len(cluster["sources"]),
        "sources": sources,
        "anchored": bool(anchored_sources.intersection(sources)),
        "latest_touch": cluster["latest_time"],
    }


def support_resistance_score_context(symbol: str, support_resistance: dict[str, Any], held: bool) -> dict[str, Any] | None:
    support = support_resistance.get("nearest_support")
    resistance = support_resistance.get("nearest_resistance")
    points = 0
    parts: list[str] = []

    if support:
        support_distance = abs(float(support["distance_pct"]))
        if held:
            support_points = 8 if support_distance <= 1 else 5 if support_distance <= 2.5 else 2 if support_distance <= 5 else 0
        else:
            support_points = 9 if support_distance <= 1 else 6 if support_distance <= 2.5 else 3 if support_distance <= 5 else 0
        points += support_points
        parts.append(f"지지선 {support['label']} {support['distance_pct']:+.1f}%")

    if resistance:
        resistance_distance = float(resistance["distance_pct"])
        if held:
            resistance_points = 7 if resistance_distance <= 1.5 else 4 if resistance_distance <= 3 else 2 if resistance_distance <= 5 else 0
        else:
            if resistance_distance <= 1.5:
                resistance_points = -10
            elif resistance_distance <= 3:
                resistance_points = -6
            elif resistance_distance <= 5:
                resistance_points = -3
            elif resistance_distance >= 10:
                resistance_points = 3
            else:
                resistance_points = 0
        points += resistance_points
        parts.append(f"저항선 {resistance['label']} +{resistance_distance:.1f}%")

    if not parts:
        return None
    points = int(clamp_number(points, -12, 12))
    if points == 0:
        return None
    scope_label = support_resistance.get("scope_label") or "자동"
    message = f"{symbol} {scope_label} 지지/저항: {', '.join(parts)} 기준으로 점수를 조정합니다."
    bucket = None
    if held:
        support_distance = abs(float(support["distance_pct"])) if support else float("inf")
        resistance_distance = float(resistance["distance_pct"]) if resistance else float("inf")
        bucket = "defense" if support_distance <= resistance_distance else "profit"
    return make_score_context("SUPPORT_RESISTANCE_STATE", points, message, bucket=bucket)


def preferred_position_action(current: str, candidate: str) -> str:
    return candidate if POSITION_ACTION_RANK.get(candidate, 0) > POSITION_ACTION_RANK.get(current, 0) else current


def add_position_signals(
    symbol: str,
    signals: list[dict[str, Any]],
    position: dict[str, Any] | None,
    bars: list[dict[str, Any]],
    closes: list[float],
    sma_values: dict[int, list[float | None]],
    latest_rsi: float | None,
    previous_rsi: float | None,
    volume_ratio: float | None,
    support_resistance: dict[str, Any],
) -> dict[str, Any] | None:
    if not position:
        return None
    average_entry = position.get("average_entry_price")
    if not average_entry:
        return {
            "held": True,
            "symbol": symbol,
            "missing_average_entry": True,
            "suggested_action": "평단입력",
        }

    latest_close = closes[-1]
    previous_close = closes[-2] if len(closes) >= 2 else latest_close
    return_pct = (latest_close / float(average_entry) - 1) * 100
    quantity = position.get("quantity")
    pnl_amount = (latest_close - float(average_entry)) * float(quantity) if quantity else None
    post_entry_closes = closes_since_entry(bars, closes, position.get("entry_date"))
    highest_close = max(post_entry_closes) if post_entry_closes else max(closes[-120:])
    drawdown_from_high_pct = (latest_close / highest_close - 1) * 100 if highest_close else None
    stop_loss_pct = float(position.get("stop_loss_pct", -7))
    trailing_stop_pct = float(position.get("trailing_stop_pct", -8))
    stop_price = float(average_entry) * (1 + stop_loss_pct / 100)
    trailing_stop_price = highest_close * (1 + trailing_stop_pct / 100) if highest_close else None
    stop_buffer_pct = (latest_close / stop_price - 1) * 100 if stop_price > 0 else None
    trailing_buffer_pct = (latest_close / trailing_stop_price - 1) * 100 if trailing_stop_price and trailing_stop_price > 0 else None
    suggested_action = "보유점검"

    if return_pct <= -5:
        signals.append(make_signal("LOSS_WARNING", "주의", "POSITION", f"{symbol} 평단 대비 {return_pct:.1f}%입니다.", "risk"))
        suggested_action = preferred_position_action(suggested_action, "방어검토")
    if stop_buffer_pct is not None and 0 < stop_buffer_pct <= 3:
        signals.append(make_signal("STOP_BUFFER_REVIEW", "방어검토", "POSITION", f"{symbol} 위험선까지 {stop_buffer_pct:.1f}% 남았습니다.", "risk"))
        suggested_action = preferred_position_action(suggested_action, "위험선근접")
    elif stop_buffer_pct is not None and 0 < stop_buffer_pct <= 6:
        signals.append(make_signal("STOP_BUFFER_WARNING", "주의", "POSITION", f"{symbol} 위험선까지 {stop_buffer_pct:.1f}% 남아 방어 기준을 확인합니다.", "risk"))
        suggested_action = preferred_position_action(suggested_action, "방어선확인")
    if return_pct <= stop_loss_pct:
        signals.append(make_signal("STOP_REVIEW", "방어검토", "POSITION", f"{symbol} 설정 방어 기준({stop_loss_pct:.0f}%)에 닿았습니다.", "risk"))
        suggested_action = preferred_position_action(suggested_action, "방어검토")
    if return_pct <= -10 and sma_values[60][-1] is not None and latest_close < sma_values[60][-1]:
        signals.append(make_signal("RISK_EXIT_REVIEW", "위험", "POSITION", f"{symbol} -10% 손실과 60일선 이탈이 겹쳤습니다.", "risk"))
        suggested_action = preferred_position_action(suggested_action, "위험축소검토")

    below_ma60 = sma_values[60][-1] is not None and latest_close < sma_values[60][-1]
    below_ma60_two_days = (
        len(closes) >= 2
        and sma_values[60][-1] is not None
        and sma_values[60][-2] is not None
        and latest_close < sma_values[60][-1]
        and previous_close < sma_values[60][-2]
    )
    down_volume = bool(volume_ratio is not None and volume_ratio >= 1.5 and latest_close < previous_close)
    support_breakdown = False
    support = support_resistance.get("nearest_support") if support_resistance else None
    if support:
        support_distance = abs(float(support["distance_pct"]))
        support_pressure = (
            return_pct < 0
            or drawdown_from_high_pct is not None
            and drawdown_from_high_pct <= -5
            or sma_values[20][-1] is not None
            and latest_close < sma_values[20][-1]
            or sma_values[60][-1] is not None
            and latest_close < sma_values[60][-1]
        )
        if 0 < support_distance <= 3 and support_pressure:
            signals.append(
                make_signal(
                    "POSITION_SUPPORT_BUFFER_WARNING",
                    "주의",
                    "POSITION",
                    f"{symbol} 매수일 이후 {support['label']} 지지선까지 {support_distance:.1f}% 남았습니다.",
                    "risk",
                )
            )
            suggested_action = preferred_position_action(suggested_action, "방어선확인")

    previous_support = None
    if len(bars) >= 3:
        previous_levels = support_resistance_levels(
            symbol,
            bars[:-1],
            previous_close,
            entry_date=position.get("entry_date"),
            average_entry_price=float(average_entry),
        )
        if previous_levels.get("scope") == "position":
            previous_support = previous_levels.get("nearest_support")
    support_breakdown_tolerance_pct = 1.0
    if previous_support and latest_close < float(previous_support["price"]) * (1 - support_breakdown_tolerance_pct / 100):
        support_breakdown = True
        support_label = previous_support.get("label", "S1")
        support_price = float(previous_support["price"])
        level = "위험" if below_ma60 or down_volume else "방어검토"
        signals.append(
            make_signal(
                "POSITION_SUPPORT_BREAKDOWN",
                level,
                "POSITION",
                f"{symbol} 매수일 이후 {support_label} 지지선 ${support_price:.2f} 아래로 종가 이탈했습니다.",
                "risk",
            )
        )
        suggested_action = preferred_position_action(suggested_action, "위험축소검토" if level == "위험" else "구조방어검토")
        if down_volume:
            signals.append(
                make_signal(
                    "POSITION_SUPPORT_VOLUME_BREAKDOWN",
                    "위험",
                    "POSITION",
                    f"{symbol} 지지선 이탈에 하락 거래량 {volume_ratio:.1f}배가 겹쳤습니다.",
                    "risk",
                )
            )
            suggested_action = preferred_position_action(suggested_action, "위험축소검토")

    if below_ma60_two_days:
        signals.append(
            make_signal(
                "POSITION_MA60_CONFIRM_BREAKDOWN",
                "방어검토",
                "POSITION",
                f"{symbol} 종가가 60일선 아래에서 2거래일 연속 머물렀습니다.",
                "risk",
            )
        )
        suggested_action = preferred_position_action(suggested_action, "구조방어검토")
    if support_breakdown and below_ma60:
        signals.append(
            make_signal(
                "POSITION_STRUCTURE_EXIT_REVIEW",
                "위험",
                "POSITION",
                f"{symbol} 지지선 이탈과 60일선 이탈이 겹쳐 구조가 크게 흔들렸습니다.",
                "risk",
            )
        )
        suggested_action = preferred_position_action(suggested_action, "위험축소검토")

    for period in (20, 60, 120):
        ma = sma_values[period][-1]
        if ma is not None and latest_close < ma:
            level = "위험" if period == 120 else "방어검토" if period == 60 else "주의"
            signals.append(make_signal(f"POSITION_MA{period}_BREAKDOWN", level, "POSITION", f"보유 종목이 {period}일선 아래에 있습니다.", "risk"))
            if period >= 60:
                suggested_action = preferred_position_action(suggested_action, "비중점검")

    profit_threshold = 30 if return_pct >= 30 else 20 if return_pct >= 20 else 10 if return_pct >= 10 else None
    if profit_threshold:
        signals.append(make_signal(f"PROFIT_{profit_threshold}", "수익관리", "POSITION", f"{symbol} 평단 대비 +{return_pct:.1f}% 수익 구간입니다.", "profit"))
        suggested_action = preferred_position_action(suggested_action, "수익보호" if profit_threshold >= 30 else "수익관리")

    if drawdown_from_high_pct is not None:
        if drawdown_from_high_pct <= min(-10, trailing_stop_pct - 2):
            signals.append(make_signal("TRAILING_STOP_REVIEW", "수익관리", "POSITION", f"고점 대비 {drawdown_from_high_pct:.1f}% 하락했습니다.", "profit"))
            suggested_action = preferred_position_action(suggested_action, "수익보호")
        elif drawdown_from_high_pct <= trailing_stop_pct:
            signals.append(make_signal("TRAILING_STOP_WARNING", "수익관리", "POSITION", f"고점 대비 {drawdown_from_high_pct:.1f}% 하락했습니다.", "profit"))
            suggested_action = preferred_position_action(suggested_action, "수익관리")
        elif trailing_buffer_pct is not None and 0 < trailing_buffer_pct <= 3 and return_pct > 0:
            signals.append(make_signal("TRAILING_BUFFER_WARNING", "수익관리", "POSITION", f"트레일링 기준가까지 {trailing_buffer_pct:.1f}% 남았습니다.", "profit"))
            suggested_action = preferred_position_action(suggested_action, "수익보호")
    if previous_rsi is not None and latest_rsi is not None and previous_rsi >= 70 > latest_rsi and return_pct > 0:
        signals.append(make_signal("RSI_OVERHEAT_COOLING_HELD", "수익관리", "POSITION", "보유 수익 중 RSI 과열이 식고 있습니다.", "profit"))
        suggested_action = preferred_position_action(suggested_action, "수익보호")

    return {
        "held": True,
        "symbol": symbol,
        "average_entry_price": float(average_entry),
        "quantity": quantity,
        "entry_date": position.get("entry_date") or "",
        "return_pct": round(return_pct, 2),
        "pnl_amount": round(pnl_amount, 2) if pnl_amount is not None else None,
        "highest_close_since_entry": round(highest_close, 4),
        "drawdown_from_high_pct": round(drawdown_from_high_pct, 2) if drawdown_from_high_pct is not None else None,
        "stop_loss_pct": round(stop_loss_pct, 2),
        "stop_price": round(stop_price, 4),
        "stop_buffer_pct": round(stop_buffer_pct, 2) if stop_buffer_pct is not None else None,
        "trailing_stop_pct": round(trailing_stop_pct, 2),
        "trailing_stop_price": round(trailing_stop_price, 4) if trailing_stop_price is not None else None,
        "trailing_buffer_pct": round(trailing_buffer_pct, 2) if trailing_buffer_pct is not None else None,
        "suggested_action": suggested_action,
        "next_earnings_date": position.get("next_earnings_date") or "",
        "notes": position.get("notes") or "",
    }


def add_earnings_signals(symbol: str, signals: list[dict[str, Any]], position: dict[str, Any] | None) -> None:
    if not position or not position.get("next_earnings_date"):
        return
    try:
        earnings_date = date.fromisoformat(str(position["next_earnings_date"]))
    except ValueError:
        return
    today = datetime.now().date()
    days_until = (earnings_date - today).days
    if days_until == 7:
        signals.append(make_signal("EARNINGS_7D", "주의", "EARNINGS", f"{symbol} 실적 발표가 7일 남았습니다.", "risk"))
    elif days_until == 1:
        signals.append(make_signal("EARNINGS_1D", "주의", "EARNINGS", f"{symbol} 실적 발표가 하루 남았습니다.", "risk"))
    elif days_until == 0:
        signals.append(make_signal("EARNINGS_TODAY", "위험", "EARNINGS", f"{symbol} 오늘 실적 발표 예정입니다.", "risk"))
    elif days_until == -1:
        signals.append(make_signal("EARNINGS_AFTER", "주의", "EARNINGS", f"{symbol} 실적 발표 다음 거래일 점검 구간입니다.", "risk"))


def closes_since_entry(bars: list[dict[str, Any]], closes: list[float], entry_date: str | None) -> list[float]:
    start_index = entry_start_index(bars, entry_date)
    if start_index is None or start_index >= len(closes):
        return closes[-120:]
    return closes[start_index:] or closes[-120:]


def entry_start_index(bars: list[dict[str, Any]], entry_date: str | None) -> int | None:
    if not entry_date:
        return None
    try:
        entry = date.fromisoformat(entry_date)
    except ValueError:
        return None
    for index, bar in enumerate(bars):
        bar_date = parse_bar_date(bar["time"])
        if bar_date and bar_date >= entry:
            return index
    return len(bars)


def parse_bar_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _ema_sparse(values: list[float | None], period: int) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    valid = [(index, value) for index, value in enumerate(values) if value is not None]
    if len(valid) < period:
        return output
    first_index = valid[period - 1][0]
    current = mean(value for _, value in valid[:period])
    output[first_index] = current
    alpha = 2 / (period + 1)
    for index, value in valid[period:]:
        current = value * alpha + current * (1 - alpha)
        output[index] = current
    return output


def make_signal(kind: str, level: str, category: str, message: str, intent: str, score_delta: int | None = None) -> dict[str, Any]:
    signal = {
        "type": kind,
        "level": level,
        "category": category,
        "message": message,
        "intent": intent,
        "delivery": DEFAULT_ALERT_PREFERENCES.get(kind, "log"),
    }
    if score_delta is not None:
        signal["score_delta"] = score_delta
    return signal


def apply_alert_preferences(signals: list[dict[str, Any]], config: dict[str, Any]) -> None:
    preferences = config.get("alert_preferences", {})
    for signal in signals:
        signal["delivery"] = preferences.get(signal["type"], signal.get("delivery", "log"))
        signal["push"] = signal["delivery"] == "push"


def rank_alert(signals: list[dict[str, Any]]) -> str:
    if not signals:
        return "정상"
    return max((signal["level"] for signal in signals), key=lambda level: LEVEL_RANK.get(level, 0))


def build_signal_score(
    signals: list[dict[str, Any]],
    position_metrics: dict[str, Any] | None,
    alert_level: str,
    score_context: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    held = bool(position_metrics)
    points_by_type = POSITION_SCORE_POINTS if held else BUY_SCORE_POINTS
    base = 50
    drivers: list[dict[str, Any]] = []
    total = base
    for context in score_context or []:
        points = int(context.get("points", 0))
        if points == 0:
            continue
        total += points
        drivers.append(
            {
                "type": context.get("type", ""),
                "points": points,
                "level": context.get("level", "상태"),
                "message": context.get("message", ""),
                "bucket": context.get("bucket", ""),
            }
        )

    for signal in signals:
        signal_type = signal.get("type", "")
        points = signal_points(signal, held, points_by_type)
        if points == 0:
            continue
        total += points
        drivers.append(
            {
                "type": signal_type,
                "points": points,
                "level": signal.get("level", ""),
                "message": signal.get("message", ""),
                "category": signal.get("category", ""),
                "intent": signal.get("intent", ""),
                "bucket": position_signal_bucket(signal) if held else "",
            }
        )

    floor = score_floor(alert_level, held)
    components = position_score_components(drivers) if held else []
    if held:
        value = position_component_score_value(components, floor)
    else:
        value = max(total, floor)
        cap = score_cap(alert_level, held)
        if cap is not None:
            value = min(value, cap)
    value = int(clamp_number(value, 0, 100))
    drivers.sort(key=lambda driver: abs(int(driver["points"])), reverse=True)
    output = {
        "mode": "position" if held else "watch",
        "label": "관리강도" if held else "진입점수",
        "value": value,
        "stage": score_stage(value, held, alert_level),
        "drivers": drivers[:6],
    }
    if held:
        output["components"] = components
    return output


def position_signal_bucket(signal: dict[str, Any]) -> str:
    signal_type = signal.get("type", "")
    if signal_type in POSITION_EVENT_TYPES or signal.get("category") in {"EARNINGS", "MARKET"}:
        return "event"
    if signal.get("intent") == "profit":
        return "profit"
    if signal.get("intent") == "risk":
        return "defense"
    return "defense"


def position_score_components(drivers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        {"key": "defense", "label": "방어", "base": 40},
        {"key": "profit", "label": "수익보호", "base": 30},
        {"key": "event", "label": "이벤트", "base": 0},
    ]
    output: list[dict[str, Any]] = []
    for spec in specs:
        key = spec["key"]
        component_drivers = [driver for driver in drivers if driver.get("bucket") == key]
        driver_points = sum(int(driver.get("points", 0)) for driver in component_drivers)
        base = int(spec["base"]) if key == "defense" or driver_points > 0 else 0
        total = base + driver_points
        value = int(clamp_number(total, 0, 100))
        component_drivers.sort(key=lambda driver: abs(int(driver.get("points", 0))), reverse=True)
        output.append(
            {
                "key": key,
                "label": spec["label"],
                "value": value,
                "stage": position_component_stage(key, value),
                "drivers": component_drivers[:3],
            }
        )
    return output


def position_component_score_value(components: list[dict[str, Any]], floor: int) -> int:
    values = {component["key"]: int(component["value"]) for component in components}
    primary = max(values.get("defense", 0), values.get("profit", 0))
    event_bonus = min(15, round(values.get("event", 0) * 0.5))
    return int(max(floor, primary + event_bonus))


def position_component_stage(key: str, value: int) -> str:
    if key == "defense":
        if value >= 90:
            return "위험축소"
        if value >= 75:
            return "강한방어"
        if value >= 60:
            return "구조방어"
        if value >= 40:
            return "방어선확인"
        if value >= 25:
            return "관찰"
        return "안정"
    if key == "profit":
        if value >= 90:
            return "수익보호강화"
        if value >= 75:
            return "비중점검"
        if value >= 60:
            return "과열점검"
        if value >= 40:
            return "수익보호"
        if value >= 20:
            return "관찰"
        return "낮음"
    if value >= 70:
        return "이벤트위험"
    if value >= 40:
        return "일정주의"
    if value > 0:
        return "체크"
    return "없음"


def signal_points(signal: dict[str, Any], held: bool, points_by_type: dict[str, int]) -> int:
    if "score_delta" in signal:
        return int(signal["score_delta"])
    signal_type = signal.get("type", "")
    level = signal.get("level", "")
    if not held:
        if signal_type == "BEARISH_VOLUME_SPIKE":
            return 12 if level == "공포관심" else 4
        if signal_type in {"LOW_60_BREAKDOWN", "LOW_120_BREAKDOWN"}:
            return 10 if level == "공포관심" else points_by_type.get(signal_type, -18)
        if signal_type == "GAP_DOWN":
            return 8 if level == "공포관심" else 3
    return points_by_type.get(signal_type, fallback_signal_points(signal, held))


def fallback_signal_points(signal: dict[str, Any], held: bool) -> int:
    level = signal.get("level", "")
    if held:
        return {
            "수익관리": 10,
            "주의": 16,
            "수익보호검토": 24,
            "방어검토": 28,
            "위험": 36,
        }.get(level, 0)
    return {
        "관심": 8,
        "공포관심": 18,
        "반등후보": 22,
        "기회후보": 28,
        "돌파후보": 30,
        "주의": -10,
        "위험": -18,
    }.get(level, 0)


def score_floor(alert_level: str, held: bool) -> int:
    if held:
        return {
            "수익관리": 55,
            "주의": 60,
            "수익보호검토": 70,
            "방어검토": 75,
            "위험": 85,
        }.get(alert_level, 0)
    return {
        "관심": 55,
        "공포관심": 60,
        "반등후보": 62,
        "기회후보": 70,
        "돌파후보": 74,
    }.get(alert_level, 50)


def score_cap(alert_level: str, held: bool) -> int | None:
    if held:
        return None
    return {
        "주의": 44,
        "위험": 25,
    }.get(alert_level)


def score_stage(value: int, held: bool, alert_level: str = "") -> str:
    if held:
        if value >= 90:
            return "강한관리"
        if value >= 80:
            return "관리강화"
        if value >= 70:
            return "점검필요"
        if value >= 60:
            return "집중관리"
        if value >= 50:
            return "관찰"
        if value >= 30:
            return "안정보유"
        return "매우안정"
    if value >= 85:
        return "진입검토"
    if value >= 70:
        if alert_level in {"기회후보", "돌파후보"}:
            return "진입검토"
        return "자리검토"
    if value >= 62:
        return "반등체크"
    if value >= 55:
        return "관찰"
    if value >= 45:
        return "대기"
    if value >= 30:
        return "주의"
    return "진입금지"


def clamp_number(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def change_pct(values: list[float], periods: int) -> float | None:
    if len(values) <= periods:
        return None
    base = values[-periods - 1]
    if base == 0:
        return None
    return round((values[-1] / base - 1) * 100, 2)


def ma_distance(close: float, ma_snapshot: dict[str, float | None]) -> dict[str, float | None]:
    output: dict[str, float | None] = {}
    for period, value in ma_snapshot.items():
        output[period] = round((close / value - 1) * 100, 2) if value else None
    return output


def attach_indicators(
    bars: list[dict[str, Any]],
    rsi_values: list[float | None],
    sma_values: dict[int, list[float | None]],
    volume_sma: list[float | None],
    macd: list[float | None],
    macd_signal: list[float | None],
    bollinger: dict[str, list[float | None]],
    ichimoku: dict[str, list[float | None]],
    signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signal_types_by_time: dict[str, list[str]] = {}
    for signal in signals:
        signal_time = signal.get("time")
        if signal_time:
            signal_types_by_time.setdefault(signal_time, []).append(signal["type"])
    output: list[dict[str, Any]] = []
    for index, bar in enumerate(bars):
        row = dict(bar)
        row["rsi14"] = round(rsi_values[index], 2) if rsi_values[index] is not None else None
        row["volume_sma"] = round(volume_sma[index], 2) if volume_sma[index] is not None else None
        row["macd"] = round(macd[index], 4) if macd[index] is not None else None
        row["macd_signal"] = round(macd_signal[index], 4) if macd_signal[index] is not None else None
        row["bb_middle"] = round(bollinger["middle"][index], 4) if bollinger["middle"][index] is not None else None
        row["bb_upper"] = round(bollinger["upper"][index], 4) if bollinger["upper"][index] is not None else None
        row["bb_lower"] = round(bollinger["lower"][index], 4) if bollinger["lower"][index] is not None else None
        row["ichimoku_tenkan"] = round(ichimoku["tenkan"][index], 4) if ichimoku["tenkan"][index] is not None else None
        row["ichimoku_kijun"] = round(ichimoku["kijun"][index], 4) if ichimoku["kijun"][index] is not None else None
        row["ichimoku_span_a"] = round(ichimoku["span_a"][index], 4) if ichimoku["span_a"][index] is not None else None
        row["ichimoku_span_b"] = round(ichimoku["span_b"][index], 4) if ichimoku["span_b"][index] is not None else None
        row["signals"] = signal_types_by_time.get(row["time"], [])
        for period, values in sma_values.items():
            row[f"sma{period}"] = round(values[index], 4) if values[index] is not None else None
        output.append(row)
    if output:
        latest_time = output[-1]["time"]
        output[-1]["signals"] = [signal["type"] for signal in signals if signal["delivery"] != "off"]
        for signal in signals:
            signal["time"] = latest_time
    return output


def apply_market_regime(results: list[dict[str, Any]], config: dict[str, Any], vix_history: dict[str, Any] | None = None) -> dict[str, Any]:
    spy = result_by_symbol(results, "SPY")
    qqq = result_by_symbol(results, "QQQ")
    spy_above = is_above_ma(spy, "120")
    qqq_above = is_above_ma(qqq, "120")
    spy_ma120_distance = distance_from_ma(spy, "120")
    qqq_ma120_distance = distance_from_ma(qqq, "120")
    vix = build_vix_state(vix_history, config)
    if spy_above is False and qqq_above is False:
        regime = "risk_off"
        label = "리스크오프"
        level = "위험"
        summary = "SPY와 QQQ가 모두 120일선 아래에 있어 진입성 신호를 보수적으로 봅니다."
    elif spy_above is True and qqq_above is True:
        regime = "risk_on"
        label = "리스크온"
        level = "정상"
        summary = "SPY와 QQQ가 모두 120일선 위에 있어 시장 추세가 우호적입니다."
    else:
        regime = "mixed"
        label = "혼조"
        level = "주의"
        summary = "SPY와 QQQ의 장기 추세가 엇갈려 신호 해석을 한 단계 보수적으로 봅니다."

    market_signals: list[dict[str, Any]] = []
    if spy_above is False:
        market_signals.append(make_signal("SPY_BELOW_MA120", "주의", "MARKET", "SPY가 120일선 아래입니다.", "risk"))
    if qqq_above is False:
        market_signals.append(make_signal("QQQ_BELOW_MA120", "주의", "MARKET", "QQQ가 120일선 아래입니다.", "risk"))
    if regime == "risk_off":
        market_signals.append(make_signal("MARKET_RISK_OFF", "위험", "MARKET", "시장 대표 ETF가 모두 약세 구간입니다.", "risk"))
    if regime == "risk_on":
        market_signals.append(make_signal("MARKET_RISK_ON", "정상", "MARKET", "시장 대표 ETF가 모두 장기 추세 위입니다.", "review"))
    if vix:
        add_vix_signals(market_signals, vix, config)
        if LEVEL_RANK.get(vix["level"], 0) > LEVEL_RANK.get(level, 0):
            level = vix["level"]
            if vix["level"] == "위험":
                label = "고변동"
                regime = "volatility_risk"
            elif vix["level"] == "주의" and regime == "risk_on":
                label = "변동성주의"
                regime = "volatility_watch"
        summary += f" VIX는 {vix['value']:.1f}로 {vix['label']} 구간입니다."
        if vix.get("change_pct_5d") is not None:
            summary += f" 5거래일 변화율은 {vix['change_pct_5d']:+.1f}%입니다."
        if vix.get("fallback") and vix.get("source") == "demo":
            summary += " 현재 VIX는 데모 대체값입니다."
        elif vix.get("fallback") and vix.get("source") == "fred":
            summary += " CBOE 요청 실패로 FRED 종가를 사용합니다."
    apply_alert_preferences(market_signals, config)

    fear = config.get("fear", {})
    vix_filter_active = bool(
        vix
        and (
            vix["value"] >= float(fear.get("fear_threshold", 30.0))
            or (vix.get("change_pct_5d") is not None and vix["change_pct_5d"] >= float(fear.get("spike_5d_pct", 20.0)))
        )
    )

    for result in results:
        if result.get("error"):
            continue
        if result.get("position") and vix_filter_active:
            position_signal = make_signal(
                "VIX_POSITION_RISK",
                "위험" if vix and vix["value"] >= float(fear.get("panic_threshold", 40.0)) else "주의",
                "POSITION",
                f"VIX {vix['value']:.1f} 구간이라 보유 포지션 변동성 점검이 필요합니다.",
                "risk",
            )
            apply_alert_preferences([position_signal], config)
            if position_signal["delivery"] != "off":
                result["signals"].append(position_signal)
            if LEVEL_RANK.get(result.get("alert_level", "정상"), 0) < LEVEL_RANK.get(position_signal["level"], 0):
                result["alert_level"] = position_signal["level"]
            result["summary"] += " VIX 공포지수 때문에 보유 리스크 점검이 필요합니다."
            continue
        if result.get("position"):
            continue
        if (regime == "risk_off" or vix_filter_active) and result.get("alert_level") in {"기회후보", "돌파후보"}:
            reason = "시장 리스크오프와 VIX 공포 구간" if regime == "risk_off" and vix_filter_active else "시장 리스크오프" if regime == "risk_off" else "VIX 공포 구간"
            downgrade = make_signal("MARKET_FILTER_DOWNGRADE", "주의", "MARKET", f"{reason}이라 기회 신호를 낮춰 봅니다.", "risk")
            apply_alert_preferences([downgrade], config)
            if downgrade["delivery"] != "off":
                result["signals"].append(downgrade)
            result["alert_level"] = "주의"
            result["summary"] += " 시장/VIX 필터 때문에 신호 등급을 낮췄습니다."

    for result in results:
        if not result.get("error"):
            result["score"] = build_signal_score(result.get("signals", []), result.get("position"), result.get("alert_level", "대기"), result.get("score_context", []))

    return {
        "regime": regime,
        "label": label,
        "level": level,
        "summary": summary,
        "spy_above_ma120": spy_above,
        "qqq_above_ma120": qqq_above,
        "spy_ma120_distance_pct": spy_ma120_distance,
        "qqq_ma120_distance_pct": qqq_ma120_distance,
        "vix": vix,
        "signals": [signal for signal in market_signals if signal["delivery"] != "off"],
    }


def build_vix_state(vix_history: dict[str, Any] | None, config: dict[str, Any]) -> dict[str, Any] | None:
    if not vix_history:
        return None
    bars = [bar for bar in vix_history.get("bars", []) if bar.get("close") is not None]
    if not bars:
        return None
    latest = bars[-1]
    value = float(latest["close"])
    compare = bars[-6] if len(bars) >= 6 else bars[0]
    compare_value = float(compare["close"])
    change_5d = (value / compare_value - 1) * 100 if compare_value else None
    fear = config.get("fear", {})
    elevated = float(fear.get("elevated_threshold", 20.0))
    fear_threshold = float(fear.get("fear_threshold", 30.0))
    panic = float(fear.get("panic_threshold", 40.0))
    if value >= panic:
        label = "극단공포"
        level = "위험"
    elif value >= fear_threshold:
        label = "공포"
        level = "위험"
    elif value >= elevated:
        label = "주의"
        level = "주의"
    else:
        label = "보통"
        level = "정상"
    source = str(vix_history.get("source", "unknown"))
    fallback = bool(vix_history.get("fallback", False))
    latest_time = str(latest.get("time", ""))
    return {
        "value": round(value, 2),
        "label": label,
        "level": level,
        "change_pct_5d": round(change_5d, 2) if change_5d is not None else None,
        "latest_time": latest_time,
        "source": source,
        "fallback": fallback,
        "cadence": "daily_close" if source in {"cboe", "fred"} else "demo",
        "freshness_label": vix_freshness_label(latest_time),
        "data_note": vix_data_note(source, fallback),
        "error": vix_history.get("error", ""),
        "fallback_from": vix_history.get("fallback_from", ""),
        "fallback_reason": vix_history.get("fallback_reason", ""),
        "thresholds": {
            "elevated": elevated,
            "fear": fear_threshold,
            "panic": panic,
        },
    }


def vix_freshness_label(latest_time: str) -> str:
    latest_date = parse_bar_date(latest_time)
    if latest_date is None:
        return "기준일 확인 필요"
    days = (datetime.now(timezone.utc).date() - latest_date).days
    if days <= 0:
        return "오늘 기준"
    if days == 1:
        return "전일 종가"
    return f"{days}일 전 종가"


def vix_data_note(source: str, fallback: bool) -> str:
    if source == "demo" and fallback:
        return "데모 대체값"
    if source == "cboe":
        return "CBOE 공식 일봉 종가 · 장중 실시간 아님"
    if source == "fred":
        suffix = " · CBOE 대체" if fallback else ""
        return f"FRED 일봉 종가{suffix} · 장중 실시간 아님"
    if source == "demo":
        return "데모 데이터"
    return source


def add_vix_signals(signals: list[dict[str, Any]], vix: dict[str, Any], config: dict[str, Any]) -> None:
    fear = config.get("fear", {})
    value = float(vix["value"])
    change_5d = vix.get("change_pct_5d")
    elevated = float(fear.get("elevated_threshold", 20.0))
    fear_threshold = float(fear.get("fear_threshold", 30.0))
    panic = float(fear.get("panic_threshold", 40.0))
    spike = float(fear.get("spike_5d_pct", 20.0))
    calming = float(fear.get("calming_5d_pct", -12.0))

    if value >= panic:
        signals.append(make_signal("VIX_PANIC", "위험", "MARKET", f"VIX가 {value:.1f}로 극단공포 구간입니다.", "risk"))
    elif value >= fear_threshold:
        signals.append(make_signal("VIX_FEAR", "위험", "MARKET", f"VIX가 {value:.1f}로 공포 구간입니다.", "risk"))
    elif value >= elevated:
        signals.append(make_signal("VIX_ELEVATED", "주의", "MARKET", f"VIX가 {value:.1f}로 변동성 주의 구간입니다.", "risk"))

    if change_5d is not None and change_5d >= spike:
        signals.append(make_signal("VIX_SPIKE", "위험", "MARKET", f"VIX가 5거래일 동안 {change_5d:+.1f}% 급등했습니다.", "risk"))
    if change_5d is not None and change_5d <= calming and value < fear_threshold:
        signals.append(make_signal("VIX_CALMING", "관심", "MARKET", f"VIX가 5거래일 동안 {change_5d:+.1f}% 하락해 공포가 진정 중입니다.", "review"))


def result_by_symbol(results: list[dict[str, Any]], symbol: str) -> dict[str, Any] | None:
    for result in results:
        if result.get("symbol") == symbol:
            return result
    return None


def is_above_ma(result: dict[str, Any] | None, period: str) -> bool | None:
    if not result or result.get("error"):
        return None
    ma = result.get("sma", {}).get(period)
    price = result.get("price")
    if ma is None or price is None:
        return None
    return float(price) >= float(ma)


def distance_from_ma(result: dict[str, Any] | None, period: str) -> float | None:
    if not result or result.get("error"):
        return None
    ma = result.get("sma", {}).get(period)
    price = result.get("price")
    if ma is None or price is None or float(ma) == 0:
        return None
    return round((float(price) / float(ma) - 1) * 100, 2)


def build_summary(
    symbol: str,
    close: float,
    latest_rsi: float | None,
    ma_snapshot: dict[str, float | None],
    volume_ratio: float | None,
    alert_level: str,
    position_metrics: dict[str, Any] | None,
) -> str:
    rsi_text = "RSI 데이터 부족" if latest_rsi is None else f"RSI {latest_rsi:.1f}"
    trend_parts: list[str] = []
    for period in ("20", "60", "120"):
        ma = ma_snapshot.get(period)
        if ma is not None:
            trend_parts.append(f"{period}일선 위" if close >= ma else f"{period}일선 아래")
    volume_text = "거래량 평균권" if volume_ratio is None or volume_ratio < 1.5 else f"거래량 {volume_ratio:.1f}배"
    prefix = f"{symbol}: 종가 ${close:.2f}, {rsi_text}, {', '.join(trend_parts)}, {volume_text}."
    if position_metrics and not position_metrics.get("missing_average_entry"):
        return_pct = position_metrics["return_pct"]
        action = position_metrics["suggested_action"]
        return f"{prefix} 보유 수익률 {return_pct:+.1f}%, 검토 상태는 {action}입니다."
    return f"{prefix} 현재 등급은 {alert_level}입니다."
