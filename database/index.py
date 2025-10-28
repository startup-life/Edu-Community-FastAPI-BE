from dotenv import load_dotenv
import os

"""
load_dotenv(dotenv_path=".env.dev")를 사용하여 .env.dev 파일에서 환경 변수를 로드
"""
load_dotenv(dotenv_path=".env.dev")

PORT = os.getenv("PORT")


MYSQL_DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE")
}