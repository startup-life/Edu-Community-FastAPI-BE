from typing import Optional
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from util.constant.httpStatusCode import STATUS_CODE, STATUS_MESSAGE
from model import post_model

# 입력으로 들어오는 값을 ISO 8601 형식의 문자열로 변환하는 헬퍼 함수
def _iso(v):
    if v is None: return None
    if isinstance(v, datetime): return v.isoformat(timespec="seconds")
    return str(v)

# 여러 키 중에서 첫 번째로 존재하는 값을 반환하는 헬퍼 함수
def _pick(row: dict, *keys, default=None):
    for k in keys:
        if isinstance(row, dict) and k in row and row[k] is not None:
            return row[k]
    return default

# 데이터베이스에서 가져온 게시글 데이터를 표준화된 형태로 변환 하는 헬퍼 함수
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
    # 새로운 게시물 작성
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

    # 게시물 목록 조회
    async def get_post_list(self, offset: str, limit: str):
        if not offset or not limit:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_OFFSET_OR_LIMIT"])
        try:
            offset_int = int(offset, 10)
            limit_int = int(limit, 10)
        except ValueError:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_OFFSET_OR_LIMIT"])

        try:
            rows = await post_model.get_post_list(offset=offset_int, limit=limit_int)
            if rows is None:
                raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"],
                                    STATUS_MESSAGE.get("GET_POST_LIST_FAILED", "get_post_list_failed"))
            if isinstance(rows, list) and len(rows) == 0:
                raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])
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

    # 단일 게시물 조회
    async def get_post(self, post_id: int):
        try:
            response_data = await post_model.get_post(post_id=post_id)
            if not response_data:
                raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_FOUND_POST"])
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["GET_POST_FAILED"])
        return {"message": None, "data": response_data}

    # 게시물 수정
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

    # 게시물 삭제
    async def delete_post(self, post_id: int):
        try:
            ok = await post_model.delete_post(post_id)
            if not ok:
                raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])
            return {
                "status_code": STATUS_CODE["CREATED"],
                "status_message": STATUS_MESSAGE["DELETE_POST_SUCCESS"],
                "data": ok,
            }
        except HTTPException:
            raise
