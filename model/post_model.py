from pymysql import MySQLError as Error
from util.constant.httpStatusCode import STATUS_MESSAGE
from typing import Optional, Dict, Any
from pymysql.cursors import DictCursor
from database.index import get_connection

# 게시글 작성
async def create_post(
    user_id: int,
    post_title: str,
    post_content: str,
    attach_file_path: Optional[str] = None,
) -> Dict[str, Any] | str | None:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(DictCursor) as cur:
            cur.execute(
                """
                SELECT nickname FROM user_table
                WHERE user_id = %s AND deleted_at IS NULL
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return STATUS_MESSAGE["NOT_FOUND_USER"]
            nickname = row["nickname"]

            cur.execute(
                """
                INSERT INTO post_table 
                (user_id, nickname, post_title, post_content)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, nickname, post_title, post_content),
            )
            affected_rows = cur.rowcount
            insert_id = cur.lastrowid

            if attach_file_path is not None:
                cur.execute(
                    """
                    INSERT INTO file_table 
                    (user_id, post_id, file_path, file_category)
                    VALUES (%s, %s, %s, 2)
                    """,
                    (user_id, insert_id, attach_file_path),
                )
                file_id = cur.lastrowid
                if file_id is not None:
                    cur.execute(
                        """
                        UPDATE post_table
                        SET file_id = %s
                        WHERE post_id = %s;
                        """,
                        (file_id, insert_id),
                    )

            conn.commit()

            """
            MySQL2 드라이버 문제로 직접 메타 정보 생성
            """
            meta = {
                "fieldCount": 0,
                "affectedRows": affected_rows,
                "insertId": insert_id,
                "info": "",
                "changedRows": 0,
            }
            return meta

    except Error as e:
        print("MySQL error in create_post:", repr(e))
        return STATUS_MESSAGE["INTERNAL_SERVER_ERROR"]
    finally:
        if conn:
            conn.close()

# 게시글 업데이트
async def update_post(
    postId: int,
    userId: int,
    postTitle: str,
    postContent: str,
    attachFilePath: Optional[str],
) -> Dict[str, Any] | str | None:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(DictCursor) as cur:
            update_post_sql = """
                UPDATE post_table
                SET post_title = %s, post_content = %s
                WHERE post_id = %s AND deleted_at IS NULL
            """
            cur.execute(
                update_post_sql,
                (postTitle, postContent, postId),
            )

            matched = int(cur.rowcount)
            cur.execute("SELECT ROW_COUNT() AS changed")
            changed = int(cur.fetchone()["changed"])

            if attachFilePath is None:
                cur.execute("UPDATE post_table SET file_id = NULL WHERE post_id = %s", (postId,))
            elif attachFilePath:
                cur.execute("SELECT file_id FROM file_table WHERE file_path = %s", (attachFilePath,))
                row = cur.fetchone()
                if not row:
                    cur.execute(
                        """
                        INSERT INTO file_table (user_id, post_id, file_path, file_category)
                        VALUES (%s, %s, %s, 2)
                        """,
                        (userId, postId, attachFilePath),
                    )
                    file_id = int(cur.lastrowid)
                    cur.execute("UPDATE post_table SET file_id = %s WHERE post_id = %s", (file_id, postId))

        conn.commit()

        """
        MySQL2 드라이버 문제로 직접 메타 정보 생성
        fieldCount는 항상 0으로 반환
        insertId는 업데이트 시 항상 0으로 반환
        affectedRows는 매치된 행 수로 반환
        changedRows는 실제 변경된 행 수로 반환
        post_id는 업데이트된 게시글 ID로 반환
        """
        meta: Dict[str, Any] = {
            "fieldCount": 0,
            "affectedRows": matched,
            "insertId": 0,
            "serverStatus": 2,
            "changedRows": changed,
            "post_id": str(postId),
        }
        return meta

    except Error as e:
        if conn:
            conn.rollback()
        print("MySQL error in update_post:", e)
        return STATUS_MESSAGE["INTERNAL_SERVER_ERROR"]
    finally:
        if conn:
            conn.close()

