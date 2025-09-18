# db.py
from typing import Optional, Dict, Any, Union
from database import index
import pymysql
from pymysql import MySQLError as Error
from utils.constant.httpStatusCode import STATUS_CODE, STATUS_MESSAGE
from starlette.concurrency import run_in_threadpool
from pymysql.cursors import DictCursor

def get_connection():
    """MySQL 연결을 반환 (동기)."""
    return pymysql.connect(
        **index.MYSQL_DB_CONFIG,
        cursorclass=DictCursor,
        autocommit=False,
    )

async def db_call(fn, *args, **kwargs):
    return await run_in_threadpool(fn, *args, **kwargs)

async def signup_user(
    email: str,
    password: str,
    nickname: str,
    profile_image_path: Optional[str] = None,
) -> Union[str, Dict[str, Optional[int]], None]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # 1) 이메일 중복 검사(UNIQUE 제약도 DB에 반드시 설정!)
            cur.execute("SELECT 1 FROM user_table WHERE email = %s LIMIT 1;", (email,))
            if cur.fetchone():
                conn.rollback()
                return "already_exist_email"

            # 2) 유저 생성 (password 컬럼 길이 확인: VARCHAR(60) 이상)
            cur.execute(
                """
                INSERT INTO user_table (email, password, nickname)
                VALUES (%s, %s, %s);
                """,
                (email, password, nickname),
            )
            user_id = cur.lastrowid

            profile_image_id: Optional[int] = None

            # 3) 프로필 이미지 처리(선택)
            if profile_image_path:
                cur.execute(
                    """
                    INSERT INTO file_table (user_id, file_path, file_category)
                    VALUES (%s, %s, 1);
                    """,
                    (user_id, profile_image_path),
                )
                file_id = cur.lastrowid
                profile_image_id = file_id
                cur.execute(
                    """
                    UPDATE user_table
                    SET file_id = %s
                    WHERE user_id = %s;
                    """,
                    (profile_image_id, user_id),
                )
                conn.commit()
        conn.commit()
        return {"userId": user_id, "profileImageId": profile_image_id}

    except Exception as e:  # 드라이버별 Error 타입 모호하면 Exception으로 포괄
        if conn:
            conn.rollback()
        # 운영 시 로거로 전환 권장
        print("[signup_user] DB error:", repr(e))
        return None
    finally:
        if conn:
            conn.close()


async def get_user_by_email(email: str) -> Optional[Dict]:
    """
    email로 user_table 조회 (deleted_at IS NULL).
    반환: Dict(유저 행) or None
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, email, password, nickname, file_id,
                        session_id,
                       created_at, updated_at, deleted_at
                FROM user_table
                WHERE email = %s AND deleted_at IS NULL
                """,
                (email,),
            )
            row = cur.fetchone()
        conn.commit()
        return row
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in get_user_by_email:", e)
        return None
    finally:
        if conn: conn.close()

async def get_profile_image_path(file_id: int) -> Optional[str]:
    """
    file_table에서 카테고리=1, 삭제 안된 프로필 이미지 경로 조회
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT file_path
                FROM file_table
                WHERE file_id = %s
                  AND deleted_at IS NULL
                  AND file_category = 1
                """,
                (file_id,),
            )
            row = cur.fetchone()
        conn.commit()
        return row["file_path"] if row else None
    except Error as e:
        print("MySQL error in get_profile_image_path:", e)
        return None
    finally:
        if conn: conn.close()

async def update_session_id(user_id: int, session_id: str) -> bool:
    """
    user_table.session_id 갱신
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE user_table SET session_id = %s WHERE user_id = %s",
                (session_id, user_id),
            )
        conn.commit()
        return True
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in update_session_id:", e)
        return False
    finally:
        if conn: conn.close()

async def destroy_user_session(user_id: int) -> bool:
    """
    user_table.session_id 삭제
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE user_table SET session_id = NULL WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in destroy_user_session:", e)
        return False
    finally:
        if conn: conn.close()

async def check_email(email: str) -> bool:
    """
    user_table에서 email 중복 검사
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM user_table WHERE email = %s", (email,))
            row = cur.fetchone()
            if row:
                return True
            else:
                return False
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in check_email:", e)
        return False
    finally:
        if conn: conn.close()

async def check_nickname(nickname: str) -> bool:
    """
    user_table에서 nickname 중복 검사
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT nickname FROM user_table WHERE nickname = %s", (nickname,))
            row = cur.fetchone()
            if row:
                return True
            else:
                return False
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in check_nickname:", e)
        return False
    finally:
        if conn: conn.close()

async def get_user(user_id: int) -> tuple[dict[str, Any], ...] | None:
    """
    user_table에서 user_id로 조회
    """
    conn = get_connection()
    try:
       with conn.cursor(DictCursor) as cur:
            cur.execute(
                """
                SELECT user_table.*, COALESCE(file_table.file_path, NULL) AS file_path
                FROM user_table
                LEFT JOIN file_table ON user_table.file_id = file_table.file_id
                WHERE user_table.user_id = %s AND user_table.deleted_at IS NULL;
                """,
                (user_id,)
            )
            row = cur.fetchall()
            return row
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in get_user:", e)
        return None
    finally:
        if conn: conn.close()

async def update_user(payload: dict) -> Union[str, bool]:
    user_id = payload.get("userId")
    nickname = payload.get("nickname")
    profile_image_path = payload.get("profileImagePath")  

    if user_id is None:
        return STATUS_MESSAGE["INVALID_USER_ID"]  

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE user_table SET nickname = %s "
                "WHERE user_id = %s AND deleted_at IS NULL",
                (nickname, user_id),
            )

            cur.execute(
                "INSERT INTO file_table (user_id, file_path, file_category) "
                "VALUES (%s, %s, %s)", 
                (user_id, profile_image_path, 1),
            )

            file_id = getattr(cur, "lastrowid", None)
            if not file_id:
                conn.rollback()
                return STATUS_MESSAGE["UPDATE_PROFILE_IMAGE_FAILED"]

            cur.execute(
                "UPDATE user_table SET file_id = %s "
                "WHERE user_id = %s AND deleted_at IS NULL",
                (file_id, user_id),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return STATUS_MESSAGE["UPDATE_PROFILE_IMAGE_FAILED"]

            conn.commit()
            return True

    except Exception as e:
        if conn: conn.rollback()
        print("MySQL error in update_user:", e)
        return False

    finally:
        if conn: conn.close()


async def change_password(payload: dict) -> bool:
    """
    user_table에서 user_id로 조회
    """
    user_id = payload.get("userId")
    password = payload.get("password")

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE user_table SET password = %s WHERE user_id = %s", (password, user_id))
            conn.commit()
            return True
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in change_password:", e)
        return False
    finally:
        if conn: conn.close()

async def delete_user(user_id: int) -> bool:
    """
    user_table에서 user_id로 삭제
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE user_table SET deleted_at = NOW() WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in delete_user:", e)
        return False
    finally:
        if conn: conn.close()

async def get_nickname(user_id: int) -> Optional[str]:
    """
    user_table에서 user_id로 조회
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT nickname FROM user_table WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return row["nickname"] if row else None
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in get_nickname:", e)
        return None
    finally:
        if conn: conn.close()
