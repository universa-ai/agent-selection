import logging
import os

from colorlog import ColoredFormatter


def config_logging(level: int = logging.INFO) -> logging.StreamHandler:
    """
    Configure logging stream.
    """
    log_path = os.devnull
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)-8s %(name)s %(funcName)s   %(message)s',
        datefmt='%Y-%m-%d,%H:%M:%S',
        filename=log_path,
        filemode='w'
    )

    # Add console logger
    console = logging.StreamHandler()
    console.setLevel(level)
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)-8s %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'blue',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white'
        },
        secondary_log_colors={},
        style='%'
    )
    console.setFormatter(formatter)
    
    return console

LOGGING_HANDLER = config_logging()

def get_logger(name: str) -> logging.Logger:
    """
    Get basic logger with custom configuration.
    """
    logger = logging.getLogger(name)
    logger.addHandler(LOGGING_HANDLER)
    
    return logger

general_logger = get_logger("Universa")
