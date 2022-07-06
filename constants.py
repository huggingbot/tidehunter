from typing import Union

from typings.enums import Timeframe

SUBSCRIBE_ARGS_LEN = 5

MIN_CANDLE_LEN = 1
MAX_CANDLE_LEN: dict[Union[str, Timeframe], int] = {
    Timeframe.Min1: 1000,
    Timeframe.Min3: 1000,
    Timeframe.Min5: 1000,
    Timeframe.Min15: 500,
    Timeframe.Min30: 500,
    Timeframe.Hour1: 100,
    Timeframe.Hour2: 100,
    Timeframe.Hour4: 100,
    Timeframe.Hour6: 100,
    Timeframe.Hour8: 100,
    Timeframe.Hour12: 100,
    Timeframe.Day1: 50,
    Timeframe.Day3: 50,
    Timeframe.Week1: 10,
}

MIN_DELTA_PERCENT = 1
MAX_DELTA_PERCENT = 100
