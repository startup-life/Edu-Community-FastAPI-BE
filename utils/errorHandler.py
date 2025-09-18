from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# 공통 HTTP 예외 핸들러
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.detail == "already_exist_email":
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "already_exist_email", "data": None}},
        )

    # 기본 처리
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"message": str(exc.detail), "data": None}},
    )