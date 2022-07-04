from typings.enums import Timeframe


def get_timeframe_from_alert_key(key: str) -> Timeframe:
    return Timeframe(key.split("_")[2])
