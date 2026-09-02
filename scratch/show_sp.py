import pymysql

try:
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='db_MIndS2026', database='plcdata')
    cursor = conn.cursor()
    cursor.execute("SHOW CREATE PROCEDURE sp_linestat_shift_sequence;")
    row = cursor.fetchone()
    if row:
        print(row[2])
    else:
        print("Procedure not found.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
