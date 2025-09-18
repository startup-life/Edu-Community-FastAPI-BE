import pymysql
from pymysql import MySQLError as Error
from pymysql.cursors import DictCursor
from database import index
from starlette.concurrency import run_in_threadpool
from utils.constant.httpStatusCode import STATUS_MESSAGE
from typing import Optional, Dict, Any

def get_connection():
    return pymysql.connect(
        **index.MYSQL_DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

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
            # 1) 닉네임 조회
            cur.execute(
                """
                SELECT nickname
                FROM user_table
                WHERE user_id = %s AND deleted_at IS NULL
                """,
                (user_id,),
            )
            row = cur.fetchone()
            print("createPost - row", row)
            if not row:
                return STATUS_MESSAGE["NOT_FOUND_USER"]
            nickname = row["nickname"]

            # 2) 게시글 INSERT
            cur.execute(
                """
                INSERT INTO post_table (user_id, nickname, post_title, post_content)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, nickname, post_title, post_content),
            )
            affected_rows = cur.rowcount            
            insert_id = cur.lastrowid
            print(affected_rows)
            print(attach_file_path)

            # 3) 첨부 파일 (옵션)
            if attach_file_path is not None:
                cur.execute(
                    """
                    INSERT INTO file_table (user_id, post_id, file_path, file_category)
                    VALUES (%s, %s, %s, 2)
                    """,
                    (user_id, insert_id, attach_file_path),
                )
                file_id = cur.lastrowid
                if file_id is not None:
                    cur.execute(
                        "UPDATE post_table SET file_id = %s WHERE post_id = %s",
                        (file_id, insert_id),
                    )

            cur.execute("SELECT @@warning_count AS warningStatus")
            warning_status = cur.fetchone()["warningStatus"]
            server_status = getattr(conn, "server_status", 2)  

            conn.commit()

            meta = {
                "fieldCount": 0,              
                "affectedRows": affected_rows,
                "insertId": insert_id,         
                "info": "",                    
                "serverStatus": server_status, # 드라이버가 달라서 server_status를 commit 전에 읽기 때문에 1이 나옴
                "warningStatus": warning_status,
                "changedRows": 0,              
            }
            return meta

    except Error as e:
        if conn:
            conn.rollback()
        print("MySQL error in create_post:", repr(e))
        return STATUS_MESSAGE["INTERNAL_SERVER_ERROR"]
    finally:
        if conn:
            conn.close()

async def update_post(
    postId: int,
    userId: int,
    postTitle: str,
    postContent: str,
    attachFilePath: Optional[str],
) -> Dict[str, Any] | str | None:
    conn = None
    try:
        conn = get_connection()  # FOUND_ROWS 설정 유지 가능
        with conn.cursor(DictCursor) as cur:
            # 값이 동일하면 매칭 자체가 안 되도록 NULL-safe 비교(<=>) 사용
            update_post_sql = """
                UPDATE post_table
                SET post_title = %s, post_content = %s
                WHERE post_id = %s
                  AND deleted_at IS NULL
                  AND NOT (post_title <=> %s AND post_content <=> %s)
            """
            cur.execute(
                update_post_sql,
                (postTitle, postContent, postId, postTitle, postContent),
            )

            matched = int(cur.rowcount)          # Rows matched (동일값이면 0)
            cur.execute("SELECT ROW_COUNT() AS changed")
            changed = int(cur.fetchone()["changed"])

            # 첨부 파일 처리
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

            cur.execute("SELECT @@warning_count AS warningStatus")
            warning_status = int(cur.fetchone()["warningStatus"])

        # 커밋 후 OkPacket 구성 (serverStatus=2로 고정)
        conn.commit()
        meta: Dict[str, Any] = {
            "fieldCount": 0,
            "affectedRows": matched,
            "insertId": 0,
            "info": f"Rows matched: {matched}  Changed: {changed}  Warnings: {warning_status}",
            "serverStatus": 2,
            "warningStatus": warning_status,
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

async def delete_post(postId: int) -> bool:
    result = False
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM post_table WHERE POST_ID = %s
                """,
                (postId,),
            )
            conn.commit()
            result = True
    except Error as e:
        print("MySQL error in delete_post:", e)
        result = False
    return result

async def get_post_list(offset: int, limit: int) -> list:
    result = []
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
        result = []
    return result

async def get_post(post_id: int) -> tuple[Any, ...] | None:
    post_result = None
    try:
        with get_connection() as conn, conn.cursor() as cur:
            # 게시글 정보 가져오기
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
            print(post_result)

            if not post_result:
                return None

            # 조회수 증가
            hits_sql = """
                UPDATE post_table 
                SET hits = hits + 1 
                WHERE post_id = %s AND deleted_at IS NULL;
            """
            cur.execute(hits_sql, (post_id,))
            conn.commit()

            # 유저 프로필 이미지 file_id 가져오기
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

                print(post_result)
        return post_result

    except Exception as e:
        print("MySQL error in get_post:", e)
        user_result = None
    return user_result
