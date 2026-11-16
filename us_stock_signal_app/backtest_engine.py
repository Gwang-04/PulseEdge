from __future__ import annotations

from copy import deepcopy
from statistics import mean, median
from typing import Any

from signal_engine import analyze_symbol, parse_bar_date, sma, support_resistance_levels

HORIZONS = (5, 20, 60, 90)
MIN_HISTORY_BARS = 140
BACKTEST_RULES: dict[str, dict[str, Any]] = {
    "hold90": {
        "key": "hold90",
        "label": "90일 보유형",
        "entry": "next_open",
        "hard_stop_enabled": False,
        "profit_targets_enabled": False,
        "trailing_enabled": False,
        "max_holding_days": 90,
    },
    "balanced": {
        "key": "balanced",
        "label": "균형형",
        "entry": "next_open",
        "hard_stop_enabled": True,
        "profit_targets_enabled": True,
        "trailing_enabled": True,
        "stop_loss_pct": -7.0,
        "target_1_pct": 12.0,
        "target_1_sell_pct": 30.0,
        "target_2_pct": 20.0,
        "target_2_sell_pct": 30.0,
        "trailing_stop_pct": -8.0,
        "max_holding_days": 60,
    },
    "growth": {
        "key": "growth",
        "label": "수익형",
        "entry": "next_open",
        "hard_stop_enabled": True,
        "profit_targets_enabled": True,
        "trailing_enabled": True,
        "stop_loss_pct": -8.0,
        "target_1_pct": 15.0,
        "target_1_sell_pct": 25.0,
        "target_2_pct": 25.0,
        "target_2_sell_pct": 25.0,
        "trailing_stop_pct": -10.0,
        "max_holding_days": 90,
    },
    "growth_structure": {
        "key": "growth_structure",
        "label": "수익형+구조손절",
        "entry": "next_open",
        "hard_stop_enabled": True,
        "profit_targets_enabled": True,
        "trailing_enabled": True,
        "stop_loss_pct": -8.0,
        "target_1_pct": 15.0,
        "target_1_sell_pct": 25.0,
        "target_2_pct": 25.0,
        "target_2_sell_pct": 25.0,
        "trailing_stop_pct": -10.0,
        "max_holding_days": 90,
        "structure_stop_enabled": True,
        "structure_support_tolerance_pct": 1.0,
        "structure_volume_multiple": 1.5,
        "structure_loss_confirm_pct": -6.0,
    },
}
DEFAULT_RULE_KEY = "hold90"


def backtest_symbol_signals(
    symbol: str,
    bars: list[dict[str, Any]],
    config: dict[str, Any],
    min_score: int = 70,
    lookback: int = 252,
    cooldown_days: int = 10,
    rule_key: str = DEFAULT_RULE_KEY,
) -> dict[str, Any]:
    min_score = clamp_int(min_score, 0, 100)
    lookback = clamp_int(lookback, 60, 720)
    cooldown_days = clamp_int(cooldown_days, 1, 60)
    rule = selected_rule(rule_key)
    lookahead_days = max(max(HORIZONS), int(rule["max_holding_days"]))
    if len(bars) < MIN_HISTORY_BARS + lookahead_days:
        return empty_backtest(symbol, min_score, lookback, cooldown_days, len(bars), rule)

    test_config = deepcopy(config)
    test_config["positions"] = []
    end_index = len(bars) - lookahead_days
    start_index = max(MIN_HISTORY_BARS - 1, end_index - lookback)
    events: list[dict[str, Any]] = []
    next_allowed_index = start_index

    for index in range(start_index, end_index):
        if index < next_allowed_index:
            continue
        result = analyze_symbol(symbol, bars[: index + 1], test_config)
        score = result.get("score", {})
        score_value = int(score.get("value", 0))
        if score_value < min_score:
            continue
        events.append(build_event(symbol, bars, index, result, rule))
        next_allowed_index = index + cooldown_days

    return {
        "symbol": symbol,
        "mode": "watch",
        "rule_key": rule["key"],
        "min_score": min_score,
        "lookback": lookback,
        "cooldown_days": cooldown_days,
        "horizons": list(HORIZONS),
        "bars": len(bars),
        "evaluated_days": max(0, end_index - start_index),
        "summary": summarize_events(events),
        "events": events[-30:][::-1],
        "rule": rule,
        "rules": list(BACKTEST_RULES.values()),
        "note": f"{rule_note(rule)} 시장/VIX 필터의 과거 재현은 아직 제외했습니다.",
    }


