from typing import Optional

from sqlmodel import Session, select
from telegram.ext import CallbackContext
from telegram.update import Update

import modules.exchange
from constants import (
    MAX_CANDLE_LEN,
    MAX_DELTA_PERCENT,
    MIN_CANDLE_LEN,
    MIN_DELTA_PERCENT,
    SUBSCRIBE_ARGS_LEN,
)
from models.main import Alert, User
from typings.enums import Exchange, Timeframe, UserRole


def gen_alert_key(
    exchange: str, symbol: str, timeframe: str, candle_len: int, delta: int
) -> str:
    return f"{exchange}_{symbol}_{timeframe}_{candle_len}_{delta}"


def validate_is_admin(
    session: Session, username: str, update: Update
) -> Optional[User]:
    assert update.message is not None

    statement = (
        select(User).where(User.username == username).where(User.role == UserRole.Admin)
    )
    user = session.exec(statement).first()
    if user is None:
        update.message.reply_text(f"User {username} is not an admin")
        return None
    return user


def validate_user_present(
    session: Session, username: str, update: Update
) -> Optional[User]:
    assert update.message is not None

    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if user is None:
        update.message.reply_text(f"User {username} does not exist")
        return None
    return user


def validate_user_absent(session: Session, username: str, update: Update) -> bool:
    assert update.message is not None

    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if user is not None:
        update.message.reply_text(f"User {username} already exists")
        return False
    return True


def validate_alert_present(
    session: Session, key: str, update: Update
) -> Optional[Alert]:
    assert update.message is not None

    statement = select(Alert).where(Alert.key == key)
    alert = session.exec(statement).first()
    if alert is None:
        update.message.reply_text(f"Alert {key} does not exist")
        return None
    return alert


def validate_args_len(update: Update, context: CallbackContext) -> Optional[int]:
    assert update.message is not None
    assert context.args is not None

    if len(context.args) != SUBSCRIBE_ARGS_LEN:
        update.message.reply_text(
            f"Invalid number of arguments, expected {SUBSCRIBE_ARGS_LEN}"
        )
        return None
    return SUBSCRIBE_ARGS_LEN


def validate_exchange(update: Update, context: CallbackContext) -> Optional[str]:
    assert update.message is not None
    assert context.args is not None

    exchange = context.args[0].lower()
    exchange_list = [item for item in Exchange]
    if exchange not in exchange_list:
        update.message.reply_text(
            f"Invalid exchange given. Supported exchanges: {exchange_list}"
        )
        return None
    return exchange


def validate_symbol(update: Update, context: CallbackContext) -> Optional[str]:
    assert update.message is not None
    assert context.args is not None

    exchange = context.args[0].lower()
    symbol = str(context.args[1].upper())
    info = modules.exchange.exchanges[exchange].client.get_symbol_info(symbol)
    if info is None:
        update.message.reply_text(f"Invalid symbol given")
        return None
    return symbol.lower()


def validate_timeframe(update: Update, context: CallbackContext) -> Optional[str]:
    assert update.message is not None
    assert context.args is not None

    timeframe = context.args[2].lower()
    timeframes = [item for item in Timeframe]
    if timeframe not in timeframes:
        update.message.reply_text(
            f"Invalid timeframe given. Supported timeframes: {timeframes}"
        )
        return None
    return timeframe


def validate_candle_len(update: Update, context: CallbackContext) -> Optional[int]:
    assert update.message is not None
    assert context.args is not None

    timeframe = context.args[2].lower()
    try:
        candle_len = int(context.args[3])
        assert MIN_CANDLE_LEN <= candle_len <= MAX_CANDLE_LEN[timeframe]
        return candle_len
    except (ValueError, AssertionError):
        update.message.reply_text(
            f"Invalid candle length given. "
            f"Supported range for {timeframe}: {MIN_CANDLE_LEN} to {MAX_CANDLE_LEN[timeframe]}"
        )
    return None


def validate_delta(update: Update, context: CallbackContext) -> Optional[int]:
    assert update.message is not None
    assert context.args is not None

    try:
        delta = int(context.args[4])
        assert delta != 0
        assert MIN_DELTA_PERCENT <= delta <= MAX_DELTA_PERCENT
        return delta
    except (ValueError, AssertionError):
        update.message.reply_text(
            f"Invalid delta given. Supported range: {MIN_DELTA_PERCENT} to {MAX_DELTA_PERCENT} excluding 0"
        )
    return None
