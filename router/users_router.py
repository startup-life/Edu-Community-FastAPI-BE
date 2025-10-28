from typing import Optional
from fastapi import APIRouter, Body, Header, Path, Query, Response
from controller.users_memory import UsersController

router = APIRouter(prefix="/users", tags=["users"], responses={404: {"description": "Not found"}})

def _ctl() -> UsersController:
    return UsersController()

@router.post("/login")
async def login(
    email: str = Body(..., description="이메일"),
    password: str = Body(..., description="비밀번호"),
):
    return await _ctl().login(email, password)

@router.post("/signup")
async def signup_user(
    email: str = Body(..., description="이메일"),
    password: str = Body(..., description="비밀번호"),
    nickname: str = Body(..., description="닉네임"),
):
    return await _ctl().signup_user(email, password, nickname)

@router.get("/{user_id}")
async def get_user(user_id: int = Path(..., description="사용자 ID")):
    return await _ctl().get_user(user_id)

@router.put("/{user_id}")
async def update_user(
    user_id: int = Path(..., description="사용자 ID"),
    nickname: str = Body(..., description="새 닉네임", embed=True),
):
    return await _ctl().update_user(user_id, nickname)

@router.get("/auth/check")
async def check_auth(userid: int = Header(..., description="사용자 ID")):
    return await _ctl().check_auth(userid)

@router.patch("/{user_id}/password")
async def change_password(
    user_id: int = Path(..., description="사용자 ID"),
    password: str = Body(..., description="새 비밀번호", embed=True),
):
    return await _ctl().change_password(user_id, password)

@router.delete("/{user_id}")
async def soft_delete_user(user_id: int = Path(..., description="사용자 ID")):
    return await _ctl().soft_delete_user(user_id)

@router.post("/logout")
async def logout_user(userid: int = Header(..., description="사용자 ID")):
    return await _ctl().logout_user(userid)

@router.get("/email/check")
async def check_email(email: str = Query(..., description="중복 확인할 이메일")):
    return await _ctl().check_email(email)

@router.get("/nickname/check")
async def check_nickname(nickname: str = Query(..., description="중복 확인할 닉네임")):
    return await _ctl().check_nickname(nickname)
