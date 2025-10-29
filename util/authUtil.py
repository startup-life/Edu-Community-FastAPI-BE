# util/auth_util.py
from typing import Optional
from fastapi import Depends, Header, HTTPException
from pymysql.cursors import DictCursor

from util.constant.httpStatusCode import STATUS_CODE
from util.constant.httpStatusCode import STATUS_MESSAGE
from model import user_model  # get_connection: 콜러블(호출 X)

# 인증 검사 함수
# FastAPI의 Depends로 주입 가능
# 헤더에서 session과 userid를 추출하여 인증 상태를 확인
# 성공 시 True 반환, 실패 시 HTTPException 발생
def is_logged_in(
    session: Optional[str] = Header(None, alias="session"),
    userid: Optional[int] = Header(None, alias="userid"),
    db = Depends(user_model.get_connection),
) -> bool:
    # 1) userId 검증
    if not userid:
        raise HTTPException(
            status_code=STATUS_CODE["UNAUTHORIZED"],
            detail=STATUS_MESSAGE["REQUIRED_AUTHORIZATION"],
        )

    # 2) DB에서 session_id 조회 (pymysql: %s 플레이스홀더)
    with db.cursor(DictCursor) as cursor:
        cursor.execute(
            "SELECT session_id FROM user_table WHERE user_id = %s",
            (userid,),
        )
        row = cursor.fetchone()  # {'session_id': '...'} or None

    # 3) 세션 검증
    if not row or not session or session != row["session_id"]:
        raise HTTPException(
            status_code=STATUS_CODE["UNAUTHORIZED"],
            detail=STATUS_MESSAGE["REQUIRED_AUTHORIZATION"],
        )

    return True