import logging
import os

def get_logger(name: str = "codivus") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_level_str = os.getenv("CODIVUS_LOG_LEVEL", "WARNING").upper()
        log_level = getattr(logging, log_level_str, logging.WARNING)
        logger.setLevel(log_level)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
