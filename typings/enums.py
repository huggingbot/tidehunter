from enum import Enum


class UserRole(str, Enum):
    User = "user"
    Admin = "admin"

    def __repr__(self):
        return self.value


class Exchange(str, Enum):
    Binance = "binance"

    def __repr__(self):
        return self.value


class Timeframe(str, Enum):
    Min1 = "1m"
    Min3 = "3m"
    Min5 = "5m"
    Min15 = "15m"
    Min30 = "30m"
    Hour1 = "1h"
    Hour2 = "2h"
    Hour4 = "4h"
    Hour6 = "6h"
    Hour8 = "8h"
    Hour12 = "12h"
    Day1 = "1d"
    Day3 = "3d"
    Week1 = "1w"
    # Month1 = '1M'

    def __repr__(self):
        return self.value
