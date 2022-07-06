import asyncio
from collections import OrderedDict
from datetime import datetime, timezone
from decimal import Decimal
from statistics import fmean

from modules.store.main import Store
from modules.telegram.telegram_bot import telegram_bot
from utils.decorators import set_interval
from utils.event_emitter import ETelegramEvent, ee


class Alerter:
    store: Store
    last_alerts: dict[str, int]

    def __init__(self, store: Store):
        self.store = store
        self.last_alerts = {}
        ee.on(ETelegramEvent.STATS, self.stats_requested)

    async def start(self) -> None:
        asyncio.create_task(self.on_tick())

    def stats_requested(self, chat_id: int):
        msg = (
            f"📊 ALERTER STATS\n"
            f"==========================\n"
            f"{'Last alerts':<15}: {self.last_alerts}\n"
            f"==========================\n"
        )
        telegram_bot.send_message(chat_id=chat_id, message=msg)

    @set_interval(interval_in_seconds=2, interval_type="dynamic")
    async def on_tick(self) -> None:
        data = self.store.data
        alerts = self.store.alerts
        for a in alerts.values():
            candle_len = a["candle_len"]
            delta_percent = Decimal(a["delta"]) / Decimal(100)

            volumes: OrderedDict = data[a["exchange"]][a["symbol"]][a["timeframe"]]
            volume_values = list(volumes.values())
            if not len(volume_values):
                return
            current_volume = volume_values[-1]
            avg_volume = Decimal(fmean(volume_values[-candle_len - 1 : -1]))
            alert_volume = avg_volume + (avg_volume * delta_percent)

            if current_volume >= alert_volume:
                key = a["key"]
                current_time = list(volumes)[-1]
                last_alert_time = self.last_alerts.get(key, 0)

                if current_time > last_alert_time:
                    self.last_alerts[key] = current_time
                    msg = (
                        f"🚨 ALERT TRIGGERED\n"
                        f"==========================\n"
                        f"{'Date':<15}: {datetime.now(tz=timezone.utc):%Y-%m-%d %H:%M:%S}\n"
                        f"{'Alert key':<15}: {a['key']}\n"
                        f"{'Alert volume':<15}: {alert_volume:.3f}\n"
                        f"{'Trigger delta':<15}: {Decimal(a['delta']):.3f}%\n"
                        f"{'Average volume':<15}: {avg_volume:.3f}\n"
                        f"==========================\n"
                    )
                    telegram_bot.send_message(message=msg)
