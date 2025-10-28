# app/api/routers/users_router.py
from typing import Optional, Any, Dict
from fastapi import APIRouter, Body, Path, Query, Header, Depends
from starlette.responses import Response

from controller.users import UsersController
from util.authUtil import is_logged_in

router = APIRouter(prefix="/users", tags=["users"], responses={404: {"description": "Not found"}})

# 컨트롤러 직접 생성 (deps.py 미사용)
def _ctl() -> UsersController:
    return UsersController()

@router.post("/login")
async def login(
    email: str = Body(...),
    password: str = Body(...),
    session_id: Optional[str] = Body(None)
):
    return await _ctl().login(email=email, password=password, session_id=session_id)

@router.post("/signup", status_code=201)
async def signup(
    email: str = Body(...),
    password: str = Body(...),
    nickname: Optional[str] = Body(None),
    profile_image_path: Optional[str] = Body(None, alias="profileImagePath"),
):
    return await _ctl().signup(email, password, nickname, profile_image_path)

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
