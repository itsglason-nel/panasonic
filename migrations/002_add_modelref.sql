-- Phase 1: Create unified modelref table
CREATE TABLE IF NOT EXISTS `modelref` (
    `id`                INT AUTO_INCREMENT PRIMARY KEY,
    `modelcode`         VARCHAR(14) NOT NULL UNIQUE,
    -- Serial Reference (1 area per model)
    `area`              VARCHAR(14) NULL,
    `serialstart`       VARCHAR(6)  NULL,
    -- Program Check Reference (compared against insp3_run readings)
    `program_h`         VARCHAR(6) NULL,
    `program_f`         VARCHAR(6) NULL,
    -- Gas Charge Tolerance
    `gmstolpos`         DECIMAL(2,0) DEFAULT 0,
    `gmstolneg`         DECIMAL(2,0) DEFAULT 0,
    -- Operating Current Tolerance
    -- `op_current_base`   DECIMAL(4,2) DEFAULT 0,
    `op_current_tolpos` DECIMAL(2,0) DEFAULT 0,
    `op_current_tolneg` DECIMAL(2,0) DEFAULT 0,
    -- Input Power Tolerance
    -- `in_power_base`   DECIMAL(4,2) DEFAULT 0,
    `in_power_tolpos`   DECIMAL(2,0) DEFAULT 0,
    `in_power_tolneg`   DECIMAL(2,0) DEFAULT 0,
    -- Temperature Difference Tolerance
    -- `temp_diff_base`   DECIMAL(4,2) DEFAULT 0,
    `temp_diff_tolpos`  DECIMAL(2,0) DEFAULT 0,
    `temp_diff_tolneg`  DECIMAL(2,0) DEFAULT 0,
    `created_at`        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Phase 2: Migrate data from existing tables

-- 2a. Merge serialref -> modelref (one area per model)
INSERT IGNORE INTO modelref (modelcode, area, serialstart)
SELECT modelcode, MAX(area), MAX(serialstart) FROM serialref
GROUP BY modelcode;

-- 2b. Merge gastolref -> modelref
-- Use ON DUPLICATE KEY UPDATE or just an UPDATE for existing records, but since some models might only be in gastolref:
INSERT IGNORE INTO modelref (modelcode)
SELECT DISTINCT modelcode FROM gastolref;

UPDATE modelref m
JOIN gastolref g ON m.modelcode = g.modelcode
SET m.gmstolpos = g.gmstolpos, m.gmstolneg = g.gmstolneg;

-- 2c. Ensure all partref modelcodes have a modelref row
INSERT IGNORE INTO modelref (modelcode)
SELECT DISTINCT modelcode FROM partref;
