import pymysql

conn = pymysql.connect(host='localhost', user='root', password='Kin0919136592', database='Flask_Web', charset='utf8mb4')
cur = conn.cursor()
print('playlist_songs columns:')
cur.execute('SHOW COLUMNS FROM playlist_songs')
for r in cur.fetchall():
    print(r)
print('\nSample ordered rows (first 10 by added_at):')
cur.execute('SELECT playlist_id, song_id, added_at FROM playlist_songs ORDER BY added_at ASC LIMIT 10')
for r in cur.fetchall():
    print(r)
conn.close()
