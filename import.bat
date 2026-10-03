@echo off
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pdb_MIndS2026 plcdata < migrations\001_initial_schema.sql
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pdb_MIndS2026 plcdata < migrations\002_sp_linestat_shift.sql
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pdb_MIndS2026 plcdata < migrations\003_station_triggers.sql
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pdb_MIndS2026 plcdata < migrations\005_fix_pit_trigger.sql
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pdb_MIndS2026 plcdata < migrations\000_add_to_server.sql
echo Done