def build_event(symbol: str, bars: list[dict[str, Any]], index: int, result: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    entry_index = index + 1
    entry_price = float(bars[entry_index]["open"])
    event_date = parse_bar_date(str(bars[index].get("time", "")))
    entry_date = parse_bar_date(str(bars[entry_index].get("time", "")))
    returns = {f"{horizon}d": fixed_holding_return(bars, entry_index, horizon) for horizon in HORIZONS}
    drawdowns = {
        "20d": max_drawdown(bars, entry_index, 20),
        "60d": max_drawdown(bars, entry_index, 60),
    }
    score = result.get("score", {})
    return {
        "symbol": symbol,
        "index": index,
        "date": event_date.isoformat() if event_date else str(bars[index].get("time", ""))[:10],
        "signal_price": round(float(bars[index]["close"]), 4),
        "entry_index": entry_index,
        "entry_date": entry_date.isoformat() if entry_date else str(bars[entry_index].get("time", ""))[:10],
        "entry_price": round(entry_price, 4),
        "price": round(entry_price, 4),
        "score": {
            "value": int(score.get("value", 0)),
            "stage": score.get("stage", ""),
            "label": score.get("label", "매수점수"),
        },
        "alert_level": result.get("alert_level", "대기"),
        "rsi14": result.get("rsi14"),
        "volume_ratio": result.get("volume_ratio"),
        "returns": returns,
        "max_drawdown": drawdowns,
        "rule_result": simulate_rule_trade(bars, entry_index, rule),
        "signals": compact_signals(result.get("signals", [])),
        "drivers": result.get("score", {}).get("drivers", [])[:4],
    }


def compact_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": signal.get("type", ""),
            "level": signal.get("level", ""),
            "message": signal.get("message", ""),
        }
        for signal in signals[:4]
    ]


def fixed_holding_return(bars: list[dict[str, Any]], entry_index: int, horizon: int) -> float | None:
    target_index = entry_index + horizon - 1
    if target_index >= len(bars):
        return None
    entry_price = float(bars[entry_index]["open"])
    if entry_price <= 0:
        return None
    exit_price = float(bars[target_index]["close"])
    return round((exit_price / entry_price - 1) * 100, 2)


def max_drawdown(bars: list[dict[str, Any]], entry_index: int, horizon: int) -> float | None:
    window = bars[entry_index : entry_index + horizon]
    if not window:
        return None
    entry_price = float(bars[entry_index]["open"])
    if entry_price <= 0:
        return None
    lowest_low = min(float(bar["low"]) for bar in window)
    return round((lowest_low / entry_price - 1) * 100, 2)


def simulate_recommended_trade(bars: list[dict[str, Any]], entry_index: int) -> dict[str, Any]:
    return simulate_rule_trade(bars, entry_index, selected_rule(DEFAULT_RULE_KEY))


