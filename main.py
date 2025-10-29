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
# 기본 로깅 레벨을 INFO로 설정
logging.basicConfig(level=logging.INFO)
# 현재 모듈의 로거 인스턴스 생성
logger = logging.getLogger(__name__)

# 타임아웃 미들웨어 정의
# 요청 처리 시간이 지정된 시간(초)을 초과하면 504 응답 반환
class TimeoutMiddleware(BaseHTTPMiddleware):
    # 타임아웃 시간(초) 설정
    # __init__은 미들웨어 인스턴스 생성 시 호출되는 초기화 메서드
    def __init__(self, app, timeout: int = 10):
        super().__init__(app)
        self.timeout = timeout
    # 요청 처리에 타임아웃 적용
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

# 간단한 메모리 기반 속도 제한 미들웨어 정의
# 각 클라이언트 IP별로 일정 시간 내에 허용된 요청 횟수를 초과하면 429 응답 반환
rate_limit_data: Dict[str, Deque[float]] = {}

# 속도 제한 미들웨어 정의
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_limit: int = 5, time_window: int = 10):
        super().__init__(app)
        self.requests_limit = requests_limit  # 허용 요청 횟수
        self.time_window = time_window      # 시간 창 (초)

    async def dispatch(self, request: Request, call_next):
        # 클라이언트 IP 가져오기
        # 없을 경우 "unknown" 사용
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

# 정적 파일 서빙 설정
app.mount("/public", StaticFiles(directory="public"))

# 라우터 포함
app.include_router(users_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(files_router)

# CORS 설정
ALLOW_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# 미들웨어 추가
app.add_middleware(TimeoutMiddleware, timeout=15)

# 속도 제한 미들웨어 추가
# 현재: 10초에 100회 요청 허용
app.add_middleware(
    RateLimitMiddleware,
    requests_limit=100,
    time_window=10
)

"""
미들웨어 설정 - CORS 및 세션 관리
- CORS 미들웨어: 지정된 출처에서 오는 요청 허용
- 세션 미들웨어: 세션 관리를 위한 비밀 키 설정
allow_origins는 허용할 출처 목록을 지정
allow_credentials는 자격 증명(쿠키, 인증 헤더 등)을 허용할지 여부를 설정
allow_methods는 허용할 HTTP 메서드를 지정. ["*"]는 모든 메서드를 허용함을 의미
allow_headers는 허용할 HTTP 헤더를 지정. ["*"]는 모든 헤더를 허용함을 의미
expose_headers는 클라이언트가 접근할 수 있는 헤더를 지정. ["*"]는 모든 헤더를 노출함을 의미
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 세션 미들웨어 추가
# SESSION_SECRET 환경 변수를 비밀 키로 사용
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))

# 애플리케이션 시작 시 모든 사용자의 session_id를 NULL로 초기화
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

# 애플리케이션 시작 이벤트에 초기화 함수 등록
@app.on_event("startup")
async def startup_event():
    init_session_id()