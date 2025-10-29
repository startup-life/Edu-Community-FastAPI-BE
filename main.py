import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import time
from typing import Dict, Deque
from router.users_router import router as users_router
from router.files_router import router as files_router
from router.posts_router import router as posts_router
from router.comments_router import router as comments_router
from collections import deque
from fastapi.staticfiles import StaticFiles

from database.index import get_connection
import os
from starlette.middleware.sessions import SessionMiddleware


# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout: int = 10):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        try:
            # asyncio.wait_for를 사용하여 요청 처리에 타임아웃 적용
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            # 타임아웃 발생 시 경고 로그 기록
            logger.warning(
                f"Request timed out: {request.method} {request.url}"
            )
            # 504 Gateway Timeout 응답 반환
            return JSONResponse(
                {"detail": "Request processing time exceeded limit"},
                status_code=504
            )


rate_limit_data: Dict[str, Deque[float]] = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_limit: int = 5, time_window: int = 10):
        super().__init__(app)
        self.requests_limit = requests_limit  # 허용 요청 횟수
        self.time_window = time_window      # 시간 창 (초)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # 현재 IP에 대한 요청 기록 가져오기 (없으면 새로 생성)
        request_timestamps = rate_limit_data.setdefault(client_ip, deque())

        # 시간 창을 벗어난 오래된 타임스탬프 제거
        while request_timestamps and request_timestamps[0] < current_time - self.time_window:
            request_timestamps.popleft()

        # 현재 요청 횟수가 한도를 초과했는지 확인
        if len(request_timestamps) >= self.requests_limit:
            return JSONResponse(
                {"detail": "Too Many Requests"},
                status_code=429 # 429 Too Many Requests
            )

        # 현재 요청의 타임스탬프 추가
        request_timestamps.append(current_time)

        # 다음 미들웨어 또는 엔드포인트 실행
        response = await call_next(request)
        return response

app = FastAPI()

app.mount("/public", StaticFiles(directory="public"))

app.include_router(users_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(files_router)

ALLOW_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(TimeoutMiddleware, timeout=15)

app.add_middleware(
    RateLimitMiddleware,
    requests_limit=5,
    time_window=10
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))

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