import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get('DB_HOST', '127.0.0.1')
port = int(os.environ.get('DB_PORT', 3306))
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASSWORD', '')
db_name = os.environ.get('DB_NAME', 'plcdata')

def main():
    print(f"Connecting to DB {db_name} at {host}:{port} with user {user}")
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db_name)
    cursor = conn.cursor()

    try:
        # Let's insert a finished good.
        serial = 'TEST-FG-001'
        modelcode = 'CW-U921JPH'
        
        # 1. Insert into CRS (Compressor Registration System)
        cursor.execute("""
        INSERT INTO crs (
            modelcode, serial, compmod, compserial, 
            fan1mod, fan1serial, fan2mod, fan2serial, 
            part1mod, part1desc, part1serial, 
            part2mod, part2desc, part2serial, 
            part3mod, part3desc, part3serial, time
        ) VALUES (
            %s, %s, '9SS064XHA21', 'CMP-TEST-001', 
            'ACXA98-02590', 'F1-TEST-001', 'ACXA98-02600', 'F2-TEST-001', 
            'G0C702K00002', 'REACTOR', 'P1-TEST-001', 
            'ACXA43C07110', 'EXP VALVE COIL', 'P2-TEST-001', 
            'ACXB05-00010', 'EXP VALVE', 'P3-TEST-001', NOW()
        )
        """, (modelcode, serial))

        # 2. Insert into ATT (Safety Parts Monitoring System)
        cursor.execute("""
        INSERT INTO att (modelcode, serial, status, time)
        VALUES (%s, %s, 'GOOD', NOW())
        """, (modelcode, serial))

        # 3. Insert into GMS (Gas Management System)
        cursor.execute("""
        INSERT INTO gms (modelcode, serial, gascharge, status, time, lineno)
        VALUES (%s, %s, 0.41, 'GOOD', NOW(), 'L1')
        """, (modelcode, serial))

        conn.commit()
        print("Successfully seeded finished good: " + serial)
        
        serial2 = 'TEST-FG-002'
        
        cursor.execute("""
        INSERT INTO crs (
            modelcode, serial, compmod, compserial, 
            fan1mod, fan1serial, fan2mod, fan2serial, 
            part1mod, part1desc, part1serial, 
            part2mod, part2desc, part2serial, 
            part3mod, part3desc, part3serial, time
        ) VALUES (
            %s, %s, '9SS064XHA21', 'CMP-TEST-002', 
            'ACXA98-02590', 'F1-TEST-002', 'ACXA98-02600', 'F2-TEST-002', 
            'G0C702K00002', 'REACTOR', 'P1-TEST-002', 
            'ACXA43C07110', 'EXP VALVE COIL', 'P2-TEST-002', 
            'ACXB05-00010', 'EXP VALVE', 'P3-TEST-002', NOW()
        )
        """, (modelcode, serial2))

        cursor.execute("""
        INSERT INTO att (modelcode, serial, status, time)
        VALUES (%s, %s, 'GOOD', NOW())
        """, (modelcode, serial2))

        cursor.execute("""
        INSERT INTO gms (modelcode, serial, gascharge, status, time, lineno)
        VALUES (%s, %s, 0.41, 'GOOD', NOW(), 'L1')
        """, (modelcode, serial2))

        conn.commit()
        print("Successfully seeded finished good: " + serial2)

    except Exception as e:
        conn.rollback()
        print("Error: ", e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
