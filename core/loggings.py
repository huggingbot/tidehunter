import logging

from utils.path import build_path

DEFAULT_LOGGER_NAME = "tidehunter-bot"
DEFAULT_LOGGING_PATH = ["logs", DEFAULT_LOGGER_NAME]


def setup_logging() -> None:
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.getLogger("binance-client").setLevel(logging.WARN)
    logging.getLogger("binance-futures").setLevel(logging.WARN)
    logging.getLogger("apscheduler.executors.default").setLevel(logging.INFO)
    logging.getLogger("apscheduler.executors.default").propagate = False

    handlers: list[logging.Handler] = []
    formatter = logging.Formatter(
        "%(asctime)s [%(name)-12.12s] %(levelname)s : %(message)s"
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    handlers.append(stream_handler)

    file_handler = logging.FileHandler(
        build_path(DEFAULT_LOGGING_PATH), encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
    logging.basicConfig(level=logging.INFO, handlers=handlers)


setup_logging()

logger = logging.getLogger(DEFAULT_LOGGER_NAME)
telegram_logger = logging.getLogger("telegram-bot")
