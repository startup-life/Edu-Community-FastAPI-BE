import shutil
from typing import Annotated, Optional, Union, IO
import io
from fastapi import APIRouter, HTTPException, Header, Query, Body, UploadFile, File, Path, Depends, Header
from fastapi.responses import JSONResponse
from uuid import uuid4, uuid4

from multipart import file_path
from starlette.responses import Response
from model import user_model
import uuid
from starlette.concurrency import run_in_threadpool
import bcrypt
from utils.constant.httpStatusCode import STATUS_MESSAGE
from utils.constant.httpStatusCode import STATUS_CODE
from utils.validUtil import valid_email, valid_password, valid_nickname
from pathlib import Path as FSPath
import os
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from utils.authUtil import is_logged_in
from time import sleep

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# 로그인
@router.post("/login")
async def login(
    email: str = Body(..., description="이메일"),
    password: str = Body(..., description="비밀번호"),
    session_id: Optional[str] = Body(None, alias="sessionId", description="세션 ID(선택)")
):

    if not valid_email(email):
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"], content={"error": {"message": STATUS_MESSAGE["INVALID_EMAIL_FORMAT"], "data": None}})

    user_row = await user_model.get_user_by_email(email)
    if not user_row:
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"], content={"error": {"message": STATUS_MESSAGE["INVALID_CREDENTIALS"], "data": None}})

    db_hashed_pw = user_row["password"]
    ok = await run_in_threadpool(bcrypt.checkpw, password.encode("utf-8"), db_hashed_pw.encode("utf-8"))
    if not ok:
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"], content={"error": {"message": STATUS_MESSAGE["INVALID_CREDENTIALS"], "data": None}})


    profile_path = user_row.get("profile_image_path")
    file_id = user_row.get("file_id")
    if not profile_path and file_id is not None:
        profile_path = await user_model.get_profile_image_path(file_id)


    session_id = session_id or uuid4().hex
    updated = await user_model.update_session_id(user_row["user_id"], session_id)
    if not updated:
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"], content={"error": {"message": STATUS_MESSAGE["FAILED_TO_UPDATE_SESSION"], "data": None}})


    return JSONResponse(
        status_code=STATUS_CODE["OK"],
        content={"message": STATUS_MESSAGE["LOGIN_SUCCESS"], "data": {
            "userId": int(user_row["user_id"]),
            "email": user_row["email"],
            "nickname": user_row.get("nickname"),
            "sessionId": session_id,
            "created_at": str(user_row["created_at"]) if user_row.get("created_at") else None,
            "updated_at": str(user_row["updated_at"]) if user_row.get("updated_at") else None,
            "deleted_at": str(user_row["deleted_at"]) if user_row.get("deleted_at") else None,
        }},
    )

# 회원 가입
@router.post("/signup", status_code=STATUS_CODE["CREATED"])
async def signup(
    email: str = Body(..., description="이메일"),
    password: str = Body(..., description="비밀번호"),
    nickname: Optional[str] = Body(None, description="닉네임"),
    profile_image_path: Optional[str] = Body(None, alias="profileImagePath", description="프로필 이미지 경로"),
):
    # 검증
    if not valid_email(email) or not email:
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                            content={"error": {"message": STATUS_MESSAGE["INVALID_EMAIL_FORMAT"], "data": None}})

    if not valid_password(password) or not password:
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                            content={"error": {"message": STATUS_MESSAGE["INVALID_PASSWORD_FORMAT"], "data": None}})

    if nickname and not valid_nickname(nickname) or not nickname:
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                            content={"error": {"message": STATUS_MESSAGE["INVALID_NICKNAME_FORMAT"], "data": None}})

    # 비밀번호 해시
    hashed_password: bytes = await run_in_threadpool(
        bcrypt.hashpw, password.encode("utf-8"), bcrypt.gensalt()
    )
    hashed_password_str = hashed_password.decode("utf-8")
    print(hashed_password_str)

    user = await user_model.signup_user(
        email=email,
        password=hashed_password_str,
        nickname=nickname,  # 빈 문자열일 수도 있음(정책에 맞출 것)
        profile_image_path=profile_image_path,
    )

    if user == "already_exist_email":
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                            content={"error": {"message": STATUS_MESSAGE["ALREADY_EXIST_EMAIL"], "data": None}})

    if not user or not isinstance(user, dict) or "userId" not in user:
        return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                            content={"error": {"message": STATUS_MESSAGE["FAILED_TO_SIGNUP"], "data": None}})

    return JSONResponse(
        status_code=STATUS_CODE["CREATED"],
        content={"message": STATUS_MESSAGE["SIGNUP_SUCCESS"], "data": {
            "userId": int(user["userId"]),
            "profileImageId": user.get("profileImageId"),
        }},
    )

# 로그아웃
@router.post("/logout")
async def logout(
    user_id: int = Header(..., alias="userId")
):

    await user_model.destroy_user_session(
        user_id
    )
    return Response(status_code=STATUS_CODE["END"])

# 유저 정보 가져오기
@router.get("/{user_id}", dependencies=[Depends(is_logged_in)])
async def getUser(user_id: int = Path(..., gt=0)):
    try:
        if not user_id:
            raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_USER_ID"])


        response_data = await user_model.get_user(
            user_id
        )


        if response_data is None:
            raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=STATUS_CODE["INTERNAL_SERVER_ERROR"], detail=STATUS_MESSAGE["INTERNAL_SERVER_ERROR"])

    return JSONResponse(
        status_code=STATUS_CODE["OK"],
        content={"message": None, "data": jsonable_encoder(response_data)}
    )
    

