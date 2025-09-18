from fastapi import FastAPI
from controller import users
from controller import post
from controller import comment
from utils.constant.httpStatusCode import STATUS_MESSAGE
from utils.errorHandler import http_exception_handler
from fastapi import Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
import pymysql
from database import index
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import os
from fastapi_limiter.depends import RateLimiter
from starlette.middleware.sessions import SessionMiddleware
from fastapi_limiter import FastAPILimiter
import time


app = FastAPI()
#리미터 전체 적용
# 전역 요청 기록 저장용 (IP별)
REQUEST_LOG = {}

class GlobalLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        now = time.time()
        window = 60      # 60초 기준
        limit = 100      # 최대 100번

        # 현재 윈도우 내 요청만 유지
        user_log = REQUEST_LOG.setdefault(ip, [])
        user_log = [t for t in user_log if now - t < window]

        # 남은 요청 수
        remaining = limit - len(user_log) - 1
        reset = window - (now - user_log[0]) if user_log else window

        if len(user_log) >= limit:
            headers = {
                "RateLimit-Limit": str(limit),
                "RateLimit-Remaining": "0",
                "RateLimit-Reset": str(int(reset))
            }
            raise HTTPException(
                status_code=429,
                detail="Too Many Requests",
                headers=headers
            )

        # 로그 업데이트
        user_log.append(now)
        REQUEST_LOG[ip] = user_log

        # 정상 응답에 헤더 추가
        response = await call_next(request)
        response.headers["RateLimit-Limit"] = str(limit)
        response.headers["RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["RateLimit-Reset"] = str(int(reset))
        return response



app.add_middleware(GlobalLimiterMiddleware)

@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        # 10초 이상 걸리면 타임아웃 처리
        return await asyncio.wait_for(call_next(request), timeout=10)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))
load_dotenv(dotenv_path=".env.dev")

app.include_router(users.router)
app.include_router(post.router)
app.include_router(comment.router)

app.mount("/public", StaticFiles(directory="public"), name="public")

ALLOW_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,     
    allow_credentials=False,
    allow_methods=["*"],             
    allow_headers=["*"],             
    expose_headers=["*"],            
)


def get_connection():
    return pymysql.connect(
        **index.MYSQL_DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False, 
    )

def init_session_id():
    try:
        sql = """
            UPDATE user_table SET session_id = NULL;
        """
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
    except Exception as e:
        print("MySQL error in init_session_id:", e)
        return False
    return True

@app.on_event("startup")
async def startup_event():
    init_session_id()