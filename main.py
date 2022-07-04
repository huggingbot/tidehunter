import asyncio
import os

import nest_asyncio
from dotenv import load_dotenv

from core.loggings import logger
from models.main import create_db_and_tables
from modules.exchange import exchanges
from modules.store.alerter import Alerter
from modules.store.garbage_cleaner import GarbageCleaner
from modules.store.main import Store
from modules.store.store_updater import StoreUpdater
from modules.telegram.telegram_bot import telegram_bot
from typings.enums import Exchange

load_dotenv("./.env")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

nest_asyncio.apply()


async def main() -> None:
    logger.info("Starting main()")
    create_db_and_tables()

    telegram_bot.start_bot()
    await asyncio.gather(asyncio.to_thread(lambda: telegram_bot.run_bot()))

    exchange = exchanges[Exchange.Binance]
    await exchange.start(api_key=BINANCE_API_KEY, secret_key=BINANCE_SECRET_KEY)

    store = Store()
    StoreUpdater(store)
    alerter = Alerter(store)
    await alerter.start()
    garbage_cleaner = GarbageCleaner(store, alerter)
    await garbage_cleaner.start()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