# 게시글 삭제
async def delete_post(postId: int) -> bool:
    result = False
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE post_table
                SET deleted_at = NOW()
                WHERE post_id = %s AND deleted_at IS NULL;
                """,
                (postId,),
            )
            conn.commit()
            result = True
    except Error as e:
        print("MySQL error in delete_post:", e)
        result = False
    return result

# 게시글 목록 조회
async def get_post_list(offset: int, limit: int) -> list:
    result = None
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.post_id,
                    p.post_title,
                    p.post_content,
                    p.file_id,
                    p.user_id,
                    p.nickname,
                    p.created_at,
                    p.updated_at,
                    p.deleted_at,
                    CASE
                        WHEN p.`like` >= 1000000 THEN CONCAT(ROUND(p.`like` / 1000000, 1), 'M')
                        WHEN p.`like` >= 1000    THEN CONCAT(ROUND(p.`like` / 1000, 1), 'K')
                        ELSE p.`like`
                    END AS likeCount,
                    CASE
                        WHEN p.comment_count >= 1000000 THEN CONCAT(ROUND(p.comment_count / 1000000, 1), 'M')
                        WHEN p.comment_count >= 1000    THEN CONCAT(ROUND(p.comment_count / 1000, 1), 'K')
                        ELSE p.comment_count
                    END AS commentCount,
                    CASE
                        WHEN p.hits >= 1000000 THEN CONCAT(ROUND(p.hits / 1000000, 1), 'M')
                        WHEN p.hits >= 1000    THEN CONCAT(ROUND(p.hits / 1000, 1), 'K')
                        ELSE p.hits
                    END AS hits,
                    COALESCE(f.file_path, NULL) AS profileImagePath
                FROM post_table AS p
                LEFT JOIN user_table AS u ON p.user_id = u.user_id
                LEFT JOIN file_table AS f ON u.file_id = f.file_id
                WHERE p.deleted_at IS NULL
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s;
                """,
                (limit, offset),
            )
            result = cur.fetchall()
    except Exception as e:
        print("MySQL error in get_post_list:", e)
        result = None
    return result

# 특정 게시글 조회
async def get_post(post_id: int) -> tuple[Any, ...] | None:
    post_result = None
    try:
        with get_connection() as conn, conn.cursor() as cur:
            post_sql = """
            SELECT 
                post_table.post_id,
                post_table.post_title,
                post_table.post_content,
                post_table.file_id,
                post_table.user_id,
                post_table.nickname,
                post_table.created_at,
                post_table.updated_at,
                post_table.deleted_at,
                CASE
                    WHEN post_table.`like` >= 1000000 THEN CONCAT(ROUND(post_table.`like` / 1000000, 1), 'M')
                    WHEN post_table.`like` >= 1000 THEN CONCAT(ROUND(post_table.`like` / 1000, 1), 'K')
                    ELSE CAST(post_table.`like` AS CHAR)
                END as `like`,
                CASE
                    WHEN post_table.comment_count >= 1000000 THEN CONCAT(ROUND(post_table.comment_count / 1000000, 1), 'M')
                    WHEN post_table.comment_count >= 1000 THEN CONCAT(ROUND(post_table.comment_count / 1000, 1), 'K')
                    ELSE CAST(post_table.comment_count AS CHAR)
                END as comment_count,
                CASE
                    WHEN post_table.hits >= 1000000 THEN CONCAT(ROUND(post_table.hits / 1000000, 1), 'M')
                    WHEN post_table.hits >= 1000 THEN CONCAT(ROUND(post_table.hits / 1000, 1), 'K')
                    ELSE CAST(post_table.hits AS CHAR)
                END as hits,
                COALESCE(file_table.file_path, NULL) AS filePath
            FROM post_table
            LEFT JOIN file_table ON post_table.file_id = file_table.file_id
            WHERE post_table.post_id = %s AND post_table.deleted_at IS NULL;
            """
            cur.execute(post_sql, (post_id,))
            post_result = cur.fetchone()

            if not post_result:
                return None

            hits_sql = """
                UPDATE post_table 
                SET hits = hits + 1 
                WHERE post_id = %s AND deleted_at IS NULL;
            """
            cur.execute(hits_sql, (post_id,))
            conn.commit()

            user_sql = """
                SELECT file_id 
                FROM user_table 
                WHERE user_id = %s;
            """
            cur.execute(user_sql, (post_result["user_id"],))
            user_result = cur.fetchone()

            if user_result and len(user_result) > 0:
                profile_image_sql = """
                SELECT file_path FROM file_table 
                WHERE file_id = %s AND file_category = 1 AND user_id = %s;
                """
                cur.execute(profile_image_sql, (user_result["file_id"], post_result["user_id"]))
                profile_image_result = cur.fetchone()

                if profile_image_result:
                    post_result["profileImage"] = profile_image_result["file_path"]

        return post_result

    except Exception as e:
        print("MySQL error in get_post:", e)
        user_result = None
    return user_result