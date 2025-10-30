from typing import Annotated
from fastapi import APIRouter, Body, Header, Depends, Path
from util.authUtil import is_logged_in
from controller.comments import CommentsController

# 댓글 관련 라우터 설정
# Prefix: /posts
router = APIRouter(prefix="/posts/{post_id}/comments", responses={404: {"description": "Not found"}})

# 파이썬에서는 _를 접두사로 사용하면 비공개(private)용으로 사용하겠다는 암묵적 신호
# 외부 모듈에서 직접 호출하지 말라는 개발자 간의 약속
# CommentsController 인스턴스를 반환하는 헬퍼 함수
def _ctl() -> CommentsController:
    return CommentsController()

# 새로운 댓글 작성 엔드포인트
@router.post("", status_code=201, dependencies=[Depends(is_logged_in)])
async def write_comment(
    commentContent: Annotated[str, Body(embed=True)],
    userId: int = Header(..., alias="userId"),
    pageId: int = Path(..., alias="post_id"),
):
    return await _ctl().write_comment(commentContent, userId, pageId)

# 댓글 조회 엔드포인트
@router.get("", dependencies=[Depends(is_logged_in)])
async def get_comments(post_id: int = Path(..., alias="post_id")):
    return await _ctl().get_comments(post_id)

# 댓글 수정 엔드포인트
@router.patch("/{commentId}", dependencies=[Depends(is_logged_in)])
async def update_comment(
    commentContent: Annotated[str, Body(embed=True)],
    postId: int = Path(..., alias="post_id"),
    commentId: int = Path(..., alias="commentId"),
    userId: int = Header(..., alias="userId"),
):
    return await _ctl().update_comment(commentContent, postId, commentId, userId)

# 댓글 삭제 엔드포인트
@router.delete("/{commentId}", dependencies=[Depends(is_logged_in)])
async def delete_comment(
    postId: int = Path(..., alias="post_id"),
    commentId: int = Path(..., alias="commentId"),
    userId: int = Header(..., alias="userId"),
):
    return await _ctl().delete_comment(postId, commentId, userId)