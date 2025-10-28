import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, Deque
from collections import deque

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
        self.time_window = time_window  # 시간 창 (초)

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
                status_code=429  # 429 Too Many Requests
            )

        # 현재 요청의 타임스탬프 추가
        request_timestamps.append(current_time)

        # 다음 미들웨어 또는 엔드포인트 실행
        response = await call_next(request)
        return response


app = FastAPI()

app.add_middleware(TimeoutMiddleware, timeout=15)

app.add_middleware(
    RateLimitMiddleware,
    requests_limit=5,
    time_window=10
)