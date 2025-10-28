from fastapi import FastAPI, Request


app = FastAPI()

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