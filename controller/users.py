from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import Response

# 인메모리 상태
# DB 대체
users = [
    {
        "user_id": 1, "email": "alice@example.com", "password": "Alice@1234",
        "nickname": "앨리스", "file_id": 101, "session_id": "sess-abc123",
        "created_at": "2024-12-01T10:00:00Z", "updated_at": "2024-12-01T10:00:00Z", "deleted_at": None,
    },
    {
        "user_id": 2, "email": "bob@example.com", "password": "Bob!pass2024",
        "nickname": "밥", "file_id": 102, "session_id": "sess-def456",
        "created_at": "2024-12-02T11:30:00Z", "updated_at": "2024-12-02T11:30:00Z", "deleted_at": None,
    },
    {
        "user_id": 3, "email": "carol@example.com", "password": "Carol#Pass5678",
        "nickname": "캐롤", "file_id": None, "session_id": None,
        "created_at": "2024-12-03T12:45:00Z", "updated_at": "2024-12-03T12:45:00Z", "deleted_at": None,
    },
    {
        "user_id": 4, "email": "david@example.com", "password": "David*Secure999",
        "nickname": "데이빗", "file_id": 103, "session_id": "sess-ghi789",
        "created_at": "2024-12-04T14:15:00Z", "updated_at": "2024-12-04T14:15:00Z", "deleted_at": None,
    },
    {
        "user_id": 5, "email": "eve@example.com", "password": "Eve%Password!1",
        "nickname": "이브", "file_id": None, "session_id": None,
        "created_at": "2024-12-05T15:20:00Z", "updated_at": "2024-12-05T15:20:00Z", "deleted_at": None,
    },
]

# 현재 UTC 시간을 ISO 포맷 문자열로 반환
_now = lambda: datetime.now(timezone.utc).isoformat()

class UsersController:
    # 특정 필드로 삭제되지 않은 활성 사용자 찾기
    def _find_active(self, *, by: str, value) -> Optional[Dict[str, Any]]:
        return next((u for u in users if u.get(by) == value and not u.get("deleted_at")), None)

    # 로그인 처리
    # 이메일 + 비밀번호가 일치하고 삭제되지 않은 사용자만 인증
    # 실패 시 401 반환
    async def login(self, email: str, password: str):
        user = next((u for u in users if u["email"] == email and u["password"] == password and not u["deleted_at"]), None)
        if not user:
            return JSONResponse(status_code=401, content={"data": None})
        return JSONResponse(status_code=200, content={"data": user})

    """
    회원가입 처리
    이메일 중복되면 400반환
    신규 사용자 정보를 users에 추가
    """
    async def signup_user(self, email: str, password: str, nickname: str):
        if self._find_active(by="email", value=email):
            return JSONResponse(status_code=400, content={"data": "duplicate"})
        new_user = {
            "user_id": len(users) + 1,
            "email": email,
            "password": password,
            "nickname": nickname,
            "file_id": None,
            "session_id": None,
            "created_at": _now(),
            "updated_at": _now(),
            "deleted_at": None,
        }
        users.append(new_user)
        return JSONResponse(status_code=201, content={"data": new_user})

    """
    특정 user_id로 사용자 정보 조회
    존재하지 않거나 삭제된 경우 404 반환
    """
    async def get_user(self, user_id: int):
        user = self._find_active(by="user_id", value=user_id)
        if not user:
            return JSONResponse(status_code=404, content={"data": None})
        return JSONResponse(status_code=200, content={"data": user})

    """
    사용자 정보 업데이트
    없는 경우 404, 성공 시 200 반환
    """
    async def update_user(self, user_id: int, nickname: str):
        user = self._find_active(by="user_id", value=user_id)
        if not user:
            return JSONResponse(status_code=404, content={"data": None})
        user["nickname"] = nickname
        user["updated_at"] = _now()
        return JSONResponse(status_code=200, content={"data": None})

    """
    인증 상태 확인
    유효한 사용자면 인증 정보 반환, 없으면 401 반환
    """
    async def check_auth(self, userid: int):
        user = self._find_active(by="user_id", value=userid)
        if not user:
            return JSONResponse(status_code=401, content={"data": None})
        return JSONResponse(
            status_code=200,
            content={
                "data": {
                    "userId": user["user_id"],
                    "email": user["email"],
                    "nickname": user["nickname"],
                    "auth_token": user["session_id"],
                    "auth_status": True,
                }
            },
        )

    """
    비밀번호 변경,
    없는 경우 404, 성공 시 200반환
    """
    async def change_password(self, user_id: int, password: str):
        user = self._find_active(by="user_id", value=user_id)
        if not user:
            return JSONResponse(status_code=404, content={"data": None})
        user["password"] = password
        user["updated_at"] = _now()
        return JSONResponse(status_code=200, content={"data": None})

    """
    소프트 딜리트 처리
    deleted_at 필드에 현재 시간 저장
    """
    async def soft_delete_user(self, user_id: int):
        user = self._find_active(by="user_id", value=user_id)
        if not user:
            return JSONResponse(status_code=404, content={"data": None})
        user["deleted_at"] = _now()
        return JSONResponse(status_code=200, content={"data": None})

    """
    로그아웃 처리
    session_id를 None으로 변경
    존재하지 않는 사용자여도 204 반환
    """
    async def logout_user(self, userid: int):
        user = self._find_active(by="user_id", value=userid)
        if not user:
            return Response(status_code=204)
        user["session_id"] = None
        return Response(status_code=204)

    """
    이메일 중복 체크
    중복이면 400, 사용 가능한경우 200
    """
    async def check_email(self, email: str):
        user = self._find_active(by="email", value=email)
        if user:
            return JSONResponse(status_code=400, content={"data": "duplicate"})
        return JSONResponse(status_code=200, content={"data": None})

    """
    닉네임 중복 체크
    중복이면 400, 사용 가능한 경우 200
    """
    async def check_nickname(self, nickname: str):
        user = self._find_active(by="nickname", value=nickname)
        if user:
            return JSONResponse(status_code=400, content={"data": "duplicate"})
        return JSONResponse(status_code=200, content={"data": None})
