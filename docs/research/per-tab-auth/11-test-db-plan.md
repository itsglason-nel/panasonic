Base commit: 0d7b700

# A11 TEST DATABASE PLAN

[PENDING OWNER RESULT]
Please run the SQL queries in `queries-for-owner.sql` to provide schema sizes and table engines.

## Dump Commands for Owner
```bash
mysqldump -u root -p plcdata > plcdata_backup.sql
mysql -u root -p -e "CREATE DATABASE plcdata_test;"
mysql -u root -p plcdata_test < plcdata_backup.sql
```
Update `.env` to point `SQLALCHEMY_DATABASE_URI` to `plcdata_test`. Disable observers by commenting out thread starts in `app/__init__.py`.
