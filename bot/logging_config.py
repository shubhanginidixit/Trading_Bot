"""
Logging configuration for the trading bot.
Writes structured logs to both file and console.
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str = "trading_bot", log_dir: str = "logs") -> logging.Logger:
    """
    Configure and return a logger that writes to both a rotating log file
    and the console (warnings and above only).

    Args:
        name:    Logger name (also used as the log file stem).
        log_dir: Directory where log files are stored.

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers when the module is imported multiple times
    if logger.handlers:
        return logger

    # ── File handler ────────────────────────────────────────────────────────
    # One log file per calendar day, e.g. logs/trading_bot_2025-01-15.log
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(log_dir, f"{name}_{date_str}.log")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # ── Console handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        fmt="%(levelname)-8s %(message)s",
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.debug("Logger initialised → %s", log_path)
    return logger
