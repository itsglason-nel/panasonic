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
        modelcode = 'TL2-TEST'
        line = 'L1'
        num_units = 151
        
        # Bypass PLC triggers by setting LineStat to Work for this model
        cursor.execute("""
        UPDATE linestat 
        SET status = 'Work',
            crsmodelcode = %s, attmodelcode = %s, gmsmodelcode = %s,
            wcimodelcode = %s, ritmodelcode = %s, fitmodelcode = %s, pitmodelcode = %s
        WHERE lineno = %s
        """, (modelcode, modelcode, modelcode, modelcode, modelcode, modelcode, modelcode, line))
        
        print(f"Seeding {num_units} units for {modelcode} on {line}...")

        for i in range(1, num_units + 1):
            serial = f"TEST2-U-{i:04d}"
            
            # 1. CRS
            cursor.execute("""
            INSERT INTO crs (
                modelcode, serial, compmod, compserial, 
                fan1mod, fan1serial, fan2mod, fan2serial, 
                part1mod, part1desc, part1serial, 
                part2mod, part2desc, part2serial, 
                part3mod, part3desc, part3serial, time
            ) VALUES (
                %s, %s, '9SS064XHA21', %s, 
                'ACXA98-02590', %s, 'ACXA98-02600', %s, 
                'G0C702K00002', 'REACTOR', %s, 
                'ACXA43C07110', 'EXP VALVE COIL', %s, 
                'ACXB05-00010', 'EXP VALVE', %s, NOW()
            )
            """, (modelcode, serial, f'CMP-{i:04d}', f'F1-{i:04d}', f'F2-{i:04d}', f'P1-{i:04d}', f'P2-{i:04d}', f'P3-{i:04d}'))

            # 2. ATT
            cursor.execute("""
            INSERT INTO att (modelcode, serial, overallstatus, time, lineno)
            VALUES (%s, %s, 'GOOD', NOW(), %s)
            """, (modelcode, serial, line))

            # 3. GMS
            cursor.execute("""
            INSERT INTO gms (modelcode, serial, gascharge, status, time, lineno)
            VALUES (%s, %s, 0.41, 'GOOD', NOW(), %s)
            """, (modelcode, serial, line))
            
            # 4. WCI
            cursor.execute("""
            INSERT INTO wci (modelcode, serial, status1, status2, status3, status4, overallstatus, inspector, time, lineno)
            VALUES (%s, %s, 'GOOD', 'GOOD', 'GOOD', 'GOOD', 'GOOD', 'Tester', NOW(), %s)
            """, (modelcode, serial, line))
            
            # 5. RIT
            cursor.execute("""
            INSERT INTO rit (modelcode, serial, overallstatus, inspector, time, lineno)
            VALUES (%s, %s, 'GOOD', 'Tester', NOW(), %s)
            """, (modelcode, serial, line))
            
            # 6. FIT
            cursor.execute("""
            INSERT INTO fit (modelcode, serial, overallstatus, inspector, time, lineno)
            VALUES (%s, %s, 'GOOD', 'Tester', NOW(), %s)
            """, (modelcode, serial, line))
            
            # 7. PIT
            cursor.execute("""
            INSERT INTO pit (modelcode, serial, overallstatus, inspector, time, lineno)
            VALUES (%s, %s, 'GOOD', 'Tester', NOW(), %s)
            """, (modelcode, serial, line))

            if i % 25 == 0:
                print(f"Processed {i}/{num_units} units...")

        conn.commit()
        print("Successfully seeded all units!")

    except Exception as e:
        conn.rollback()
        print("Error: ", e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
