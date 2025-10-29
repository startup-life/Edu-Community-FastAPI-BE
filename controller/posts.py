from typing import Optional
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from util.constant.httpStatusCode import STATUS_CODE, STATUS_MESSAGE
from model import post_model

def _iso(v):
    if v is None: return None
    if isinstance(v, datetime): return v.isoformat(timespec="seconds")
    return str(v)

def _pick(row: dict, *keys, default=None):
    for k in keys:
        if isinstance(row, dict) and k in row and row[k] is not None:
            return row[k]
    return default

def _augment_row(row: dict) -> dict:
    if not isinstance(row, dict):
        return {"raw": str(row)}
    post_id = _pick(row, "post_id", "postId")
    post_title = _pick(row, "post_title", "postTitle", "title")
    post_content = _pick(row, "post_content", "postContent", "content")
    user_id = _pick(row, "user_id", "userId")
    nickname = _pick(row, "nickname")
    file_id = _pick(row, "file_id", "fileId")
    created_at = _iso(_pick(row, "created_at", "createdAt"))
    updated_at = _iso(_pick(row, "updated_at", "updatedAt"))
    deleted_at = _iso(_pick(row, "deleted_at", "deletedAt"))
    like_val = _pick(row, "like", "likeCount")
    comment_cnt = _pick(row, "comment_count", "commentCount")
    hits = _pick(row, "hits", "viewCount")
    profile_img = _pick(row, "profile_image_path", "profileImagePath")
    return {
        "post_id": post_id,
        "post_title": post_title,
        "post_content": post_content,
        "user_id": user_id,
        "nickname": nickname,
        "file_id": file_id,
        "created_at": created_at,
        "updated_at": updated_at,
        "deleted_at": deleted_at,
        "like": like_val,
        "comment_count": comment_cnt,
        "hits": hits,
        "profileImagePath": profile_img,
    }

class PostsController:
    async def write_post(
        self,
        user_id: int,
        post_title: str,
        post_content: str,
        attach_file_path: Optional[str],
    ):
        if not post_title:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_TITLE"])
        if len(post_title) > 26:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_TITLE_LENGTH"])
        if not post_content:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_CONTENT"])
        if len(post_content) > 1500:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_CONTENT_LENGTH"])

        response_data = await post_model.create_post(
            user_id=user_id,
            post_title=post_title,
            post_content=post_content,
            attach_file_path=attach_file_path,
        )

        if response_data == STATUS_MESSAGE["NOT_FOUND_USER"]:
            raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_FOUND_USER"])

        if not response_data:
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["WRITE_POST_FAILED"])

        return JSONResponse(
            status_code=STATUS_CODE["CREATED"],
            content={"message": STATUS_MESSAGE["WRITE_POST_SUCCESS"], "data": response_data},
        )

    async def get_post_list(self):
        try:
            rows = await post_model.get_post_list()

            if rows is None:
                raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"],
                                    STATUS_MESSAGE.get("GET_POST_LIST_FAILED", "get_post_list_failed"))

            if isinstance(rows, list) and len(rows) == 0:
                raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])

            # 조회 결과(rows)가 단일 dict이든 리스트이든 상관없이 동일한 형태로 처리하기 위해
            # rows가 리스트이면 그대로 순회하고, 단일 dict이면 [rows]로 감싸 리스트처럼 처리
            # 각 항목(r)에 대해 _augment_row() 함수를 호출하여 필드명을 통일하고 포맷(날짜 등)을 정규화한 새 dict 생성
            data_out = [_augment_row(r) for r in (rows if isinstance(rows, list) else [rows])]

            return {
                "status_code": STATUS_CODE["OK"],
                "status_message": STATUS_MESSAGE["GET_POST_LIST_SUCCESS"],
                "data": data_out,
            }

        except HTTPException:
            raise

        except Exception:
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"],
                                STATUS_MESSAGE.get("GET_POST_LIST_FAILED", "get_post_list_failed"))

    async def get_post(self, post_id: int):
        try:
            response_data = await post_model.get_post(post_id=post_id)

            if not response_data:
                raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_FOUND_POST"])

            return {"message": None, "data": response_data}

        except HTTPException:
            raise

        except Exception:
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["GET_POST_FAILED"])

    async def update_post(
        self,
        post_id: int,
        user_id: int,
        post_title: Optional[str],
        post_content: Optional[str],
        attach_file_path: Optional[str],
    ):
        if post_title is not None and len(post_title) > 26:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_TITLE_LENGTH"])

        if post_content is not None and len(post_content) > 1500:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_CONTENT_LENGTH"])

        response_data = await post_model.update_post(
            postId=post_id,
            userId=user_id,
            postTitle=post_title,
            postContent=post_content,
            attachFilePath=attach_file_path,
        )

        if not response_data:
            raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])

        return {"status_message": STATUS_MESSAGE["UPDATE_POST_SUCCESS"], "data": response_data}

    async def delete_post(self, post_id: int):
        try:
            response_data = await post_model.delete_post(post_id)
            if not response_data:
                raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])
            return {
                "status_code": STATUS_CODE["CREATED"],
                "status_message": STATUS_MESSAGE["DELETE_POST_SUCCESS"],
                "data": response_data,
            }
        except HTTPException:
            raise
