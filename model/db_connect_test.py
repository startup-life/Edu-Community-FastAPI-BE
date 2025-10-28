import pymysql

from database.index import get_connection

"""
실행시 데이터베이스 연결 테스트
"""
def connect_test():
    connection = None
    try:
        connection = get_connection()
        print("✅ 데이터베이스 연결 성공!")
        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW()")
            result = cursor.fetchone()
            print("쿼리 결과:", result)

    except pymysql.Error as e:
        print(f"❌ 데이터베이스 연결 또는 쿼리 오류: {e}")
    finally:
        if connection:
            connection.close()
            print("🔌 데이터베이스 연결 종료.")