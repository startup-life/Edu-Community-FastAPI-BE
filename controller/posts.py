from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi.responses import JSONResponse

# 인메모리 더미 데이터
users = [
    {"user_id": 1, "nickname": "앨리스"},
    {"user_id": 2, "nickname": "밥"},
]

posts: List[Dict[str, Any]] = [
    {
        "post_id": 1,
        "post_title": "첫 번째 게시글",
        "post_content": "첫 번째 내용입니다.",
        "user_id": 1,
        "nickname": "앨리스",
        "like": 0,
        "comment_count": 0,
        "hits": 10,
        "created_at": "2024-12-10T10:00:00Z",
        "updated_at": "2024-12-10T10:00:00Z",
        "deleted_at": None,
    },
    {
        "post_id": 2,
        "post_title": "두 번째 글",
        "post_content": "내용이 있습니다.",
        "user_id": 2,
        "nickname": "밥",
        "like": 2,
        "comment_count": 1,
        "hits": 15,
        "created_at": "2024-12-11T11:00:00Z",
        "updated_at": "2024-12-11T11:00:00Z",
        "deleted_at": None,
    },
]

"""
유틸 함수
"""

"""
현재 UTC 시간을 ISO 문자열로 반환
게시글 생성 및 수정 시간에 사용
"""
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

"""
사용자 ID로 닉네임 조회
해당 사용자가 없으면 "익명" 반환
"""
def _get_user_nickname(user_id: int) -> str:
    u = next((u for u in users if u["user_id"] == user_id), None)
    return u["nickname"] if u else "익명"

class PostsController:
    async def write_post(self, userid: int, postTitle: str, postContent: str):
        new_post_id = len(posts) + 1
        nickname = _get_user_nickname(userid)
        now_iso = _now()
        """
        포스트 글 형식 맞추기 위해서 new_post 생성
        """
        new_post = {
            "post_id": new_post_id,
            "post_title": postTitle,
            "post_content": postContent,
            "user_id": userid,
            "nickname": nickname,
            "like": 0,
            "comment_count": 0,
            "hits": 0,
            "created_at": now_iso,
            "updated_at": now_iso,
            "deleted_at": None,
        }
        posts.append(new_post)
        return {"data": new_post}

    async def get_posts(self):
        """
        deleted_at이 없는 활성 게시글만 필터링하여 반환
        """
        active = [p for p in posts if not p["deleted_at"]]
        return {"data": active}

    async def get_post(self, post_id: int):
        post = next((p for p in posts if p["post_id"] == post_id and not p["deleted_at"]), None)
        if not post:
            return JSONResponse(status_code=404, content={"data": None})
        post["hits"] += 1
        return {"data": post}

    async def update_post(self, post_id: int, postTitle: str, postContent: str):
        post = next((p for p in posts if p["post_id"] == post_id and not p["deleted_at"]), None)
        if not post:
            return JSONResponse(status_code=404, content={"data": None})
        post["post_title"] = postTitle
        post["post_content"] = postContent
        post["updated_at"] = _now()
        return {"data": post}

    async def soft_delete_post(self, post_id: int):
        post = next((p for p in posts if p["post_id"] == post_id and not p["deleted_at"]), None)
        if not post:
            return JSONResponse(status_code=404, content={"data": None})
        post["deleted_at"] = _now()
        return {"data": None}
