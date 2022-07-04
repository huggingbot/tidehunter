import logging
import os
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Callable

from dotenv import load_dotenv
from telegram.ext import CallbackContext, CommandHandler, Dispatcher, Updater
from telegram.update import Update

from core.extensions import Singleton
from core.loggings import telegram_logger as logger
from modules.telegram.telegram_listener import TelegramListener

load_dotenv()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID")

my_queue: queue.Queue = queue.Queue()


class TelegramBot(metaclass=Singleton):
    dispatcher: Dispatcher
    updater: Updater
    queued_msg_started = False

    def __init__(self) -> None:
        logger.setLevel(logging.INFO)

    def start_bot(self):
        date = datetime.now(tz=timezone.utc)
        logger.info(f"{date:%Y-%m-%d %H:%M:%S} > START TELEGRAM_BOT")
        self.updater = Updater(TELEGRAM_API_KEY, use_context=True)
        self.dispatcher = self.updater.dispatcher

        # Listen to user input commands
        TelegramListener(self)

        # Log all errors
        self.dispatcher.add_error_handler(self.error)

    def on_command(
        self, command: str, callback: Callable[[Update, CallbackContext], None]
    ):
        self.dispatcher.add_handler(CommandHandler(command, callback))

    def error(self, update, context):
        # Logs errors
        logger.error(f"Update {update} caused error {context.error}")

    def send_message(self, chat_id=TELEGRAM_GROUP_ID, message="blank"):
        item = {"chat_id": chat_id, "message": message}
        my_queue.put(item)

        # logger.info(f'Remaining in queue: {my_queue.qsize()}')
        if not self.queued_msg_started:
            self.queued_msg_started = True
            my_thread = threading.Thread(target=self.execute_queue)
            my_thread.start()

    def execute_queue(self):
        while not my_queue.empty():
            item = my_queue.get()
            # logger.info(item)
            self._send_message_in_queue(item["chat_id"], item["message"])
            logger.info(f"Remaining in queue: {my_queue.qsize()}")
            time.sleep(2)
        self.queued_msg_started = False
        logger.info(f"End of queue: {my_queue.qsize()}")

    def _send_message_in_queue(self, chat_id, message="blank"):
        sleep = 1
        retry = 0
        while True:
            try:
                message = message.replace("<", "&#60;")
                message = message.replace(">", "&#62;")
                self.dispatcher.bot.send_message(
                    chat_id=chat_id,
                    text="<pre>" + message + "</pre>",
                    parse_mode="HTML",
                )
            except Exception as ex:
                print(
                    f"TELEGRAM SEND FAILED: {retry}... sleeping for {sleep} second(s)\n"
                    f"{ex}"
                )
                time.sleep(sleep)
                retry += 1
                sleep += 2
                continue
            break

    def run_bot(self):
        self.updater.start_polling()


telegram_bot = TelegramBot()
