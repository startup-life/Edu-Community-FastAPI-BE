from fastapi import APIRouter, Body, Header, Path
from controller.comments import CommentsController

router = APIRouter(
    prefix="/posts/{post_id}/comments",
    tags=["comments"],
    responses={404: {"description": "Not found"}},
)

def _ctl() -> CommentsController:
    return CommentsController()

@router.get("/")
async def get_comments(post_id: int = Path(..., description="게시글 ID")):
    return await _ctl().get_comments(post_id)

@router.post("/", status_code=201)
async def write_comment(
    post_id: int = Path(..., description="게시글 ID"),
    userid: int = Header(..., description="작성자 ID"),
    commentContent: str = Body(..., description="댓글 내용", embed=True),
):
    return await _ctl().write_comment(post_id, userid, commentContent)

@router.put("/{comment_id}")
async def update_comment(
    post_id: int = Path(..., description="게시글 ID"),
    comment_id: int = Path(..., description="댓글 ID"),
    commentContent: str = Body(..., description="수정할 내용", embed=True),
):
    return await _ctl().update_comment(post_id, comment_id, commentContent)

@router.delete("/{comment_id}")
async def soft_delete_comment(
    post_id: int = Path(..., description="게시글 ID"),
    comment_id: int = Path(..., description="댓글 ID"),
):
    return await _ctl().soft_delete_comment(post_id, comment_id)
