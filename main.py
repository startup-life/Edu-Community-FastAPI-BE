import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Deque

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout: int = 10):
        # FastAPI 앱과 타임아웃 시간 설정
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        try:
            # asyncio.wait_for를 사용하여 요청 처리에 타임아웃 적용
            # 요청이 self.timeout 초를 초과하면 TimeoutError 발생
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

# FastAPI 앱 생성 및 미들웨어 추가
app = FastAPI()

app.add_middleware(TimeoutMiddleware, timeout=15)