from decimal import Decimal
from typing import TypedDict

from typings.enums import Exchange, Timeframe


class ICandlestickEventData(TypedDict):
    t: int  # Kline start time
    T: int  # Kline close time
    s: str  # Symbol
    i: str  # Interval
    f: int  # First trade ID
    L: int  # Last trade ID
    o: str  # Open price (float)
    c: str  # Close price (float)
    h: str  # High price (float)
    l: str  # Low price (float)
    v: str  # Base asset volume (float)
    n: int  # Number of trades
    x: bool  # Is this kline closed?
    q: str  # Quote asset volume (float)
    V: str  # Taker buy base asset volume (float)
    Q: str  # Taker buy quote asset volume (float)
    B: str  # Ignore


class ICandlestickEvent(TypedDict):
    e: str  # Event type
    E: int  # Event time
    s: str  # Symbol
    k: ICandlestickEventData


class ISocketEmit(TypedDict):
    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    open_time: int
    volume: Decimal
