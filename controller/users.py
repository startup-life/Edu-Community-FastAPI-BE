from typing import Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import Response
from fastapi.encoders import jsonable_encoder

from model import user_model
from util.constant.httpStatusCode import STATUS_MESSAGE, STATUS_CODE
from util.validUtil import valid_email, valid_password, valid_nickname

class UsersController:
    async def login(self, email: str, password: str):
        if not valid_email(email):
            return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                                content={"error": {"message": STATUS_MESSAGE["INVALID_EMAIL_FORMAT"], "data": None}})
        user_row = await user_model.login_user(email, password)
        if not user_row:
            return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                                content={"error": {"message": STATUS_MESSAGE["INVALID_CREDENTIALS"], "data": None}})

        profile_path = user_row.get("profile_image_path")
        file_id = user_row.get("file_id")
        if not profile_path and file_id is not None:
            profile_path = await user_model.get_profile_image_path(file_id)

        return JSONResponse(
            status_code=STATUS_CODE["OK"],
            content={"message": STATUS_MESSAGE["LOGIN_SUCCESS"], "data": {
                "userId": user_row.get("userId"),
                "email": user_row.get("email"),
                "nickname": user_row.get("nickname"),
                "profile_path": profile_path,
                "created_at": str(user_row["created_at"]) if user_row.get("created_at") else None,
                "updated_at": str(user_row["updated_at"]) if user_row.get("updated_at") else None,
                "deleted_at": str(user_row["deleted_at"]) if user_row.get("deleted_at") else None,
            }},
        )

    async def signup(self, email: str, password: str, nickname: Optional[str], profile_image_path: Optional[str]):
        if not valid_email(email) or not email:
            return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                                content={"error": {"message": STATUS_MESSAGE["INVALID_EMAIL_FORMAT"], "data": None}})
        if not valid_password(password) or not password:
            return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                                content={"error": {"message": STATUS_MESSAGE["INVALID_PASSWORD_FORMAT"], "data": None}})
        # 기존 로직 유지(빈 닉네임 금지)
        if (nickname and not valid_nickname(nickname)) or (nickname is None or nickname == ""):
            return JSONResponse(status_code=STATUS_CODE["BAD_REQUEST"],
                                content={"error": {"message": STATUS_MESSAGE["INVALID_NICKNAME_FORMAT"], "data": None}})

        user = await user_model.signup_user(
            email=email, password=password, nickname=nickname, profile_image_path=profile_image_path
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

    async def logout(self, user_id: int):
        await user_model.destroy_user_session(user_id)
        return Response(status_code=STATUS_CODE["END"])

    async def get_user(self, user_id: int):
        try:
            if not user_id:
                raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_USER_ID"])
            response_data = await user_model.get_user(user_id)
            if response_data is None:
                raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=STATUS_CODE["INTERNAL_SERVER_ERROR"],
                                detail=STATUS_MESSAGE["INTERNAL_SERVER_ERROR"])

        return JSONResponse(status_code=STATUS_CODE["OK"],
                            content={"message": None, "data": jsonable_encoder(response_data)})

    async def update_user(self, user_id: int, nickname: str, profile_image_path: Optional[str]):
        if not user_id:
            raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_USER_ID"])
        if not nickname:
            raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_NICKNAME"])
        req = {"userId": user_id, "nickname": nickname, "profileImagePath": profile_image_path}
        res = await user_model.update_user(req)
        if res is None:
            raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])
        if res == "UPDATE_PROFILE_IMAGE_FAILED":
            raise HTTPException(status_code=STATUS_CODE["INTERNAL_SERVER_ERROR"],
                                detail=STATUS_MESSAGE["UPDATE_PROFILE_IMAGE_FAILED"])
        return JSONResponse(status_code=STATUS_CODE["CREATED"],
                            content={"message": STATUS_MESSAGE["UPDATE_USER_DATA_SUCCESS"], "data": None})

    async def check_auth(self, user_id: int):
        if not user_id:
            raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_USER_ID"])
        user_data = await user_model.get_user(user_id)
        if not user_data:
            raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])
        # 값 비교는 != 사용
        if user_data[0]["user_id"] != user_id:
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

    async def change_password(self, user_id: int, password: str):
        if not password:
            raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_PASSWORD"])
        ok = await user_model.change_password({"userId": user_id, "password": password})
        if not ok:
            raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])
        return JSONResponse(status_code=STATUS_CODE["CREATED"],
                            content={"message": STATUS_MESSAGE["CHANGE_USER_PASSWORD_SUCCESS"], "data": None})

    async def check_email(self, email: str):
        res = await user_model.check_email(email)
        if res is False:
            return JSONResponse(status_code=STATUS_CODE["OK"],
                                content={"message": STATUS_MESSAGE["AVAILABLE_EMAIL"], "data": None})
        raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["ALREADY_EXIST_EMAIL"])

    async def check_nickname(self, nickname: str):
        res = await user_model.check_nickname(nickname)
        if res is False:
            return JSONResponse(status_code=STATUS_CODE["OK"],
                                content={"message": STATUS_MESSAGE["AVAILABLE_NICKNAME"], "data": None})
        raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["ALREADY_EXIST_NICKNAME"])

    async def delete_user(self, user_id: int):
        try:
            if not user_id:
                raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_USER_ID"])
            ok = await user_model.delete_user(user_id=user_id)
            if not ok:
                raise HTTPException(status_code=STATUS_CODE["NOT_FOUND"], detail=STATUS_MESSAGE["NOT_FOUND_USER"])
            return JSONResponse(status_code=STATUS_CODE["OK"],
                                content={"message": STATUS_MESSAGE["DELETE_USER_DATA_SUCCESS"], "data": None})
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=STATUS_CODE["INTERNAL_SERVER_ERROR"],
                                detail=STATUS_MESSAGE["INTERNAL_SERVER_ERROR"])
