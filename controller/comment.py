import json
from fastapi import APIRouter, Header, Body, Form
from fastapi import HTTPException, Path, Depends
from utils.constant.httpStatusCode import STATUS_CODE
from utils.constant.httpStatusCode import STATUS_MESSAGE
from model import comment_model
from utils.authUtil import is_logged_in
from starlette.concurrency import run_in_threadpool
from typing import Annotated, Any
from fastapi.responses import JSONResponse


router = APIRouter(
    prefix=f"/posts",
    tags=["comments"],
    responses={404: {"description": "Not found"}},
)

# 댓글 작성
@router.post("/{pageId}/comments", dependencies=[Depends(is_logged_in)], status_code=STATUS_CODE["CREATED"])
async def write_comment(
    comment_content: Annotated[str, Body(embed=True, alias="commentContent")],
    user_id: int = Header(..., alias="userId"),
    post_id: int = Path(..., alias="pageId"),
):
    try:
        content = (comment_content or "").strip()
        if not content or len(content) > 1000:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_CONTENT"])


        response_data = await comment_model.write_comment(
            post_id =post_id,
            user_id=user_id,
            comment_content=content,
        )
        print(response_data)
        if response_data is None or response_data == "insert_error":
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["WRITE_COMMENT_FAILED"])

        return {
            "message": STATUS_MESSAGE["WRITE_COMMENT_SUCCESS"],
            "data": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        print("write_comment error:", repr(e))
        raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["WRITE_COMMENT_FAILED"])

# 댓글 조회
@router.get("/{post_id}/comments", dependencies=[Depends(is_logged_in)])
async def get_comments(
    post_id: int = Path(..., alias="post_id")
):
    try:
        if not post_id:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_ID"])
        response_data = await comment_model.get_comments(
            post_id
        )

        if not response_data:
            return {
                "status_code": STATUS_CODE["OK"],
                "status_message": STATUS_MESSAGE["GET_COMMENTS_SUCCESS"],
                "data": []
            }
    except Exception as e:
        raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["GET_COMMENTS_FAILED"])

    return {
        "message": None,
        "data": response_data
    }

# 댓글 수정
@router.patch("/{postId}/comments/{commentId}", dependencies=[Depends(is_logged_in)])
async def update_comment(
    comment_content: Annotated[str, Body(embed=True, alias="commentContent")],
    post_id: int = Path(..., alias="postId"),
    comment_id: int = Path(..., alias="commentId"),
    user_id: int = Header(..., alias="userId"),
):
    try:
        if not post_id:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_ID"])
        if not comment_id:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_ID"])
        if not comment_content:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_CONTENT"])
        if len(comment_content) > 1000:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_CONTENT"])

        await comment_model.update_comment(
            post_id=post_id,
            comment_id=comment_id,
            user_id=user_id,
            comment_content=comment_content
        )
        
        return {
            "message": STATUS_MESSAGE["UPDATE_COMMENT_SUCCESS"],
            "data": None
        }
    except Exception as e:
        return JSONResponse(status_code=STATUS_CODE["UNAUTHORIZED"], content={"message": STATUS_MESSAGE["REQUERED_AUTHORIZATION"], "data": None})

# 댓글 삭제
@router.delete("/{postId}/comments/{commentId}", dependencies=[Depends(is_logged_in)])
async def delete_comment(
    post_id: int = Path(..., description="게시글 ID", alias="postId"),
    comment_id: int = Path(..., description="댓글 ID", alias="commentId"),
    user_id: int = Header(..., description="사용자 ID", alias="userId"),
):
    print("user_id - delete_comment", user_id)
    print("post_id - delete_comment", post_id)
    print("comment_id - delete_comment", comment_id)
    try:
        if not post_id:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_POST_ID"])
        if not comment_id:
            raise HTTPException(STATUS_CODE["BAD_REQUEST"], STATUS_MESSAGE["INVALID_COMMENT_ID"])

        result = await comment_model.delete_comment(
            post_id=post_id, 
            comment_id=comment_id, 
            user_id=user_id
            )

        if not result:
            raise HTTPException(STATUS_CODE["NOT_FOUND"], STATUS_MESSAGE["NOT_A_SINGLE_POST"])
        if result == 'no_auth_error':
            raise HTTPException(STATUS_CODE["UNAUTHORIZED"], STATUS_MESSAGE["AUTHORIZATION"])
        if result == 'delete_error':
            raise HTTPException(STATUS_CODE["INTERNAL_SERVER_ERROR"], STATUS_MESSAGE["INTERNAL_SERVER_ERROR"])

        return {
            "message": STATUS_MESSAGE["DELETE_COMMENT_SUCCESS"],
            "data": None,
        }
    except Exception as e:
        return JSONResponse(status_code=STATUS_CODE["UNAUTHORIZED"], content={"message": STATUS_MESSAGE["REQUERED_AUTHORIZATION"], "data": None})
        
