from collections import OrderedDict
from decimal import Decimal

from sqlmodel import Session, select

from constants import MAX_CANDLE_LEN
from models.main import Alert, engine
from modules.exchange import exchanges
from modules.store.main import Store
from typings.enums import Timeframe
from typings.exchange import ISocketEmit
from utils.candlestick import (
    get_latest_incomplete_candlestick_start_time,
    interval_in_ms,
)
from utils.event_emitter import EExchange, EStoreUpdater, ee


class StoreUpdater:
    store: Store

    def __init__(self, store: Store) -> None:
        self.store = store

        with Session(engine) as session:
            alerts = session.exec(select(Alert)).all()
            for a in alerts:
                self.on_add_store_alert(a)
                self.on_add_store_data(a)
        ee.on(EStoreUpdater.ON_ADD_STORE_ALERT, self.on_add_store_alert)
        ee.on(EStoreUpdater.ON_REMOVE_STORE_DATA, self.on_remove_store_alert)
        ee.on(EStoreUpdater.ON_ADD_STORE_DATA, self.on_add_store_data)
        ee.on(EStoreUpdater.ON_REMOVE_STORE_DATA, self.on_remove_store_data)
        ee.on(EExchange.CANDLESTICK_EVENT, self.on_candlestick_event)

    def on_add_store_alert(self, a: Alert) -> None:
        alerts = self.store.alerts
        alerts[a.key] = {
            "key": a.key,
            "exchange": a.exchange,
            "symbol": a.symbol,
            "timeframe": a.timeframe,
            "candle_len": a.candle_len,
            "delta": a.delta,
        }

    def on_remove_store_alert(self, a: Alert) -> None:
        alerts = self.store.alerts
        del alerts[a.key]

    def on_add_store_data(self, a: Alert) -> None:
        data = self.store.data
        if not data.get(a.exchange):
            data[a.exchange] = {}
        symbols: dict = data[a.exchange]
        if not symbols.get(a.symbol):
            symbols[a.symbol] = {}
        timeframes: dict = symbols[a.symbol]
        if not timeframes.get(a.timeframe):
            timeframes[a.timeframe] = OrderedDict()
        volumes: OrderedDict = timeframes[a.timeframe]

        # Add only absent data in the store
        if not len(volumes):
            timeframe = Timeframe(a.timeframe)
            latest_candle_start_time = get_latest_incomplete_candlestick_start_time(
                timeframe
            )
            start_time = latest_candle_start_time - (
                interval_in_ms(timeframe) * MAX_CANDLE_LEN[timeframe]
            )

            exchange = exchanges[a.exchange]
            klines = exchange.client.get_historical_klines(
                a.symbol.upper(), a.timeframe, start_time
            )
            for kline in klines:
                open_time: int = kline[0]
                volume = Decimal(kline[5])
                volumes[open_time] = volume
            self.add_socket(a)

    def add_socket(self, a: Alert) -> None:
        task_key = f"{a.symbol.upper()}_{a.timeframe}"
        exchange = exchanges[a.exchange]

        # Add only absent listener in the socket
        if exchange.tasks.get(task_key) is None:
            exchange.schedule_task(exchange.add_symbol, a.symbol, a.timeframe)

    def on_candlestick_event(self, socket_data: ISocketEmit) -> None:
        exchange = socket_data["exchange"]
        symbol = socket_data["symbol"]
        timeframe = socket_data["timeframe"]
        open_time = socket_data["open_time"]
        volume = socket_data["volume"]

        data = self.store.data
        data[exchange][symbol][timeframe][open_time] = volume

    def on_remove_store_data(self, a: Alert) -> None:
        with Session(engine) as session:
            statement = (
                select(Alert)
                .where(Alert.exchange == a.exchange)
                .where(Alert.symbol == a.symbol)
                .where(Alert.timeframe == a.timeframe)
            )
            alerts = session.exec(statement).all()

            # Remove OrderedDict if no associated alert
            if not len(alerts):
                self.remove_socket(a)
                data = self.store.data
                del data[a.exchange][a.symbol][a.timeframe]

    def remove_socket(self, a: Alert) -> None:
        task_key = f"{a.symbol.upper()}_{a.timeframe}"
        exchange = exchanges[a.exchange]

        # Remove only present listener in the socket
        if exchange.tasks.get(task_key) is not None:
            exchange.remove_symbol(a.symbol, a.timeframe)
