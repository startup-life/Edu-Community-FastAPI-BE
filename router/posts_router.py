from fastapi import APIRouter, Body, Header, Path
from controller.posts import PostsController

router = APIRouter(prefix="/posts", tags=["posts"], responses={404: {"description": "Not found"}})

def _ctl() -> PostsController:
    return PostsController()

@router.post("/", status_code=201)
async def write_post(
    userid: int = Header(..., description="작성자 ID"),
    postTitle: str = Body(..., description="게시글 제목"),
    postContent: str = Body(..., description="게시글 내용"),
):
    return await _ctl().write_post(userid, postTitle, postContent)

@router.get("/")
async def get_posts():
    return await _ctl().get_posts()

@router.get("/{post_id}")
async def get_post(post_id: int = Path(..., description="게시글 ID")):
    return await _ctl().get_post(post_id)

@router.put("/{post_id}")
async def update_post(
    post_id: int = Path(..., description="게시글 ID"),
    postTitle: str = Body(..., description="새로운 제목"),
    postContent: str = Body(..., description="새로운 내용"),
):
    return await _ctl().update_post(post_id, postTitle, postContent)

@router.delete("/{post_id}")
async def soft_delete_post(post_id: int = Path(..., description="게시글 ID")):
    return await _ctl().soft_delete_post(post_id)