def simulate_rule_trade(bars: list[dict[str, Any]], entry_index: int, rule: dict[str, Any]) -> dict[str, Any]:
    entry_price = float(bars[entry_index]["open"])
    max_days = int(rule["max_holding_days"])
    hard_stop_enabled = bool(rule.get("hard_stop_enabled", True))
    profit_targets_enabled = bool(rule.get("profit_targets_enabled", True))
    trailing_enabled = bool(rule.get("trailing_enabled", True))
    stop_price = entry_price * (1 + float(rule.get("stop_loss_pct", 0)) / 100) if hard_stop_enabled else None
    target_1_price = entry_price * (1 + float(rule.get("target_1_pct", 0)) / 100) if profit_targets_enabled else None
    target_2_price = entry_price * (1 + float(rule.get("target_2_pct", 0)) / 100) if profit_targets_enabled else None
    target_1_fraction = float(rule.get("target_1_sell_pct", 0)) / 100 if profit_targets_enabled else 0.0
    target_2_fraction = float(rule.get("target_2_sell_pct", 0)) / 100 if profit_targets_enabled else 0.0
    trailing_pct = float(rule.get("trailing_stop_pct", 0)) if trailing_enabled else 0.0
    end_index = min(len(bars) - 1, entry_index + max_days - 1)
    remaining = 1.0
    realized_return = 0.0
    realized_parts: list[dict[str, Any]] = []
    target_1_done = False
    target_2_done = False
    trailing_start_index: int | None = None
    pending_structure_exit: dict[str, Any] | None = None
    highest_high = entry_price
    lowest_low = entry_price

    for index in range(entry_index, end_index + 1):
        bar = bars[index]
        open_price = float(bar["open"])
        high = float(bar["high"])
        low = float(bar["low"])

        if remaining > 0 and pending_structure_exit and index == pending_structure_exit["exit_index"]:
            return close_trade(
                bars,
                entry_index,
                index,
                entry_price,
                open_price,
                pending_structure_exit["reason"],
                remaining,
                realized_return,
                realized_parts,
                lowest_low,
                structure_exit=pending_structure_exit,
            )

        highest_high = max(highest_high, high)
        lowest_low = min(lowest_low, low)

        if remaining > 0 and stop_price is not None and open_price <= stop_price:
            return close_trade(
                bars,
                entry_index,
                index,
                entry_price,
                open_price,
                "갭손절",
                remaining,
                realized_return,
                realized_parts,
                lowest_low,
            )
        if remaining > 0 and stop_price is not None and low <= stop_price:
            return close_trade(
                bars,
                entry_index,
                index,
                entry_price,
                stop_price,
                "손절",
                remaining,
                realized_return,
                realized_parts,
                lowest_low,
            )

        if remaining > 0 and target_1_price is not None and not target_1_done and high >= target_1_price:
            fraction = min(target_1_fraction, remaining)
            realized_return += weighted_return(entry_price, target_1_price, fraction)
            remaining -= fraction
            target_1_done = True
            trailing_start_index = index + 1
            realized_parts.append(profit_part("1차익절", fraction, target_1_price, entry_price, index, bars))
        if remaining > 0 and target_2_price is not None and not target_2_done and high >= target_2_price:
            fraction = min(target_2_fraction, remaining)
            realized_return += weighted_return(entry_price, target_2_price, fraction)
            remaining -= fraction
            target_2_done = True
            realized_parts.append(profit_part("2차익절", fraction, target_2_price, entry_price, index, bars))

        if remaining > 0 and trailing_enabled and target_1_done and trailing_start_index is not None and index >= trailing_start_index:
            trailing_price = highest_high * (1 + trailing_pct / 100)
            if low <= trailing_price:
                return close_trade(
                    bars,
                    entry_index,
                    index,
                    entry_price,
                    trailing_price,
                    "트레일링",
                    remaining,
                    realized_return,
                    realized_parts,
                    lowest_low,
                    trailing_price=trailing_price,
                )

        if remaining > 0 and index < end_index and pending_structure_exit is None:
            pending_structure_exit = structure_exit_signal(bars, entry_index, index, entry_price, rule)

    exit_price = float(bars[end_index]["close"])
    return close_trade(
        bars,
        entry_index,
        end_index,
        entry_price,
        exit_price,
        f"{max_days}일종료",
        remaining,
        realized_return,
        realized_parts,
        lowest_low,
    )


