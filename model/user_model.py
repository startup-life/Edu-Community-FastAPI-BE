from typing import Optional, Dict, Any, Union
import pymysql
from pymysql import MySQLError as Error
from util.constant.httpStatusCode import STATUS_MESSAGE
from pymysql.cursors import DictCursor
from database.index import get_connection
import bcrypt

SALT_ROUNDS = 10


async def login_user(email: str, password: str, session_id: str) -> Optional[Dict]:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            user_sql = "SELECT * FROM user_table WHERE email = %s AND deleted_at IS NULL;"
            cur.execute(user_sql, (email,))
            user_row = cur.fetchone()


            # 사용자가 없으면 None 반환
            if not user_row:
                return None

            is_match = bcrypt.checkpw(
                password.encode('utf-8'),
                user_row.get("password").encode('utf-8')
            )

            if not is_match:
                return None

            # 3. 프로필 이미지 경로 조회
            profile_image_path = None
            if user_row.get('file_id'):
                profile_sql = "SELECT file_path FROM file_table WHERE file_id = %s AND deleted_at IS NULL AND file_category = 1;"
                cur.execute(profile_sql, (user_row['file_id'],))
                profile_row = cur.fetchone()
                if profile_row:
                    profile_image_path = profile_row['file_path']

            session_sql = "UPDATE user_table SET session_id = %s WHERE user_id = %s;"
            cur.execute(session_sql, (session_id, user_row.get('user_id')))

            # 5. 모든 DB 작업이 성공했으므로 변경사항을 확정(commit)
            conn.commit()

            user = {
                "userId": user_row.get('user_id'),
                "email": user_row.get('email'),
                "nickname": user_row.get('nickname'),
                "profileImagePath": profile_image_path,
                "sessionId": session_id,
                "created_at": user_row.get('created_at'),
                "updated_at": user_row.get('updated_at'),
                "deleted_at": user_row.get('deleted_at'),
            }
            return user

    except pymysql.Error as e:
        return None
    finally:
        if conn:
            conn.close()


async def signup_user(
        email: str,
        password: str,
        nickname: str,
        profile_image_path: Optional[str] = None,
) -> Union[str, Dict[str, Optional[int]], None]:
    conn = None
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(SALT_ROUNDS))

        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM user_table WHERE email = %s LIMIT 1;", (email,))
            if cur.fetchone():
                conn.rollback()
                return "already_exist_email"

            cur.execute(
                """
                INSERT INTO user_table (email, password, nickname)
                VALUES (%s, %s, %s);
                """,
                (email, hashed_password, nickname),
            )
            user_id = cur.lastrowid

            profile_image_id: Optional[int] = None

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

    except Exception as e:
        if conn:
            conn.rollback()
        print("[signup_user] DB error:", repr(e))
        return None
    finally:
        if conn:
            conn.close()


async def get_user_by_email(email: str) -> Optional[Dict]:
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
    user_id = payload.get("userId")
    password = payload.get("password")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(SALT_ROUNDS))

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE user_table SET password = %s WHERE user_id = %s", (hashed_password, user_id))
            conn.commit()
            return True
    except Error as e:
        if conn: conn.rollback()
        print("MySQL error in change_password:", e)
        return False
    finally:
        if conn: conn.close()


async def delete_user(user_id: int) -> bool:
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
