
from typing import Optional
from fastapi import Depends, Header, HTTPException
from pymysql.cursors import DictCursor

from util.constant.httpStatusCode import STATUS_CODE
from util.constant.httpStatusCode import STATUS_MESSAGE
from model import user_model  # get_connection: 콜러블(호출 X)

def is_logged_in(
    session: Optional[str] = Header(None, alias="session"), # 요청 헤더의 session 값을 받음
    userid: Optional[int] = Header(None, alias="userid"), # 요청 헤더의 userId 값을 받음
    db = Depends(user_model.get_connection), # DB 연결 의존성 주입
) -> bool:
    # 1) userId 검증
    # - 헤더에 userId가 없으면 인증되지 않은 요청으로 판단
    if not userid:
        raise HTTPException(
            status_code=STATUS_CODE["UNAUTHORIZED"],
            detail=STATUS_MESSAGE["REQUIRED_AUTHORIZATION"],
        )

    # 2) DB에서 session_id 조회 (pymysql: %s 플레이스홀더)
    # - pymysql의 DictCursor를 사용하여 결과를 dict 형태로 받음
    # - SQL 인젝션 방지를 위해 %s 플레이스홀더 사용
    with db.cursor(DictCursor) as cursor:
        cursor.execute(
            "SELECT session_id FROM user_table WHERE user_id = %s",
            (userid,),
        )
        row = cursor.fetchone()  # {'session_id': '...'} or None

    # 3) 세션 검증
    # - 세션 정보가 없거나, 요청 헤더에 session이 없거나, DB에 저장된 세션과 헤더의 세션이 불일치 할 경우 인증 실패
    if not row or not session or session != row["session_id"]:
        raise HTTPException(
            status_code=STATUS_CODE["UNAUTHORIZED"],
            detail=STATUS_MESSAGE["REQUIRED_AUTHORIZATION"],
        )

    # 검증 통과시 로그인 상태 반환 -> 조건이 전부 통과된 경우 True를 반환
    return True