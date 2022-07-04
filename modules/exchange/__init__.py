from modules.exchange.binance_socket_exchange import BinanceExchange
from typings.enums import Exchange

exchanges = {Exchange.Binance: BinanceExchange()}
