from database.index import get_connection
from util.constant.httpStatusCode import STATUS_MESSAGE
from typing import Dict, Any

# 댓글 조회
async def get_comments(post_id: int) -> list:
    result = []
    try:
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ct.*, ut.file_id, COALESCE(ft.file_path, NULL) AS profileImage
                FROM comment_table AS ct
                LEFT JOIN user_table AS ut ON ct.user_id = ut.user_id
                LEFT JOIN file_table AS ft ON ut.file_id = ft.file_id
                WHERE ct.post_id = %s AND ct.deleted_at IS NULL;
                """,
                post_id
            )
            result = cursor.fetchall()
    except Exception as e:
        print("MySQL error in get_comments:", e)
        result = []
    return result

# 새로운 댓글 작성
async def write_comment(post_id: int, user_id: int, comment_content: str) -> str | int | bool:
    result = False
    try:
        with get_connection() as connection, connection.cursor() as cursor:
            nickname_sql = """
                SELECT nickname FROM user_table
                WHERE user_id = %s AND deleted_at IS NULL;
                """

            cursor.execute(nickname_sql, (user_id,))
            nickname_sql_result: tuple = cursor.fetchone()
            if not nickname_sql_result:
                return STATUS_MESSAGE["NOT_FOUND_USER"]
            result_nickname: str = nickname_sql_result["nickname"]

            cursor.execute(
                """
                SELECT * FROM post_table
                WHERE post_id = %s AND deleted_at IS NULL;
                """,
                (post_id,)
            )
            post_sql: str = cursor.fetchone()
            if not post_sql:
                return STATUS_MESSAGE["NOT_FOUND_POST"]
            result_post: str = post_sql["post_id"]
            insert_comment_sql = """
                INSERT INTO comment_table
                (post_id, user_id, nickname, comment_content)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_comment_sql, (result_post, user_id, result_nickname, comment_content), )
            result = cursor.lastrowid
            if not result:
                return STATUS_MESSAGE["WRITE_POST_FAILED"]

            comment_count_sql = """
                UPDATE post_table
                SET comment_count = comment_count + 1
                WHERE post_id = %s;
            """
            cursor.execute(comment_count_sql, (result_post,))
            result = cursor.lastrowid
            connection.commit()
            return result
    except Exception as e:
        print("MySQL error in write_comment:", e)
        result = False
    return result

# 댓글 삭제
async def delete_comment(post_id: int, comment_id: int, user_id: int):
    result = False
    try:
        with get_connection() as conn, conn.cursor() as cur:
            check_post_sql = """
                SELECT * FROM post_table
                WHERE post_id = %s AND deleted_at IS NULL;
            """
            cur.execute(check_post_sql, (post_id,))
            check_post_result = cur.fetchone()

            if not check_post_result:
                return None

            ckeck_user_sql = """
            SELECT * FROM comment_table
            WHERE post_id = %s AND comment_id = %s AND user_id = %s AND deleted_at IS NULL;
            """
            cur.execute(ckeck_user_sql, (post_id, comment_id, user_id))
            check_user_result = cur.fetchone()

            if not check_user_result:
                return STATUS_MESSAGE["NO_AUTH_ERROR"]

            sql = """
            UPDATE comment_table
            SET deleted_at = now()
            WHERE post_id = %s
            AND comment_id = %s
            AND user_id = %s
            AND deleted_at IS NULL;
            """
            cur.execute(sql, (post_id, comment_id, user_id))

            result = cur.rowcount

            if not result or result == 0:
                return 'delete_error'

            comment_count_sql = """
            UPDATE post_table
            SET comment_count = comment_count - 1
            WHERE post_id = %s;
            """

            cur.execute(comment_count_sql, (post_id,))
            conn.commit()
            return result
    except Exception as e:
        print("MySQL error in delete_comment:", e)
        result = False
    return result

# 댓글 수정
async def update_comment(post_id: int, comment_id: int, user_id: int, comment_content: str) -> Dict[str, Any] | str | None:
    result = False
    try:
        with get_connection() as conn, conn.cursor() as cur:
            check_post_sql = """
                SELECT * FROM post_table
                WHERE post_id = %s AND deleted_at IS NULL;
            """
            cur.execute(check_post_sql, (post_id,))

            sql = """
            UPDATE comment_table
            SET comment_content = %s
            WHERE post_id = %s 
            AND comment_id = %s 
            AND user_id = %s
            AND deleted_at IS NULL;
            """

            cur.execute(sql, (comment_content, post_id, comment_id, user_id))
            result = cur.rowcount

            conn.commit()
            return result
    except Exception:
        print("MySQL error in update_comment:")
    return result