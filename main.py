from fastapi import FastAPI, Request


app = FastAPI()

# POST 요청 예제
# Request Body에서 user_name과 age를 받아서 인사 메시지를 반환하는 엔드포인트
@app.post("/user/init")
async def user_init(request: Request):
    body = await request.json()
    user_name = body.get("user_name")
    age = body.get("age")
    return {
        "user_name": user_name,
        "age": age,
        "message": f"안녕하세요! {user_name}님!",
    }