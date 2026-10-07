Base commit: 0d7b700

# A11 TEST DATABASE PLAN

[PENDING OWNER RESULT]
(Table engines, sizes, and largest tables will be populated once you run the queries).

## Dump Commands for Owner
```powershell
mysqldump -u root -p plcdata > "C:\test_db_dump\plcdata_backup.sql"
mysql -u root -p -e "CREATE DATABASE plcdata_test;"
mysql -u root -p plcdata_test < "C:\test_db_dump\plcdata_backup.sql"
```
Ensure the dump is stored outside the repo directory (`C:\test_db_dump\`).
Update `.env` to point `SQLALCHEMY_DATABASE_URI` to `plcdata_test`. Disable observers by commenting out the threads in `app/__init__.py`.
