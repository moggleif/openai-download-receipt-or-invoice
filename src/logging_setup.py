import sys
import logging

LOG_FILE = "openai_receipt.log"
NOISY_LOGGERS = ("asyncio", "playwright", "urllib3")


def setup_logging(verbose: bool = False) -> None:
    log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            _console_handler(verbose),
            _file_handler(),
        ],
    )
    _silence_noisy_loggers()
    _write_session_separator()


def _console_handler(verbose: bool) -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    return handler


def _file_handler() -> logging.Handler:
    handler = logging.FileHandler(LOG_FILE)
    handler.setLevel(logging.DEBUG)
    return handler


def _silence_noisy_loggers() -> None:
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def _write_session_separator() -> None:
    with open(LOG_FILE, "a") as f:
        f.write("\n" + "=" * 60 + "\n\n")
