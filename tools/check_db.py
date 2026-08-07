import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.environ.get('DB_HOST', '127.0.0.1'),
    port=int(os.environ.get('DB_PORT', 3306)),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', ''),
    database='plcdata'
)
c = conn.cursor()
c.execute("SELECT serial, time FROM crs WHERE serial LIKE 'TEST-FG%'")
print(c.fetchall())
conn.close()
