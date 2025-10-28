from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi.responses import JSONResponse

# 인메모리 더미 데이터
users = [
    {"user_id": 1, "nickname": "앨리스"},
    {"user_id": 2, "nickname": "밥"},
]

comments: List[Dict[str, Any]] = [
    {
        "comment_id": 1,
        "comment_content": "좋은 글이네요.",
        "post_id": 1,
        "user_id": 2,
        "nickname": "밥",
        "created_at": "2024-12-10T10:00:00Z",
        "updated_at": "2024-12-10T10:00:00Z",
        "deleted_at": None,
    },
    {
        "comment_id": 2,
        "comment_content": "감사합니다!",
        "post_id": 1,
        "user_id": 1,
        "nickname": "앨리스",
        "created_at": "2024-12-10T10:05:00Z",
        "updated_at": "2024-12-10T10:05:00Z",
        "deleted_at": None,
    },
]

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _get_user_nickname(user_id: int) -> str:
    u = next((u for u in users if u["user_id"] == user_id), None)
    return u["nickname"] if u else "익명"

class CommentsController:
    async def get_comments(self, post_id: int):
        filtered = [c for c in comments if c["post_id"] == post_id and not c["deleted_at"]]
        return {"data": filtered}

    async def write_comment(self, post_id: int, userid: int, commentContent: str):
        new_id = len(comments) + 1
        nickname = _get_user_nickname(userid)
        now_iso = _now()
        new_comment = {
            "comment_id": new_id,
            "comment_content": commentContent,
            "post_id": post_id,
            "user_id": userid,
            "nickname": nickname,
            "created_at": now_iso,
            "updated_at": now_iso,
            "deleted_at": None,
        }
        comments.append(new_comment)
        return {"data": new_comment}

    async def update_comment(self, post_id: int, comment_id: int, commentContent: str):
        comment = next(
            (c for c in comments if c["post_id"] == post_id and c["comment_id"] == comment_id and not c["deleted_at"]),
            None,
        )
        if not comment:
            return JSONResponse(status_code=404, content={"data": None})
        comment["comment_content"] = commentContent
        comment["updated_at"] = _now()
        return {"data": comment}

    async def soft_delete_comment(self, post_id: int, comment_id: int):
        comment = next(
            (c for c in comments if c["post_id"] == post_id and c["comment_id"] == comment_id and not c["deleted_at"]),
            None,
        )
        if not comment:
            return JSONResponse(status_code=404, content={"data": None})
        comment["deleted_at"] = _now()
        return {"data": None}
