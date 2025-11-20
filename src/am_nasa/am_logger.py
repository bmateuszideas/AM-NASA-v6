import logging
import sys

# Konfiguracja loggera
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("am_debug.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("am_logger")

def log_debug(msg):
    logger.debug(msg)

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

def log_exception(msg):
    logger.exception(msg)

# Dekorator do logowania wywołań funkcji
def log_call(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Wywołanie: {func.__name__} args={args} kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Wynik: {func.__name__} -> {result}")
            return result
        except Exception as e:
            logger.exception(f"Błąd w {func.__name__}: {e}")
            raise
    return wrapper
