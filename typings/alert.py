from typing import TypedDict

from typings.enums import Exchange, Timeframe


class IAlert(TypedDict):
    key: str
    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    candle_len: int
    delta: int
