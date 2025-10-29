import logging
from time import perf_counter

import pymysql
from dotenv import load_dotenv
import os

from pymysql.cursors import DictCursor

load_dotenv(dotenv_path=".env.dev")

# MySQL 연결 설정
MYSQL_DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE")
}

# SQL 로깅 설정
logger = logging.getLogger("sql")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class LoggingCursor(DictCursor):
    # SQL 실행 시각과 쿼리 로깅
    def execute(self, query, args=None):
        start = perf_counter()
        try:
            return super().execute(query, args)
        finally:
            elapsed_ms = (perf_counter() - start) * 1000
            logger.info("SQL %0.2f ms | %s",
                        elapsed_ms, self.mogrify(query, args).decode() if isinstance(self.mogrify(query, args), bytes) else self.mogrify(query, args))

# MySQL 연결 함수
def get_connection():
    """MySQL 연결을 반환 (동기, 실행 시각+SQL 로깅)."""
    return pymysql.connect(
        # **는 파이썬의 딕셔너리 언패킹 문법
        # MYSQL_DB_CONFIG가 딕셔너리일때 그 안의 키-값 쌍을 인자로 풀어서 전달
        **MYSQL_DB_CONFIG,
        cursorclass=LoggingCursor,
        autocommit=False,
    )