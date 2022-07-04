from pyee import AsyncIOEventEmitter

ee = AsyncIOEventEmitter()


class EExchange:
    CANDLESTICK_EVENT = "CANDLESTICK_EVENT"


class EStoreUpdater:
    ON_ADD_STORE_ALERT = "ON_ADD_STORE_ALERT"
    ON_REMOVE_STORE_ALERT = "ON_REMOVE_STORE_ALERT"
    ON_ADD_STORE_DATA = "ON_ADD_STORE"
    ON_REMOVE_STORE_DATA = "ON_REMOVE_STORE"


class ETelegramEvent:
    STATS = "STATS"
