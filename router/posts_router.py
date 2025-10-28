from typing import Optional
from fastapi import APIRouter, Body, Header, Query, Path, Depends
from util.authUtil import is_logged_in
from controller.posts import PostsController

router = APIRouter(prefix="/posts", tags=["posts"], responses={404: {"description": "Not found"}})

def _ctl() -> PostsController:
    return PostsController()

@router.post("", status_code=201, dependencies=[Depends(is_logged_in)])
async def write_post(
    user_id: int = Header(..., alias="userId"),
    post_title: str = Body(..., alias="postTitle"),
    post_content: str = Body(..., alias="postContent"),
    attach_file_path: Optional[str] = Body(None, alias="attachFilePath"),
):
    return await _ctl().write_post(user_id, post_title, post_content, attach_file_path)

@router.get("", dependencies=[Depends(is_logged_in)])
async def get_post_list():
    return await _ctl().get_post_list()

@router.get("/{post_id}", dependencies=[Depends(is_logged_in)])
async def get_post(post_id: int = Path(..., gt=0, description="게시글 ID")):
    return await _ctl().get_post(post_id)

@router.patch("/{post_id}", dependencies=[Depends(is_logged_in)])
async def update_post(
    post_id: int = Path(..., gt=0, description="수정할 게시글 ID"),
    user_id: int = Header(..., alias="userId"),
    post_title: Optional[str] = Body(None, alias="postTitle"),
    post_content: Optional[str] = Body(None, alias="postContent"),
    attach_file_path: Optional[str] = Body(None, alias="attachFilePath"),
):
    return await _ctl().update_post(post_id, user_id, post_title, post_content, attach_file_path)

@router.delete("/{post_id}", dependencies=[Depends(is_logged_in)])
async def delete_post(post_id: int = Path(..., gt=0, description="삭제할 게시글 ID")):
    return await _ctl().delete_post(post_id)
