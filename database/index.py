import logging
from time import perf_counter

import pymysql
from dotenv import load_dotenv
import os

from pymysql.cursors import DictCursor

load_dotenv(dotenv_path=".env.dev")

PORT = os.getenv("PORT")

MYSQL_DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE")
}

logger = logging.getLogger("sql")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class LoggingCursor(DictCursor):
    def execute(self, query, args=None):
        start = perf_counter()
        try:
            return super().execute(query, args)
        finally:
            elapsed_ms = (perf_counter() - start) * 1000
            logger.info("SQL %0.2f ms | %s",
                        elapsed_ms, self.mogrify(query, args).decode() if isinstance(self.mogrify(query, args), bytes) else self.mogrify(query, args))

def get_connection():
    """MySQL 연결을 반환 (동기, 실행 시각+SQL 로깅)."""
    return pymysql.connect(
        **MYSQL_DB_CONFIG,
        cursorclass=LoggingCursor,
        autocommit=False,
    )