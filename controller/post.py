from typing import Annotated, Optional, Union, IO
import io
from fastapi import APIRouter, HTTPException, Header, Path, Body, Query, UploadFile, File, Depends
from starlette.concurrency import run_in_threadpool
from utils.constant.httpStatusCode import STATUS_CODE
from utils.constant.httpStatusCode import STATUS_MESSAGE
from model import post_model
from fastapi.responses import JSONResponse
import shutil
from pathlib import Path as FSPath
import os
import uuid
from utils.authUtil import is_logged_in

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    responses={404: {"description": "Not found"}},
)

# 게시글 작성 
@router.post("", status_code=201, dependencies=[Depends(is_logged_in)])
async def write_post(
    user_id: int = Header(..., alias="userId"),
    post_title: str = Body(..., alias="postTitle"),
    post_content: str = Body(..., alias="postContent"),
    attach_file_path: Optional[str] = Body(None, alias="attachFilePath"),
):
    print(user_id)
    print(post_title)
    print(post_content)
    print(attach_file_path)
    # 검증
    if not post_title:
        raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_TITLE"])
    if len(post_title) > 26:
        raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_TITLE_LENGTH"])
    if not post_content:
        raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_CONTENT"])
    if len(post_content) > 1500:
        raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_CONTENT_LENGTH"])

    # DB 호출 (키워드 인자로 통일, 파일이 없어도 None으로 전달)
    response_data = await post_model.create_post(
    user_id=user_id,
    post_title=post_title,
    post_content=post_content,
    attach_file_path=attach_file_path,  # 없으면 None
    )

    if response_data == STATUS_MESSAGE["NOT_FOUND_USER"]:
        raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_FOUND_USER"])
    if not response_data:
        raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["WRITE_POST_FAILED"])

    
    return JSONResponse(
        status_code=STATUS_CODE["CREATED"],
        content={"message": STATUS_MESSAGE["WRITE_POST_SUCCESS"], "data": response_data},
    )

# 게시글 목록 조회
@router.get("", dependencies=[Depends(is_logged_in)])
async def get_post_list(
    offset: str = Query(..., description="조회 시작 위치"),
    limit:  str = Query(..., description="조회 개수"),
):
    from datetime import datetime

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
        post_id      = _pick(row, "post_id", "postId")
        post_title   = _pick(row, "post_title", "postTitle", "title")
        post_content = _pick(row, "post_content", "postContent", "content")
        user_id      = _pick(row, "user_id", "userId")
        nickname     = _pick(row, "nickname")
        file_id      = _pick(row, "file_id", "fileId")
        created_at   = _iso(_pick(row, "created_at", "createdAt"))
        updated_at   = _iso(_pick(row, "updated_at", "updatedAt"))
        deleted_at   = _iso(_pick(row, "deleted_at", "deletedAt"))
        like_val     = _pick(row, "like", "likeCount")
        comment_cnt  = _pick(row, "comment_count", "commentCount")
        hits         = _pick(row, "hits", "viewCount")
        profile_img  = _pick(row, "profile_image_path", "profileImagePath")

        return {
            # snake
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

    try:
        if not offset or not limit:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_OFFSET_OR_LIMIT"])
        try:
            o = int(offset, 10); l = int(limit, 10)
        except ValueError:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_OFFSET_OR_LIMIT"])

        rows = await post_model.get_post_list(offset=o, limit=l)

        if rows is None:
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE.get("GET_POST_LIST_FAILED", "get_post_list_failed"))
        if isinstance(rows, list) and len(rows) == 0:
            raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])

        data_out = [_augment_row(r) for r in (rows if isinstance(rows, list) else [rows])]

        payload = {
            "message": STATUS_MESSAGE.get("GET_POST_LIST_SUCCESS", "get_post_list_success"),
            "data": data_out,  # 목록은 배열 유지
        }
        return {
            "status_code": STATUS_CODE["OK"],
            "status_message": STATUS_MESSAGE["GET_POST_LIST_SUCCESS"],
            "data": data_out
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE.get("GET_POST_LIST_FAILED", "get_post_list_failed"))


# 게시글 단일 조회 
@router.get("/{post_id}")
async def get_post(post_id: int = Path(..., gt=0, description="게시글 ID")):
    try:
        response_data = await post_model.get_post(
            post_id=post_id
        )
        print("response_data", response_data)
        if not response_data:
            raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_FOUND_POST"])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["GET_POST_FAILED"])

    return {
        "message": None,
        "data": response_data
    }

# 게시글 수정 
@router.patch("/{post_id}", dependencies=[Depends(is_logged_in)])
async def update_post(
    post_id: int = Path(..., gt=0, description="수정할 게시글 ID"),
    user_id: int = Header(..., alias="userId"),
    post_title: str = Body(None, alias="postTitle"),
    post_content: str = Body(None, alias="postContent"),
    attach_file_path: Optional[str] = Body(None, alias="attachFilePath"),
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
        attachFilePath=attach_file_path
    )

    if not response_data:
        raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])

    return {
        "status_message": STATUS_MESSAGE["UPDATE_POST_SUCCESS"],
        "data": response_data
    }

# 게시글 삭제
@router.delete("/{post_id}")
async def delete_post(post_id: int = Path(..., gt=0, description="삭제할 게시글 ID")):
    try:
        response_data = await post_model.delete_post(
            post_id
        )
        if not response_data:
            raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])
    except HTTPException:
        raise
    
    return {
        "status_code": STATUS_CODE["CREATED"],
        "status_message": STATUS_MESSAGE["DELETE_POST_SUCCESS"],
        "data": response_data
    }


POST_DIR = FSPath("./public/image/post")

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

@router.post("/upload/attach-file")
async def upload_profile_image(
    postFile: bytes = File(...)
):

    filename = f"{uuid.uuid4()}.png"

    if not postFile:
        raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_FILE"])

    dest_path = os.path.join(POST_DIR, filename)

    await _save_upload_file(postFile, dest_path)
    
    return {
        "status_code": STATUS_CODE["CREATED"],
        "status_message": STATUS_MESSAGE["FILE_UPLOAD_SUCCESS"],
        "data": {"filePath": f"/public/image/post/{filename}", "fileName": filename}
    }  