-- Migration 005: Add spamso_outmodel_refs table and alter gas tolerance precision to DECIMAL(4,2)
-- Date: 2026-09-02
-- Description:
--   1. Adds spamso_outmodel_refs table to store per-model SPAMSO output model reference
--   2. Ensures outmodel column exists in linestat after outvar
--   3. Changes gmstolpos and gmstolneg from DECIMAL(2,0) to DECIMAL(4,2) in modelref, linestat, and gastolref
--   These changes allow storing gas tolerances like 5.25 instead of only integer values.

-- 1. Alter Gas Tolerance Columns to support decimal values
ALTER TABLE modelref MODIFY COLUMN gmstolpos DECIMAL(4,2) DEFAULT 0;
ALTER TABLE modelref MODIFY COLUMN gmstolneg DECIMAL(4,2) DEFAULT 0;

ALTER TABLE linestat MODIFY COLUMN gmstolpos DECIMAL(4,2) DEFAULT 0;
ALTER TABLE linestat MODIFY COLUMN gmstolneg DECIMAL(4,2) DEFAULT 0;

ALTER TABLE gastolref MODIFY COLUMN gmstolpos DECIMAL(4,2) DEFAULT 0;
ALTER TABLE gastolref MODIFY COLUMN gmstolneg DECIMAL(4,2) DEFAULT 0;

-- 2. Add outmodel column to linestat (if not already present) after outvar
-- Uses a safe conditional pattern via information_schema
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'linestat' AND COLUMN_NAME = 'outmodel');
SET @sqlstmt := IF(@exist > 0, 'SELECT ''Column outmodel already exists in linestat''',
                               'ALTER TABLE linestat ADD COLUMN outmodel VARCHAR(14) NULL AFTER outvar');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. Create spamso_outmodel_refs lookup table
CREATE TABLE IF NOT EXISTS `spamso_outmodel_refs` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `outmodel`    VARCHAR(14) NOT NULL,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_spamso_outmodel_ref_modelcode` (`modelcode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
