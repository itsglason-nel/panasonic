-- =============================================================================
-- TEST SCRIPT: Safeguard and Sequence Integrity Testing
-- Database: plcdata | Line: L1
-- =============================================================================
-- This script contains 3 ready-to-run sections:
--
--   SECTION 1: Setup Scenario 1 (Test Safeguard: Block edit when CRS moved to Model B)
--   SECTION 2: Setup Scenario 2 (Test Re-Awaken: Allow edit when no next model is running)
--   SECTION 3: Teardown / Reset to clean baseline
--
-- Choose and run the section you wish to test.
-- =============================================================================

USE `plcdata`;

-- #############################################################################
-- SECTION 1: Setup Scenario 1 — Safeguard Block (CRS moved to Model B)
-- #############################################################################
-- What this does:
--   1. Sequence 0: CW-U921JPH (Model A) is fully produced (Plan = 10, Actual = 10).
--   2. Sequence 1: CW-U923JPH-H (Model B) is scheduled (Plan = 10, Actual = 0).
--   3. LineStat is loaded with Model B at CRS (status = 'Work', crsmodelcode = 'CW-U923JPH-H', crsvar = 10).
--
-- How to test in UI:
--   1. Refresh Admin -> Work Schedule.
--   2. Click "Edit" on Sequence 0 (CW-U921JPH).
--   3. Try to increase Planned Quantity from 10 to 12.
--   4. Verify: The modal displays the inline warning:
--        "Blocked: CRS has already completed this sequence and the line moved to the next model.
--         To produce more units of this model, please Add a new Work Schedule sequence."
--   5. Click "Save Changes".
--   6. Verify: The server rejects the edit with an error toast:
--        "Cannot increase plan: CRS has already completed this sequence and the line moved to CW-U923JPH-H..."
-- #############################################################################

-- UNCOMMENT LINES BELOW TO RUN SECTION 1:
/*
DELETE FROM worksched WHERE lineno = 'L1' AND date = CURDATE();

INSERT INTO worksched (lineno, seq, modelcode, plan, act, takttime, date, finalized) VALUES
('L1', 0, 'CW-U921JPH',   10, 10, 45, CURDATE(), 0),
('L1', 1, 'CW-U923JPH-H', 10,  0, 45, CURDATE(), 0);

UPDATE linestat SET
    status       = 'Work',
    active_date  = CURDATE(),
    crsmodelcode = 'CW-U923JPH-H',
    crsvar       = 10,
    attmodelcode = NULL, attvar = 0,
    gmsmodelcode = NULL, gmsvar = 0,
    inmodelcode  = NULL, invar  = 0,
    outmodelcode = NULL, outvar = 0,
    wcimodelcode = NULL, wcivar = 0,
    ritmodelcode = NULL, ritvar = 0,
    fitmodelcode = NULL, fitvar = 0,
    pitmodelcode = 'CW-U921JPH', pitvar = 0,
    updtime      = CURRENT_TIMESTAMP
WHERE lineno = 'L1';

SELECT 'SCENARIO 1 READY: Sequence 0 (CW-U921JPH) done, CRS occupied by Sequence 1 (CW-U923JPH-H).' AS status_message;
*/


-- #############################################################################
-- SECTION 2: Setup Scenario 2 — Re-Awaken / Edit Allowed (No Next Model)
-- #############################################################################
-- What this does:
--   1. Sequence 0: CW-U921JPH (Model A) is completed (Plan = 10, Actual = 10).
--   2. No other model is scheduled after it.
--   3. LineStat is idle (status = 'No Work', crsmodelcode = NULL, crsvar = 0).
--
-- How to test in UI:
--   1. Refresh Admin -> Work Schedule.
--   2. Click "Edit" on Sequence 0 (CW-U921JPH).
--   3. Increase Planned Quantity from 10 to 12.
--   4. Verify: NO blocking warning is shown.
--   5. Click "Save Changes".
--   6. Verify: The edit succeeds!
--   7. Check Line Status / Scoreboard:
--        - LineStat wakes up from 'No Work' to 'Work'.
--        - crsmodelcode becomes 'CW-U921JPH' with crsvar = 2.
--        - Station operators can scan the 2 additional units without errors.
-- #############################################################################

-- UNCOMMENT LINES BELOW TO RUN SECTION 2:
/*
DELETE FROM worksched WHERE lineno = 'L1' AND date = CURDATE();

INSERT INTO worksched (lineno, seq, modelcode, plan, act, takttime, date, finalized) VALUES
('L1', 0, 'CW-U921JPH', 10, 10, 45, CURDATE(), 0);

UPDATE linestat SET
    status       = 'No Work',
    active_date  = NULL,
    crsmodelcode = NULL, crsvar = 0,
    attmodelcode = NULL, attvar = 0,
    gmsmodelcode = NULL, gmsvar = 0,
    inmodelcode  = NULL, invar  = 0,
    outmodelcode = NULL, outvar = 0,
    wcimodelcode = NULL, wcivar = 0,
    ritmodelcode = NULL, ritvar = 0,
    fitmodelcode = NULL, fitvar = 0,
    pitmodelcode = NULL, pitvar = 0,
    updtime      = CURRENT_TIMESTAMP
WHERE lineno = 'L1';

SELECT 'SCENARIO 2 READY: Sequence 0 (CW-U921JPH) done, Line is idle, No next model.' AS status_message;
*/


-- #############################################################################
-- SECTION 3: Teardown / Reset to Clean Baseline
-- #############################################################################
-- Restores Line L1 to clean initial state.
-- #############################################################################

-- UNCOMMENT LINES BELOW TO RUN SECTION 3:
/*
DELETE FROM worksched WHERE lineno = 'L1' AND date = CURDATE();

INSERT INTO worksched (lineno, seq, modelcode, plan, act, takttime, date, finalized) VALUES
('L1', 0, 'CW-U921JPH', 2, 2, 45, CURDATE(), 0);

UPDATE linestat SET
    status       = 'No Work',
    active_date  = NULL,
    crsmodelcode = NULL, crsvar = 0,
    attmodelcode = NULL, attvar = 0,
    gmsmodelcode = NULL, gmsvar = 0,
    inmodelcode  = NULL, invar  = 0,
    outmodelcode = NULL, outvar = 0,
    wcimodelcode = NULL, wcivar = 0,
    ritmodelcode = NULL, ritvar = 0,
    fitmodelcode = NULL, fitvar = 0,
    pitmodelcode = NULL, pitvar = 0,
    updtime      = CURRENT_TIMESTAMP
WHERE lineno = 'L1';

SELECT 'RESET COMPLETE: Line L1 restored to clean baseline.' AS status_message;
*/
