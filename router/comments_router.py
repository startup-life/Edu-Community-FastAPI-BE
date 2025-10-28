from typing import Annotated
from fastapi import APIRouter, Body, Header, Depends, Path
from util.authUtil import is_logged_in
from controller.comments import CommentsController

router = APIRouter(prefix="/posts", tags=["comments"], responses={404: {"description": "Not found"}})

def _ctl() -> CommentsController:
    return CommentsController()

@router.post("/{pageId}/comments", status_code=201, dependencies=[Depends(is_logged_in)])
async def write_comment(
    commentContent: Annotated[str, Body(embed=True)],
    userId: int = Header(..., alias="userId"),
    pageId: int = Path(..., alias="pageId"),
):
    return await _ctl().write_comment(commentContent, userId, pageId)

@router.get("/{post_id}/comments", dependencies=[Depends(is_logged_in)])
async def get_comments(post_id: int = Path(..., alias="post_id")):
    return await _ctl().get_comments(post_id)

@router.patch("/{postId}/comments/{commentId}", dependencies=[Depends(is_logged_in)])
async def update_comment(
    commentContent: Annotated[str, Body(embed=True)],
    postId: int = Path(..., alias="postId"),
    commentId: int = Path(..., alias="commentId"),
    userId: int = Header(..., alias="userId"),
):
    return await _ctl().update_comment(commentContent, postId, commentId, userId)

@router.delete("/{postId}/comments/{commentId}", dependencies=[Depends(is_logged_in)])
async def delete_comment(
    postId: int = Path(..., alias="postId"),
    commentId: int = Path(..., alias="commentId"),
    userId: int = Header(..., alias="userId"),
):
    return await _ctl().delete_comment(postId, commentId, userId)
