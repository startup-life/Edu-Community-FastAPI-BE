from fastapi import FastAPI

app = FastAPI()

# 기본 루트 엔드포인트
@app.get("/")
def get_Hello():
    return "Hello, Adapterz!"