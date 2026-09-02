import sqlite3
conn = sqlite3.connect('instance/app.db')
c = conn.cursor()
c.execute("SELECT modelcode, serial FROM crs WHERE serial IS NOT NULL AND serial != '' LIMIT 1")
res1 = c.fetchone()
if res1:
    print(f"CRS Serial: {res1[1]}, Model: {res1[0]}")
c.execute("SELECT modelcode, serial FROM att WHERE serial IS NOT NULL AND serial != '' LIMIT 1")
res2 = c.fetchone()
if res2:
    print(f"ATT Serial: {res2[1]}, Model: {res2[0]}")
conn.close()
