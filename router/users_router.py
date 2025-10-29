from typing import Optional
from fastapi import APIRouter, Body, Header, Path, Query
from controller.users import UsersController

"""
prefix="/users" 모든 경로 앞에 /users 추가
404 응답에 대한 공통 설명 추가
"""
router = APIRouter(prefix="/users", responses={404: {"description": "Not found"}})

def _ctl() -> UsersController:
    return UsersController()

@router.post("/login")
async def login(
    email: str = Body(..., description="이메일"),
    password: str = Body(..., description="비밀번호"),
):
    return await _ctl().login(email, password)

@router.post("/signup", status_code=201)
async def signup(
    email: str = Body(..., description="이메일"),
    password: str = Body(..., description="비밀번호"),
    nickname: Optional[str] = Body(None, description="닉네임"),
    profileImagePath: Optional[str] = Body(None, description="프로필 이미지 경로"),
):
    return await _ctl().signup(email, password, nickname, profileImagePath)

@router.post("/logout")
async def logout(userId: int = Header(..., alias="userId")):
    return await _ctl().logout(userId)

@router.get("/{user_id}")
async def get_user(user_id: int = Path(..., gt=0)):
    return await _ctl().get_user(user_id)

@router.put("/{userId}")
async def update_user(
    userId: int = Path(..., alias="userId"),
    nickname: str = Body(..., alias="nickname"),
    profileImagePath: Optional[str] = Body(None, alias="profileImagePath"),
):
    return await _ctl().update_user(userId, nickname, profileImagePath)

@router.get("/auth/check")
async def check_auth(userId: int = Header(..., alias="userId")):
    return await _ctl().check_auth(userId)

@router.patch("/{userId}/password")
async def change_password(
    password: str = Body(..., embed=True, alias="password"),
    userId: int = Path(..., gt=0, alias="userId"),
):
    return await _ctl().change_password(userId, password)

@router.get("/email/check")
async def check_email(email: str = Query(..., description="이메일")):
    return await _ctl().check_email(email)

@router.get("/nickname/check")
async def check_nickname(nickname: str = Query(...)):
    return await _ctl().check_nickname(nickname)

@router.delete("/{user_id}")
async def delete_user(user_id: int = Path(..., gt=0)):
    return await _ctl().delete_user(user_id)
