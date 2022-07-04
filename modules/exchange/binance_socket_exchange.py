import asyncio
from asyncio import Task
from decimal import Decimal
from typing import Any, Callable, Union

from binance import AsyncClient, BinanceSocketManager, Client

from modules.telegram.telegram_bot import telegram_bot
from typings.enums import Exchange, Timeframe
from typings.exchange import ICandlestickEvent
from utils.decorators import set_interval
from utils.event_emitter import EExchange, ETelegramEvent, ee


class BinanceExchange:
    tasks: dict[str, Task]
    callables: list[tuple]
    client: Client
    async_client: AsyncClient
    ws_client: BinanceSocketManager

    def __init__(self) -> None:
        self.tasks = {}
        self.callables = []
        ee.on(ETelegramEvent.STATS, self.stats_requested)

    async def start(self, api_key: str, secret_key: str) -> None:
        self.client = Client(api_key=api_key, api_secret=secret_key)
        self.async_client = await AsyncClient.create(
            api_key=api_key, api_secret=secret_key
        )
        self.ws_client = BinanceSocketManager(self.async_client)

        asyncio.create_task(self.scheduler())

    def stats_requested(self, chat_id: int) -> None:
        msg = (
            f"📊 EXCHANGE STATS\n"
            f"==========================\n"
            f"{'Sockets':<15}: {list(self.tasks)}\n"
            f"{'Pending calls':<15}: {self.callables}\n"
            f"==========================\n"
        )
        telegram_bot.send_message(chat_id=chat_id, message=msg)

    def schedule_task(self, *args: Union[list[Callable], list[Any]]) -> None:
        self.callables.append(args)

    @set_interval(2, "dynamic")
    async def scheduler(self) -> None:
        if len(self.callables):
            for call in self.callables:
                function = call[0]
                await function(*call[1:])
            self.callables = []

    async def add_symbol(self, symbol: str, interval: Union[str, Timeframe]) -> None:
        symbol_upper = symbol.upper()
        symbol_lower = symbol.lower()

        async def listen():
            ts = self.ws_client.kline_socket(symbol_upper, interval)

            async with ts as tscm:
                while True:
                    res: ICandlestickEvent = await tscm.recv()
                    ee.emit(
                        EExchange.CANDLESTICK_EVENT,
                        {
                            "exchange": Exchange.Binance,
                            "symbol": symbol_lower,
                            "timeframe": interval,
                            "open_time": res["k"]["t"],
                            "volume": Decimal(res["k"]["q"]),
                        },
                    )

        task = asyncio.create_task(listen())
        self.tasks[f"{symbol_upper}_{interval}"] = task

    def remove_symbol(self, symbol: str, interval: Union[str, Timeframe]) -> None:
        symbol_upper = symbol.upper()
        task = self.tasks[f"{symbol_upper}_{interval}"]
        task.cancel()
        del self.tasks[f"{symbol_upper}_{interval}"]

    async def close(self) -> None:
        self.client.close_connection()
        await self.async_client.close_connection()
