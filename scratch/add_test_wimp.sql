USE plcdata;

-- 1. Insert a test schedule for TEST-1234
-- We use seq 99 to avoid colliding with any existing sequences today
INSERT INTO worksched (lineno, seq, modelcode, plan, act, takttime, date, finalized)
VALUES ('L1', 99, 'TEST-1234', 20, 5, 60, CURRENT_DATE(), 0)
ON DUPLICATE KEY UPDATE 
    plan = 20, act = 5;

-- 2. Force the linestat (active line memory) to be running this test schedule
UPDATE linestat
SET 
    status = 'Work',
    active_date = CURRENT_DATE(),
    crsmodelcode = 'TEST-1234',
    crsvar = 10,
    attmodelcode = 'TEST-1234',
    attvar = 12,
    gmsmodelcode = 'TEST-1234',
    gmsvar = 15,
    updtime = CURRENT_TIMESTAMP()
WHERE id = 1;

SELECT 'Test WIMP injected successfully!' AS Result;