# 회원 정보 수정
@router.put("/{userId}", dependencies=[Depends(is_logged_in)])
async def update_user(
    user_id: int = Path(..., alias="userId"),
    nickname: str = Body(..., alias="nickname"),
    profile_image_path: Optional[str] = Body(None, alias="profileImagePath"),
):
    if not user_id:
        raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_USER_ID"])
    if not nickname:
        raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_NICKNAME"])
    req = {"userId": user_id, "nickname": nickname, "profileImagePath": profile_image_path}
    res = await user_model.update_user(req)

    if res is None:
        raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])
    if res == "UPDATE_PROFILE_IMAGE_FAILED":
        raise HTTPException(status_code=STATUS_CODE["INTERNAL_SERVER_ERROR"], detail=STATUS_MESSAGE["UPDATE_PROFILE_IMAGE_FAILED"])

    return JSONResponse(
        status_code=STATUS_CODE["CREATED"],
        content={"message": STATUS_MESSAGE["UPDATE_USER_DATA_SUCCESS"], "data": None},
    )

# 로그인 상태 체크
@router.get("/auth/check")
async def check_auth(
    user_id: int = Header(..., alias="userId"),
):
    if not user_id:
        raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_USER_ID"])

    user_data = await user_model.get_user(user_id)

    if user_data[0]["user_id"] is not user_id:
        raise HTTPException(status_code=STATUS_CODE["UNAUTHORIZED"], detail=STATUS_MESSAGE["REQUIRED_AUTHORIZATION"])

    if not user_data:
        raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])
    if user_data[0]["user_id"] != user_id:
        raise HTTPException(status_code=STATUS_CODE["UNAUTHORIZED"], detail=STATUS_MESSAGE["REQUIRED_AUTHORIZATION"])

    if user_data[0]["user_id"] is not user_id:
        raise HTTPException(status_code=STATUS_CODE["UNAUTHORIZED"], detail=STATUS_MESSAGE["REQUIRED_AUTHORIZATION"])

    return JSONResponse(
        status_code=STATUS_CODE["OK"],
        content={"message": None, "data": {
            "userId": user_id,
            "email": user_data[0]["email"],
            "nickname": user_data[0]["nickname"],
            "profileImagePath": user_data[0]["file_path"],
            "authStatus": True,
        }},
    )
    

# 비밀번호 변경
@router.patch("/{userId}/password", dependencies=[Depends(is_logged_in)])
async def change_password(
    password: str = Body(...,embed=True, alias="password"),
    user_id: int = Path(..., gt=0, alias="userId")
):
    if not password:
        raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_PASSWORD"])

    hashed: bytes = await run_in_threadpool(bcrypt.hashpw, password.encode("utf-8"), bcrypt.gensalt())
    ok = await user_model.change_password({"userId": user_id, "password": hashed.decode("utf-8")})
    if not ok:
        raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])

    return JSONResponse(
        status_code=STATUS_CODE["CREATED"],
        content={"message": STATUS_MESSAGE["CHANGE_USER_PASSWORD_SUCCESS"], "data": None}
    )

# 이메일 중복 검사
@router.get("/email/check")
async def check_email(email: str = Query(..., description="이메일")):
    res = await user_model.check_email(email)
    if res is False:
        return JSONResponse(
            status_code=STATUS_CODE["OK"],
            content={"message": STATUS_MESSAGE["AVAILABLE_EMAIL"], "data": None}
        )
    raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["ALREADY_EXIST_EMAIL"])

# 닉네임 중복 검사
@router.get("/nickname/check")
async def check_nickname(nickname: str = Query(...)):
    res = await user_model.check_nickname(nickname)
    if res is False:
        return JSONResponse(
            status_code=STATUS_CODE["OK"],
            content={"message": STATUS_MESSAGE["AVAILABLE_NICKNAME"], "data": None}
        )
    raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["ALREADY_EXIST_NICKNAME"])

# 유저 삭제
@router.delete("/{user_id}", dependencies=[Depends(is_logged_in)])
async def delete_user(
    user_id: int = Path(..., gt=0),
):
    try:
        if not user_id:
            raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_USER_ID"])
        ok = await user_model.delete_user(
            user_id = user_id
        )
        if not ok:
            raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])

        return JSONResponse(
            status_code=STATUS_CODE["OK"],
            content={"message": STATUS_MESSAGE["DELETE_USER_DATA_SUCCESS"], "data": None}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=STATUS_CODE["INTERNAL_SERVER_ERROR"], detail=STATUS_MESSAGE["INTERNAL_SERVER_ERROR"])


SAVE_DIR = FSPath("./public/image/profile")

async def _save_upload_file(src: Union[UploadFile, bytes, IO[bytes]], dest_path: str) -> None:
    # 1) 타입별로 파일 객체 확보
    if isinstance(src, UploadFile):
        fobj = src.file
    elif isinstance(src, (bytes, bytearray)):
        fobj = io.BytesIO(src)
    elif hasattr(src, "read"):  # 이미 파일 객체
        fobj = src
    else:
        raise TypeError(f"Unsupported src type: {type(src)}")

    # 2) 가능하면 처음으로 이동
    try:
        fobj.seek(0, os.SEEK_SET)
    except Exception:
        pass

    # 3) 디스크로 복사
    with open(dest_path, "wb") as out:
        shutil.copyfileobj(fobj, out)

@router.post("/upload/profile-image")
async def upload_profile_image(
    profileImage: bytes = File(...)
):

    filename = f"{uuid.uuid4()}.png"

    if not profileImage:
        raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_FILE"])

    dest_path = os.path.join(SAVE_DIR, filename)

    await _save_upload_file(profileImage, dest_path)

    upload_file_path = f"/public/image/profile/{filename}"

    return JSONResponse(
        content={
            "data": {"filePath": upload_file_path}
        },
    )
