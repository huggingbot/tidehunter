from datetime import datetime, timezone
from typing import Union

from typings.enums import Timeframe

CANDLESTICK_INTERVAL_MAP = {
    Timeframe.Min1: 60,
    Timeframe.Min3: 180,
    Timeframe.Min5: 300,
    Timeframe.Min15: 900,
    Timeframe.Min30: 1800,
    Timeframe.Hour1: 3600,
    Timeframe.Hour2: 7200,
    Timeframe.Hour4: 14400,
    Timeframe.Hour6: 21600,
    Timeframe.Hour8: 28800,
    Timeframe.Hour12: 43200,
    Timeframe.Day1: 86400,
    Timeframe.Day3: 259200,
    Timeframe.Week1: 604800,
}


def interval_in_ms(timeframe: Timeframe) -> int:
    return CANDLESTICK_INTERVAL_MAP[timeframe] * (10**3)


def get_candlestick_start_time(timestamp_in_ms: int, interval: Timeframe) -> int:
    return timestamp_in_ms - (timestamp_in_ms % interval_in_ms(interval))


def get_latest_incomplete_candlestick_start_time(interval: Timeframe) -> int:
    return get_candlestick_start_time(time_now_in_ms(), interval)


def get_latest_complete_candlestick_start_time(interval: Timeframe) -> int:
    return get_latest_incomplete_candlestick_start_time(interval) - interval_in_ms(
        interval
    )


def time_now_in_ms():
    """Returned current timestamp is offset-aware"""
    return date_to_timestamp(datetime.now(timezone.utc))


def date_to_timestamp(date: datetime):
    """Returned timestamp is offset-aware"""
    return int(
        (date - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds() * (10**3)
    )
