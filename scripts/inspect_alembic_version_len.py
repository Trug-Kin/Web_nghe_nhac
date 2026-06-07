import pymysql

conn = pymysql.connect(host='localhost', user='root', password='Kin0919136592', database='Flask_Web', charset='utf8mb4')
cur = conn.cursor()
cur.execute("SHOW COLUMNS FROM alembic_version")
print("alembic_version columns:")
for r in cur.fetchall():
    print(r)
cur.execute("SELECT * FROM alembic_version")
print("rows:", cur.fetchall())
conn.close()
