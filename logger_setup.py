import os
import sys

from loguru import logger

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger.remove()

# Лог в файл (всегда)
logger.add(
    f"{LOG_DIR}/sync_{{time:YYYY-MM-DD}}.log",
    rotation="1 day",
    retention="14 days",
    level="INFO",
    encoding="utf-8"
)

# Лог в stdout (только если он существует)
if getattr(sys, 'stdout', None):
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

