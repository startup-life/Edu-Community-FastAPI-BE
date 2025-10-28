from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/customstatus")
def create_item():
    content = {"item_id": 2, "name": "수동 생성"}
    # 상태 코드를 201로 지정하여 응답
    return JSONResponse(content=content, status_code=201)

@app.get("/customheaders")
def get_with_headers():
    content = {"message": "헤더 확인!"}
    headers = {"X-Request-ID": "abc-123", "Cache-Control": "no-cache"}
    # headers 딕셔너리를 함께 전달
    return JSONResponse(content=content, headers=headers)

@app.get("/cookie")
def login():
    resp = JSONResponse(content={"message": "로그인 성공"})
    # 응답 객체에 쿠키를 설정
    resp.set_cookie(key="session_id", value="user1234", httponly=True)
    return resp