def close_trade(
    bars: list[dict[str, Any]],
    entry_index: int,
    exit_index: int,
    entry_price: float,
    exit_price: float,
    reason: str,
    remaining: float,
    realized_return: float,
    realized_parts: list[dict[str, Any]],
    lowest_low: float,
    trailing_price: float | None = None,
    structure_exit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if remaining > 0:
        realized_return += weighted_return(entry_price, exit_price, remaining)
    exit_date = parse_bar_date(str(bars[exit_index].get("time", "")))
    return {
        "return_pct": round(realized_return, 2),
        "exit_reason": reason,
        "exit_index": exit_index,
        "exit_date": exit_date.isoformat() if exit_date else str(bars[exit_index].get("time", ""))[:10],
        "exit_price": round(exit_price, 4),
        "holding_days": exit_index - entry_index + 1,
        "remaining_exit_pct": round(remaining * 100, 1),
        "max_drawdown_pct": round((lowest_low / entry_price - 1) * 100, 2),
        "target_1_hit": any(part["label"] == "1차익절" for part in realized_parts),
        "target_2_hit": any(part["label"] == "2차익절" for part in realized_parts),
        "trailing_stop_price": round(trailing_price, 4) if trailing_price is not None else None,
        "structure_stop_hit": bool(structure_exit),
        "structure_reason": structure_exit.get("detail", "") if structure_exit else "",
        "parts": realized_parts,
    }


def structure_exit_signal(
    bars: list[dict[str, Any]],
    entry_index: int,
    index: int,
    entry_price: float,
    rule: dict[str, Any],
) -> dict[str, Any] | None:
    if not rule.get("structure_stop_enabled") or index <= entry_index:
        return None
    close = float(bars[index]["close"])
    previous_close = float(bars[index - 1]["close"])
    return_pct = (close / entry_price - 1) * 100
    closes = [float(bar["close"]) for bar in bars[: index + 1]]
    sma60 = sma(closes, 60)
    current_ma60 = sma60[index] if index < len(sma60) else None
    previous_ma60 = sma60[index - 1] if index - 1 < len(sma60) else None
    below_ma60 = current_ma60 is not None and close < current_ma60
    below_ma60_two_days = below_ma60 and previous_ma60 is not None and previous_close < previous_ma60
    volume_ratio = volume_ratio_at(bars, index)
    down_volume = volume_ratio is not None and volume_ratio >= float(rule.get("structure_volume_multiple", 1.5)) and close < previous_close
    loss_confirmed = return_pct <= float(rule.get("structure_loss_confirm_pct", -6.0))
    entry_date = parse_bar_date(str(bars[entry_index].get("time", "")))
    previous_levels = support_resistance_levels(
        "BACKTEST",
        bars[:index],
        previous_close,
        entry_date=entry_date.isoformat() if entry_date else None,
        average_entry_price=entry_price,
    )
    previous_support = previous_levels.get("nearest_support") if previous_levels.get("scope") == "position" else None
    tolerance_pct = float(rule.get("structure_support_tolerance_pct", 1.0))
    support_break = bool(previous_support and close < float(previous_support["price"]) * (1 - tolerance_pct / 100))

    reason = ""
    detail = ""
    if support_break and loss_confirmed:
        reason = "구조손절"
        support_price = float(previous_support["price"]) if previous_support else 0.0
        detail = f"S1 ${support_price:.2f} 이탈"
        if below_ma60 and down_volume:
            reason = "위험구조손절"
            detail += f" + 60일선 이탈 + 거래량 {volume_ratio:.1f}배"
        elif below_ma60:
            detail += " + 60일선 이탈"
        elif down_volume:
            detail += f" + 거래량 {volume_ratio:.1f}배"
        elif loss_confirmed:
            detail += f" + 손실 {return_pct:.1f}%"
    elif below_ma60_two_days and loss_confirmed:
        reason = "추세손절"
        detail = f"60일선 2거래일 연속 이탈 + 손실 {return_pct:.1f}%"

    if not reason:
        return None
    exit_index = min(index + 1, len(bars) - 1)
    return {
        "signal_index": index,
        "exit_index": exit_index,
        "reason": reason,
        "detail": detail,
    }


def volume_ratio_at(bars: list[dict[str, Any]], index: int, period: int = 20) -> float | None:
    if index < period:
        return None
    previous_volumes = [float(bar.get("volume", 0)) for bar in bars[index - period : index]]
    average_volume = mean(previous_volumes) if previous_volumes else 0
    if average_volume <= 0:
        return None
    return float(bars[index].get("volume", 0)) / average_volume


def weighted_return(entry_price: float, exit_price: float, fraction: float) -> float:
    return (exit_price / entry_price - 1) * 100 * fraction


def profit_part(label: str, fraction: float, price: float, entry_price: float, index: int, bars: list[dict[str, Any]]) -> dict[str, Any]:
    event_date = parse_bar_date(str(bars[index].get("time", "")))
    return {
        "label": label,
        "date": event_date.isoformat() if event_date else str(bars[index].get("time", ""))[:10],
        "sell_pct": round(fraction * 100, 1),
        "price": round(price, 4),
        "return_pct": round((price / entry_price - 1) * 100, 2),
    }


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"signals": len(events)}
    rule_returns = numeric_values(event.get("rule_result", {}).get("return_pct") for event in events)
    rule_drawdowns = numeric_values(event.get("rule_result", {}).get("max_drawdown_pct") for event in events)
    holding_days = numeric_values(event.get("rule_result", {}).get("holding_days") for event in events)
    exit_reasons = [str(event.get("rule_result", {}).get("exit_reason", "")) for event in events]
    summary["avg_rule_return"] = round(mean(rule_returns), 2) if rule_returns else None
    summary["median_rule_return"] = round(median(rule_returns), 2) if rule_returns else None
    summary["win_rate_rule"] = round(sum(1 for value in rule_returns if value > 0) / len(rule_returns) * 100, 1) if rule_returns else None
    summary["best_rule_return"] = round(max(rule_returns), 2) if rule_returns else None
    summary["worst_rule_return"] = round(min(rule_returns), 2) if rule_returns else None
    summary["avg_rule_mdd"] = round(mean(rule_drawdowns), 2) if rule_drawdowns else None
    summary["avg_holding_days"] = round(mean(holding_days), 1) if holding_days else None
    summary["stop_count"] = sum(1 for reason in exit_reasons if reason in {"손절", "갭손절"})
    summary["structure_stop_count"] = sum(1 for reason in exit_reasons if "구조손절" in reason or reason == "추세손절")
    summary["risk_structure_stop_count"] = exit_reasons.count("위험구조손절")
    summary["trailing_count"] = exit_reasons.count("트레일링")
    summary["time_exit_count"] = sum(1 for reason in exit_reasons if reason.endswith("일종료"))
    summary["target_1_count"] = sum(1 for event in events if event.get("rule_result", {}).get("target_1_hit"))
    summary["target_2_count"] = sum(1 for event in events if event.get("rule_result", {}).get("target_2_hit"))
    for horizon in HORIZONS:
        key = f"{horizon}d"
        values = numeric_values(event.get("returns", {}).get(key) for event in events)
        summary[f"avg_return_{key}"] = round(mean(values), 2) if values else None
        summary[f"median_return_{key}"] = round(median(values), 2) if values else None
        summary[f"win_rate_{key}"] = round(sum(1 for value in values if value > 0) / len(values) * 100, 1) if values else None
        summary[f"sample_{key}"] = len(values)

    return_20d = numeric_values(event.get("returns", {}).get("20d") for event in events)
    drawdown_20d = numeric_values(event.get("max_drawdown", {}).get("20d") for event in events)
    drawdown_60d = numeric_values(event.get("max_drawdown", {}).get("60d") for event in events)
    scores = numeric_values(event.get("score", {}).get("value") for event in events)
    summary["best_return_20d"] = round(max(return_20d), 2) if return_20d else None
    summary["worst_return_20d"] = round(min(return_20d), 2) if return_20d else None
    summary["avg_max_drawdown_20d"] = round(mean(drawdown_20d), 2) if drawdown_20d else None
    summary["avg_max_drawdown_60d"] = round(mean(drawdown_60d), 2) if drawdown_60d else None
    summary["avg_score"] = round(mean(scores), 1) if scores else None
    return summary


