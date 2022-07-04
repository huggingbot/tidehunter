from __future__ import annotations

from sqlmodel import Session, select
from telegram.ext import CallbackContext
from telegram.update import Update

import modules.telegram.telegram_bot
from core.loggings import telegram_logger as logger
from models.main import Alert, User, engine
from modules.telegram.command_validators import (
    gen_alert_key,
    validate_alert_present,
    validate_args_len,
    validate_candle_len,
    validate_delta,
    validate_exchange,
    validate_is_admin,
    validate_symbol,
    validate_timeframe,
    validate_user_absent,
    validate_user_present,
)
from typings.enums import UserRole
from utils.event_emitter import EStoreUpdater, ETelegramEvent, ee


class TelegramListener:
    def __init__(self, telegram_bot: modules.telegram.telegram_bot.TelegramBot):
        telegram_bot.on_command("help", self.help_command)
        telegram_bot.on_command("register", self.register_command)
        telegram_bot.on_command("deregister", self.deregister_command)
        telegram_bot.on_command("subscribe", self.subscribe_command)
        telegram_bot.on_command("unsubscribe", self.unsubscribe_command)
        telegram_bot.on_command("list_subscribed", self.list_subscribed_command)
        telegram_bot.on_command("stats", self.stats_command)

    def help_command(self, update: Update, context: CallbackContext) -> None:
        assert update.message is not None

        logger.info(update.message)
        msg = (
            f"/help for help message\n"
            f"/register to register user\n"
            f"/deregister to deregister user\n"
            f"/subscribe to subscribe to alerts\n"
            f"subscribe format: <exchange>_<symbol>_<timeframe>_<candle_len>_<delta>\n"
            f"subscribe example: /subscribe binance_bnbbtc_1h_50_100\n"
            f"/unsubscribe to unsubscribe to alerts\n"
            f"unsubscribe format: <exchange>_<symbol>_<timeframe>_<candle_len>_<delta>\n"
            f"unsubscribe example: /unsubscribe binance_bnbbtc_1h_50_100\n"
            f"/list_subscribed to list subscribed alerts\n"
            f"/stats for bot stats\n"
        )
        update.message.reply_text(msg)

    def register_command(self, update: Update, context: CallbackContext) -> None:
        assert update.message is not None
        assert context.args is not None

        with Session(engine) as session:
            admin_username = update.message.from_user.username
            if not len(context.args):
                return
            username = context.args[0]

            admin = validate_is_admin(session, admin_username, update)
            user_absent = validate_user_absent(session, username, update)
            if not admin or not user_absent:
                return
            user = User(username=username, role=UserRole.User)
            session.add(user)
            session.commit()
            update.message.reply_text(f"Successfully registered user {username}")

    def deregister_command(self, update: Update, context: CallbackContext) -> None:
        assert update.message is not None
        assert context.args is not None

        with Session(engine) as session:
            admin_username = update.message.from_user.username
            if not len(context.args):
                return
            username = context.args[0]

            admin = validate_is_admin(session, admin_username, update)
            user = validate_user_present(session, username, update)
            if not admin or user is None:
                return
            session.delete(user)
            session.commit()
            update.message.reply_text(f"Successfully deregistered user {username}")

    def subscribe_command(self, update: Update, context: CallbackContext) -> None:
        assert update.message is not None

        args_len = validate_args_len(update, context)
        if not args_len:
            return
        exchange = validate_exchange(update, context)
        if not exchange:
            return
        symbol = validate_symbol(update, context)
        if not symbol:
            return
        timeframe = validate_timeframe(update, context)
        if not timeframe:
            return
        candle_len = validate_candle_len(update, context)
        if not candle_len:
            return
        delta = validate_delta(update, context)
        if not delta:
            return

        with Session(engine) as session:
            username = update.message.from_user.username
            user = validate_user_present(session, username, update)
            if user is None:
                return

            key = gen_alert_key(exchange, symbol, timeframe, candle_len, delta)
            statement = select(Alert).where(Alert.key == key)
            alert = session.exec(statement).first()
            if alert is None:
                alert = Alert(
                    key=key,
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=timeframe,
                    candle_len=candle_len,
                    delta=delta,
                )

            alert.users.append(user)
            session.add(alert)
            session.commit()
            ee.emit(EStoreUpdater.ON_ADD_STORE_ALERT, alert)
            ee.emit(EStoreUpdater.ON_ADD_STORE_DATA, alert)
            update.message.reply_text(f"Successfully subscribed to alert {key}")

    def unsubscribe_command(self, update: Update, context: CallbackContext):
        assert update.message is not None

        args_len = validate_args_len(update, context)
        if not args_len:
            return
        exchange = validate_exchange(update, context)
        if not exchange:
            return
        symbol = validate_symbol(update, context)
        if not symbol:
            return
        timeframe = validate_timeframe(update, context)
        if not timeframe:
            return
        candle_len = validate_candle_len(update, context)
        if not candle_len:
            return
        delta = validate_delta(update, context)
        if not delta:
            return

        with Session(engine) as session:
            username = update.message.from_user.username
            user = validate_user_present(session, username, update)
            if user is None:
                return

            key = gen_alert_key(exchange, symbol, timeframe, candle_len, delta)
            alert = validate_alert_present(session, key, update)
            if alert is None:
                return
            alert.users.remove(user)

            # No user is associated with the current alert
            if len(alert.users) == 0:
                session.delete(alert)
                ee.emit(EStoreUpdater.ON_REMOVE_STORE_ALERT, alert)
                ee.emit(EStoreUpdater.ON_REMOVE_STORE_DATA, alert)
            else:
                session.add(alert)
            session.commit()
            update.message.reply_text(f"Successfully unsubscribed to alert {key}")

    def list_subscribed_command(self, update: Update, context: CallbackContext):
        assert update.message is not None

        with Session(engine) as session:
            username = update.message.from_user.username
            user = validate_user_present(session, username, update)
            if user is None:
                return

            msg = "Subscribed alerts:\n\n"
            for alert in user.alerts:
                msg += f"key: {alert.key}\n"
                msg += f"exchange: {alert.exchange}\n"
                msg += f"symbol: {alert.symbol}\n"
                msg += f"timeframe: {alert.timeframe}\n"
                msg += f"candle length: {alert.candle_len}\n"
                msg += f"delta: {alert.delta}\n\n"
            update.message.reply_text(msg)

    def stats_command(self, update, context: CallbackContext):
        assert update.message is not None

        with Session(engine) as session:
            admin_username = update.message.from_user.username

            admin = validate_is_admin(session, admin_username, update)
            if not admin:
                return

        text = str(update.message.text).lower()
        logger.info(f"User ({update.message.chat.id}) says: {text}")
        update.message.reply_text("CHECKING STATS...")
        ee.emit(ETelegramEvent.STATS, update.message.chat.id)
