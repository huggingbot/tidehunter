from sqlmodel import Session, select

from models.main import User, UserAlertLink, engine
from modules.telegram.telegram_bot import telegram_bot
from typings.alert import IAlert
from utils.event_emitter import ETelegramEvent, ee


class Store:
    data: dict
    alerts: dict[str, IAlert]

    def __init__(self):
        self.data = {}
        self.alerts = {}
        ee.on(ETelegramEvent.STATS, self.stats_requested)

    def stats_requested(self, chat_id: int):
        users, user_alert_links = self.query_users()

        display_data: dict = {}
        for exchange, symbols in self.data.items():
            for symbol, timeframes in symbols.items():
                if not display_data.get(exchange):
                    display_data[exchange] = {}
                _symbols: dict = display_data[exchange]
                if not _symbols.get(symbol):
                    _symbols[symbol] = list(timeframes)

        msg = (
            f"📊 STORE STATS\n"
            f"==========================\n"
            f"{'Alerts':<15}: {list(self.alerts)}\n"
            f"{'Data':<15}: {display_data}\n"
            f"{'Users':<15}: {users}\n"
            f"{'UserAlertLinks':<15}: {user_alert_links}\n"
            f"==========================\n"
        )
        telegram_bot.send_message(chat_id=chat_id, message=msg)

    def query_users(self) -> tuple[list[User], list[UserAlertLink]]:
        with Session(engine) as session:
            users = session.exec(select(User)).all()
            user_alert_links = session.exec(select(UserAlertLink)).all()
            return users, user_alert_links
