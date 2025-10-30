# app/api/routers/users_router.py
from typing import Optional, Any, Dict
from fastapi import APIRouter, Body, Path, Query, Header, Depends
from starlette.responses import Response

from controller.users import UsersController
from util.authUtil import is_logged_in

# 사용자 관련 라우터 설정
# Prefix: /users
router = APIRouter(prefix="/users", responses={404: {"description": "Not found"}})

# 컨트롤러 직접 생성 (deps.py 미사용)
def _ctl() -> UsersController:
    return UsersController()

# 로그인 엔드포인트
@router.post("/login")
async def login(
    email: str = Body(...),
    password: str = Body(...),
    session_id: Optional[str] = Body(None)
):
    return await _ctl().login(email=email, password=password, session_id=session_id)

# 회원가입 엔드포인트
@router.post("/signup", status_code=201)
async def signup(
    email: str = Body(...),
    password: str = Body(...),
    nickname: Optional[str] = Body(None),
    profile_image_path: Optional[str] = Body(None, alias="profileImagePath"),
):
    return await _ctl().signup(email, password, nickname, profile_image_path)

# 로그아웃 엔드포인트
# dependencies를 사용하여 is_logged_in 함수로 인증 검사
@router.post("/logout", dependencies=[Depends(is_logged_in)])
async def logout(user_id: int = Header(..., alias="userId")):
    return await _ctl().logout(user_id)

# 사용자 정보 조회 엔드포인트
# dependencies를 사용하여 is_logged_in 함수로 인증 검사
@router.get("/{user_id}", dependencies=[Depends(is_logged_in)])
async def get_user(user_id: int = Path(..., gt=0)):
    return await _ctl().get_user(user_id)

# 사용자 정보 수정 엔드포인트
# dependencies를 사용하여 is_logged_in 함수로 인증 검사
@router.put("/{user_id}", dependencies=[Depends(is_logged_in)])
async def update_user(
    user_id: int = Path(..., alias="user_id"),
    nickname: str = Body(..., alias="nickname"),
    profile_image_path: Optional[str] = Body(None, alias="profileImagePath"),
):
    return await _ctl().update_user(user_id, nickname, profile_image_path)

# 인증 상태 확인 엔드포인트
# dependencies를 사용하여 is_logged_in 함수로 인증 검사
@router.get("/auth/check", dependencies=[Depends(is_logged_in)])
async def check_auth(user_id: int = Header(..., alias="userId")):
    return await _ctl().check_auth(user_id)

# 비밀번호 변경 엔드포인트
# dependencies를 사용하여 is_logged_in 함수로 인증 검사
@router.patch("/{user_id}/password", dependencies=[Depends(is_logged_in)])
async def change_password(
    password: str = Body(..., embed=True, alias="password"),
    user_id: int = Path(..., gt=0, alias="user_id"),
):
    return await _ctl().change_password(user_id, password)

# 이메일 중복 확인 엔드포인트
@router.get("/email/check")
async def check_email(email: str = Query(...)):
    return await _ctl().check_email(email)

# 닉네임 중복 확인 엔드포인트
@router.get("/nickname/check")
async def check_nickname(nickname: str = Query(...)):
    return await _ctl().check_nickname(nickname)

# 사용자 삭제 엔드포인트
# dependencies를 사용하여 is_logged_in 함수로 인증 검사
@router.delete("/{user_id}", dependencies=[Depends(is_logged_in)])
async def delete_user(user_id: int = Path(..., gt=0)):
    return await _ctl().delete_user(user_id)