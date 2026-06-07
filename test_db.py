import pymysql

try:
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="Kin0919136592", 
        database="Flask_Web"
    )
    print("✅ Kết nối MySQL thành công!")
    connection.close()
except Exception as e:
    print("❌ Lỗi kết nối:", e)
