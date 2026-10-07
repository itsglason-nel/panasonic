-- A0.4: Accounts per role
SELECT role, COUNT(*) as account_count FROM users GROUP BY role;

-- A10: Distinct roles that exist
SELECT DISTINCT role FROM users;

-- A11: Table engines, database size, and largest tables
SELECT table_name, engine, ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb, table_rows FROM information_schema.tables WHERE table_schema = 'plcdata' ORDER BY (data_length + index_length) DESC;
