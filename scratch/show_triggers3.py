import pymysql

try:
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='db_MIndS2026', database='plcdata')
    cursor = conn.cursor()
    cursor.execute('SHOW TRIGGERS;')
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"Trigger: {r[0]} | Event: {r[1]} | Table: {r[2]} | Statement: {r[3]}")
    else:
        print("No triggers found.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