def numeric_values(values: Any) -> list[float]:
    output: list[float] = []
    for value in values:
        if value is None:
            continue
        try:
            output.append(float(value))
        except (TypeError, ValueError):
            continue
    return output


def empty_backtest(symbol: str, min_score: int, lookback: int, cooldown_days: int, bar_count: int, rule: dict[str, Any] | None = None) -> dict[str, Any]:
    rule = rule or selected_rule(DEFAULT_RULE_KEY)
    lookahead_days = max(max(HORIZONS), int(rule["max_holding_days"]))
    return {
        "symbol": symbol,
        "mode": "watch",
        "rule_key": rule["key"],
        "min_score": min_score,
        "lookback": lookback,
        "cooldown_days": cooldown_days,
        "horizons": list(HORIZONS),
        "bars": bar_count,
        "evaluated_days": 0,
        "summary": summarize_events([]),
        "events": [],
        "rule": rule,
        "rules": list(BACKTEST_RULES.values()),
        "note": f"백테스트에는 최소 140개 과거 봉과 이후 {lookahead_days}거래일 결과가 필요합니다.",
    }


def selected_rule(rule_key: str) -> dict[str, Any]:
    key = str(rule_key or DEFAULT_RULE_KEY).lower()
    return deepcopy(BACKTEST_RULES.get(key, BACKTEST_RULES[DEFAULT_RULE_KEY]))


def rule_note(rule: dict[str, Any]) -> str:
    parts = [f"{rule['label']}룰: 다음 거래일 시가 진입"]
    if rule.get("hard_stop_enabled", True):
        parts.append(f"{float(rule['stop_loss_pct']):.0f}% 손절")
    if rule.get("profit_targets_enabled", True):
        parts.append(f"+{float(rule['target_1_pct']):.0f}% {float(rule['target_1_sell_pct']):.0f}% 익절")
        parts.append(f"+{float(rule['target_2_pct']):.0f}% {float(rule['target_2_sell_pct']):.0f}% 익절")
    if rule.get("trailing_enabled", True):
        parts.append(f"남은 물량은 {float(rule['trailing_stop_pct']):.0f}% 트레일링 또는 {int(rule['max_holding_days'])}거래일 종료")
    else:
        parts.append(f"중간 익절/손절 없이 {int(rule['max_holding_days'])}거래일 보유 후 종료")
    note = ", ".join(parts) + "."
    if rule.get("structure_stop_enabled"):
        loss_confirm = abs(float(rule.get("structure_loss_confirm_pct", -6.0)))
        note += f" 종가 기준 S1 1% 이탈과 -{loss_confirm:.0f}% 손실 확인이 겹치거나 60일선 2거래일 이탈에 -{loss_confirm:.0f}% 손실 확인이 붙으면 다음 거래일 시가 구조손절로 봅니다."
    return note


def clamp_int(value: int | float, minimum: int, maximum: int) -> int:
    return min(maximum, max(minimum, int(value)))
