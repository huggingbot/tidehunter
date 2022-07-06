import asyncio

from constants import MAX_CANDLE_LEN
from modules.store.alerter import Alerter
from modules.store.main import Store
from utils.alert import get_timeframe_from_alert_key
from utils.candlestick import (
    get_latest_complete_candlestick_start_time,
    get_latest_incomplete_candlestick_start_time,
    interval_in_ms,
)
from utils.decorators import set_interval


class GarbageCleaner:
    store: Store
    alerter: Alerter

    def __init__(self, store: Store, alerter: Alerter):
        self.store = store
        self.alerter = alerter

    async def start(self) -> None:
        asyncio.create_task(self.on_tick())

    @set_interval(interval_in_seconds=10, interval_type="dynamic")
    async def on_tick(self) -> None:
        self.clean_store()
        self.clean_alerter()

    def clean_store(self) -> None:
        volume_keys = []
        data = self.store.data
        for exchange, symbols in data.items():
            for symbol, timeframes in symbols.items():
                for timeframe, volumes in timeframes.items():
                    current_first_time = next(iter(volumes))
                    latest_candle_start_time = (
                        get_latest_incomplete_candlestick_start_time(timeframe)
                    )
                    default_start_time = latest_candle_start_time - (
                        interval_in_ms(timeframe) * MAX_CANDLE_LEN[timeframe]
                    )

                    # An old item is present in the ordered dict
                    if default_start_time > current_first_time:
                        volume_keys.append(
                            (exchange, symbol, timeframe, current_first_time)
                        )

        for exchange, symbol, timeframe, timestamp in volume_keys:
            del self.store.data[exchange][symbol][timeframe][timestamp]

    def clean_alerter(self) -> None:
        alert_keys = []
        last_alerts = self.alerter.last_alerts
        for key, timestamp in last_alerts.items():
            timeframe = get_timeframe_from_alert_key(key)
            complete_candle_start_time = get_latest_complete_candlestick_start_time(
                timeframe
            )
            if complete_candle_start_time > timestamp:
                alert_keys.append(key)
        for alert_key in alert_keys:
            del self.alerter.last_alerts[alert_key]
