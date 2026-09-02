import pymysql

try:
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='db_MIndS2026', database='plcdata')
    cursor = conn.cursor()
    
    trigger_sql = """
    CREATE TRIGGER test_worksched_insert
    AFTER INSERT ON worksched
    FOR EACH ROW
    BEGIN
        DECLARE v_test INT;
        SELECT MIN(seq) INTO v_test FROM worksched;
    END;
    """
    cursor.execute("DROP TRIGGER IF EXISTS test_worksched_insert;")
    cursor.execute(trigger_sql)
    
    print("Trigger created. Testing insert...")
    cursor.execute("INSERT INTO worksched (lineno, seq, modelcode, plan, act, takttime, date) VALUES ('L1', 999, 'TEST', 10, 0, 0, '2026-08-18')")
    conn.commit()
    print("Insert successful!")
    
    cursor.execute("DELETE FROM worksched WHERE seq=999")
    cursor.execute("DROP TRIGGER test_worksched_insert;")
    conn.commit()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
