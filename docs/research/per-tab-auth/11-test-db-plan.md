Base commit: 0d7b700

# A11 TEST DATABASE PLAN
[PENDING OWNER RESULT: Table engines, database sizes]

Exact commands for owner (Dump stored OUTSIDE repo):
mysqldump -u root -p plcdata > "C:\test_db_dump\plcdata_backup.sql"
mysql -u root -p -e "CREATE DATABASE plcdata_test;"
mysql -u root -p plcdata_test < "C:\test_db_dump\plcdata_backup.sql"
