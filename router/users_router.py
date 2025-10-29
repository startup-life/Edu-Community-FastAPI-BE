
from typing import Optional, Any, Dict
from fastapi import APIRouter, Body, Path, Query, Header, Depends
from starlette.responses import Response

from controller.users import UsersController
from util.authUtil import is_logged_in

router = APIRouter(prefix="/users", tags=["users"], responses={404: {"description": "Not found"}})

# 컨트롤러 직접 생성 (deps.py 미사용)
"""
라우터 함수가 호출될때마다 새로운 컨트롤러 객체를 생성하기 위해 함수로 정의
- 싱글톤 패턴을 적용하지 않는 이유:
    컨트롤러가 상태를 가지지 않더라도, 향후 상태를 가질 가능성을 고려하여 매 요청마다 새로운 인스턴스를 생성
    싱글톤 패턴 적용시 상태 관리에 따른 부작용 발생 가능성
이름 앞에 _를 붙이는 이유는 내부 전용 함수임을 명시하기 위해서 입니다. 파이썬의 관례
"""
def _ctl() -> UsersController:
    return UsersController()

@router.post("/login")
async def login(
    email: str = Body(...),
    password: str = Body(...)
):
    return await _ctl().login(email=email, password=password)

@router.post("/signup", status_code=201)
async def signup(
    email: str = Body(...),
    password: str = Body(...),
    nickname: Optional[str] = Body(None),
    profile_image_path: Optional[str] = Body(None, alias="profileImagePath"),
):
    return await _ctl().signup(email, password, nickname, profile_image_path)

# dependencies로 is_logged_in 사용하여 인증
# Dependencies 추가시 요청 처리 전 자동 실행할 기능을 정의 가능
@router.post("/logout", dependencies=[Depends(is_logged_in)])
async def logout(user_id: int = Header(..., alias="userId")):
    return await _ctl().logout(user_id)

@router.get("/{user_id}", dependencies=[Depends(is_logged_in)])
async def get_user(user_id: int = Path(..., gt=0)):
    return await _ctl().get_user(user_id)

@router.put("/{userId}", dependencies=[Depends(is_logged_in)])
async def update_user(
    user_id: int = Path(..., alias="userId"),
    nickname: str = Body(..., alias="nickname"),
    profile_image_path: Optional[str] = Body(None, alias="profileImagePath"),
):
    return await _ctl().update_user(user_id, nickname, profile_image_path)

@router.get("/auth/check", dependencies=[Depends(is_logged_in)])
async def check_auth(user_id: int = Header(..., alias="userId")):
    return await _ctl().check_auth(user_id)

@router.patch("/{userId}/password", dependencies=[Depends(is_logged_in)])
async def change_password(
    password: str = Body(..., embed=True, alias="password"),
    user_id: int = Path(..., gt=0, alias="userId"),
):
    return await _ctl().change_password(user_id, password)

@router.get("/email/check")
async def check_email(email: str = Query(...)):
    return await _ctl().check_email(email)

@router.get("/nickname/check")
async def check_nickname(nickname: str = Query(...)):
    return await _ctl().check_nickname(nickname)

@router.delete("/{user_id}", dependencies=[Depends(is_logged_in)])
async def delete_user(user_id: int = Path(..., gt=0)):
    return await _ctl().delete_user(user_id)
