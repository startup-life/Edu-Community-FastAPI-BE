from typing import Optional
from fastapi import APIRouter, Body, Header, Path, Query, Response
from controller.users import UsersController

"""
prefix: 모든 엔드포인트 앞에 /users 자동 추가
responses: 공통 응답 정의
"""
router = APIRouter(prefix="/users", tags=["users"], responses={404: {"description": "Not found"}})

"""
각 요청마다 새로운 UserController 인스턴스 생성
상태 충돌 회피를 위해서 추가했음
"""
def _ctl() -> UsersController:
    return UsersController()

"""
로그인
이메일과 비밀번호로 로그인
인증 실패 시 401 반환,
"""
@router.post("/login")
async def login(
    email: str = Body(..., description="이메일"),
    password: str = Body(..., description="비밀번호"),
):
    return await _ctl().login(email, password)

"""
회원가입
이메일, 비밀번호, 닉네임으로 회원가입
중복 이메일 시 400 반환
"""
@router.post("/signup")
async def signup_user(
    email: str = Body(..., description="이메일"),
    password: str = Body(..., description="비밀번호"),
    nickname: str = Body(..., description="닉네임"),
):
    return await _ctl().signup_user(email, password, nickname)

"""
사용자 조회
user_id로 사용자 정보 조회
존재하지 않으면 404 반환
"""
@router.get("/{user_id}")
async def get_user(user_id: int = Path(..., description="사용자 ID")):
    return await _ctl().get_user(user_id)

"""
사용자 정보 업데이트
user_id로 사용자 정보(닉네임) 업데이트
존재하지 않으면 404 반환
"""
@router.put("/{user_id}")
async def update_user(
    user_id: int = Path(..., description="사용자 ID"),
    nickname: str = Body(..., description="새 닉네임", embed=True),
):
    return await _ctl().update_user(user_id, nickname)

"""
인증 상태 확인
Header로 전달된 사용자 ID 기반 인증 상태 확인
유효하지 않으면 401 반환
"""
@router.get("/auth/check")
async def check_auth(userid: int = Header(..., description="사용자 ID")):
    return await _ctl().check_auth(userid)

"""
비밀번호 변경
존재하지 않으면 404 반환
"""
@router.patch("/{user_id}/password")
async def change_password(
    user_id: int = Path(..., description="사용자 ID"),
    password: str = Body(..., description="새 비밀번호", embed=True),
):
    return await _ctl().change_password(user_id, password)

"""
사용자 삭제 (소프트 딜리트)
deleted_at 필드에 현재 시간 저장
"""
@router.delete("/{user_id}")
async def soft_delete_user(user_id: int = Path(..., description="사용자 ID")):
    return await _ctl().soft_delete_user(user_id)

"""
로그아웃 
session_id를 None으로 변경
존재하지 않아도 204 반환
"""
@router.post("/logout")
async def logout_user(userid: int = Header(..., description="사용자 ID")):
    return await _ctl().logout_user(userid)

"""
이메일 중복 체크
중복이면 400반환, 사용 가능하면 200반환
"""
@router.get("/email/check")
async def check_email(email: str = Query(..., description="중복 확인할 이메일")):
    return await _ctl().check_email(email)

"""
닉네임 중복 확인
중복이면 400반환, 사용 가능하면 200반환
"""
@router.get("/nickname/check")
async def check_nickname(nickname: str = Query(..., description="중복 확인할 닉네임")):
    return await _ctl().check_nickname(nickname)
