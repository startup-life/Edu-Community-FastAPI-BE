from typing import Optional
from fastapi import APIRouter, Body, Header, Path
from controller.posts import PostsController

router = APIRouter(prefix="/posts", tags=["posts"], responses={404: {"description": "Not found"}})

def _ctl() -> PostsController:
    return PostsController()

@router.post("", status_code=201)
async def write_post(
    userId: int = Header(..., alias="userId"),
    postTitle: str = Body(..., alias="postTitle"),
    postContent: str = Body(..., alias="postContent"),
    attachFilePath: Optional[str] = Body(None, alias="attachFilePath"),
):
    return await _ctl().write_post(userId, postTitle, postContent, attachFilePath)

@router.get("")
async def get_post_list():
    return await _ctl().get_post_list()

@router.get("/{post_id}")
async def get_post(post_id: int = Path(..., gt=0, description="게시글 ID")):
    return await _ctl().get_post(post_id)

@router.patch("/{post_id}")
async def update_post(
    post_id: int = Path(..., gt=0, description="수정할 게시글 ID"),
    userId: int = Header(..., alias="userId"),
    postTitle: Optional[str] = Body(None, alias="postTitle"),
    postContent: Optional[str] = Body(None, alias="postContent"),
    attachFilePath: Optional[str] = Body(None, alias="attachFilePath"),
):
    return await _ctl().update_post(post_id, userId, postTitle, postContent, attachFilePath)

@router.delete("/{post_id}")
async def delete_post(post_id: int = Path(..., gt=0, description="삭제할 게시글 ID")):
    return await _ctl().delete_post(post_id)
