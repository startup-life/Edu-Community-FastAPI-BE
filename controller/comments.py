from typing import Annotated
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from util.constant.httpStatusCode import STATUS_CODE, STATUS_MESSAGE
from model import comment_model

class CommentsController:
    async def write_comment(self, comment_content: str, user_id: int, post_id: int):
        try:
            content = (comment_content or "").strip()
            if not content or len(content) > 1000:
                raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_CONTENT"])

            res = await comment_model.write_comment(post_id=post_id, user_id=user_id, comment_content=content)
            if res is None or res == "insert_error":
                raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["WRITE_COMMENT_FAILED"])

            return {"message": STATUS_MESSAGE["WRITE_COMMENT_SUCCESS"], "data": None}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["WRITE_COMMENT_FAILED"])

    async def get_comments(self, post_id: int):
        try:
            if not post_id:
                raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_ID"])

            data = await comment_model.get_comments(post_id)
            if not data:
                return {
                    "status_code": STATUS_CODE["OK"],
                    "status_message": STATUS_MESSAGE["GET_COMMENTS_SUCCESS"],
                    "data": [],
                }
            return {"message": None, "data": data}
        except Exception:
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["GET_COMMENTS_FAILED"])

    async def update_comment(self, comment_content: str, post_id: int, comment_id: int, user_id: int):
        try:
            if not post_id:
                raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_ID"])
            if not comment_id:
                raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_ID"])
            if not comment_content or len(comment_content) > 1000:
                raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_CONTENT"])

            await comment_model.update_comment(
                post_id=post_id, comment_id=comment_id, user_id=user_id, comment_content=comment_content
            )
            return {"message": STATUS_MESSAGE["UPDATE_COMMENT_SUCCESS"], "data": None}
        except Exception:
            return JSONResponse(
                status_code=STATUS_CODE["UNAUTHORIZED"],
                content={"message": STATUS_MESSAGE["REQUERED_AUTHORIZATION"], "data": None},
            )

    async def delete_comment(self, post_id: int, comment_id: int, user_id: int):
        try:
            if not post_id:
                raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_ID"])
            if not comment_id:
                raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_ID"])

            result = await comment_model.delete_comment(post_id=post_id, comment_id=comment_id, user_id=user_id)

            if not result:
                raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])
            if result == "no_auth_error":
                raise HTTPException(STATUS_CODE["UNAUTHORIZED"], STATUS_MESSAGE["AUTHORIZATION"])
            if result == "delete_error":
                raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["INTERNAL_SERVER_ERROR"])

            return {"message": STATUS_MESSAGE["DELETE_COMMENT_SUCCESS"], "data": None}
        except Exception:
            return JSONResponse(
                status_code=STATUS_CODE["UNAUTHORIZED"],
                content={"message": STATUS_MESSAGE["REQUERED_AUTHORIZATION"], "data": None},
            )
