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

"""
SQL 실행 시간을 콘솔에 출력하기 위한 로거 설정
"""
logger = logging.getLogger("sql")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

"""
pymysql DictCursor를 상속하여 SQL 실행 시간을 측정하고
실행된 쿼리를 로깅하는 커서 클래스 정의
"""
class LoggingCursor(DictCursor):
    def execute(self, query, args=None):
        start = perf_counter() # 실행 시작 시간 기록
        try:
            return super().execute(query, args)
        finally:
            # 실행 시간 측정 후 로그 출력
            elapsed_ms = (perf_counter() - start) * 1000
            # mogrify는 SQL에 파라미터를 실제 값으로 치환한 최종 쿼리 문자열을 반환
            # mogrify는 결과가 bytes일 경우 문자열로 디코딩
            logger.info("SQL %0.2f ms | %s",
                        elapsed_ms, self.mogrify(query, args).decode() if isinstance(self.mogrify(query, args), bytes) else self.mogrify(query, args))

# MySQL DB 연결 객체를 반환
# - LoggingCursor를 사용해 모든 SQL 실행 시 로깅
# - autocommit=False로 트랜잭션 수동 관리 가능
def get_connection():
    """MySQL 연결을 반환 (동기, 실행 시각+SQL 로깅)."""
    return pymysql.connect(
        **MYSQL_DB_CONFIG,
        cursorclass=LoggingCursor,
        autocommit=False,
    )