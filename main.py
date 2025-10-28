from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# 실무에서 많이 사용되는 JSONResponse를 활용하여 구현
# JSONResponse를 많이 사용하는 이유는 상태 코드, 헤더, 쿠키 등을 세밀하게 제어할 수 있고
# FastAPI의 기본 응답 클래스인 Response를 상속받아 구현되어 있어 호환성이 좋고 자동 JSON 직렬화 기능을 제공해서 편리

# 커스텀 상태 코드 지정
@app.get("/customstatus")
def create_item():
    content = {"item_id": 2, "name": "수동 생성"}
    # 상태 코드를 201로 지정하여 응답
    return JSONResponse(content=content, status_code=201)

# 커스텀 헤더 추가
@app.get("/customheaders")
def get_with_headers():
    content = {"message": "헤더 확인!"}
    headers = {"X-Request-ID": "abc-123", "Cache-Control": "no-cache"}
    # headers 딕셔너리를 함께 전달
    return JSONResponse(content=content, headers=headers)

# 쿠키 설정
@app.get("/cookie")
def login():
    resp = JSONResponse(content={"message": "로그인 성공"})
    # 응답 객체에 쿠키를 설정
    resp.set_cookie(key="session_id", value="user1234", httponly=True)
    return resp