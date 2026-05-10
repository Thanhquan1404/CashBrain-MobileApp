import pymysql

connection_config = {
    'host': '127.0.0.1',
    'user': 'CashBrain',
    'password': '123456',
    'database': 'auth_service_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

try:
    connection = pymysql.connect(**connection_config)
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION();")
        result = cursor.fetchone()
        print(f"✅ Kết nối thành công! Phiên bản MySQL: {result['VERSION()']}")
finally:
    if 'connection' in locals():
        connection.close()