-- ALTER TABLE linestat ADD COLUMN gascharge DECIMAL(4,2) NOT NULL DEFAULT 0.00 AFTER gmsvar;

-- ALTER TABLE linestat
--     ADD COLUMN wcmodelcode VARCHAR(14), ADD COLUMN wcvar INTEGER,
--     
--     ADD COLUMN rimodelcode VARCHAR(14), ADD COLUMN rivar INTEGER,
--     ADD COLUMN ri_progh VARCHAR(6), ADD COLUMN ri_progf VARCHAR(6),
--     ADD COLUMN ri_opcur DECIMAL(8,2), ADD COLUMN ri_opcur_pos DECIMAL(2,0), ADD COLUMN ri_opcur_neg DECIMAL(2,0),
--     ADD COLUMN ri_oppow DECIMAL(8,2), ADD COLUMN ri_oppow_pos DECIMAL(2,0), ADD COLUMN ri_oppow_neg DECIMAL(2,0),
--     ADD COLUMN ri_tempdiff DECIMAL(8,2), ADD COLUMN ri_tempdiff_pos DECIMAL(2,0), ADD COLUMN ri_tempdiff_neg DECIMAL(2,0),
--     
--     ADD COLUMN fimodelcode VARCHAR(14), ADD COLUMN fivar INTEGER,
--     ADD COLUMN fi_opcur DECIMAL(5,2), ADD COLUMN fi_oppow DECIMAL(5,2),
--     
--     ADD COLUMN packmodelcode VARCHAR(14), ADD COLUMN packvar INTEGER;


-- Drop users table 
INSERT IGNORE INTO `users` (`id`, `username`, `password_hash`, `full_name`, `role`, `must_change_password`) VALUES
    (2, 'dev_glaee', 'scrypt:32768:8:1$BGIEyY4lKmHpdNCF$8afb6db376d8f1197525e44cc281f4bbe3b77fa39625f6bc61b61c1dabcec5a8642ee5bb2917401c28504e39c7e34c2bdc32c2b3873cb5021672eb0d70a92dc0', 'System Administrator', 'admin', 1);

-- ---------------------------------------------------------
-- Table 1: SAFETY PARTS MONITORING SYSTEM INDOOR (SPAMSI)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS SPAMSI (
     id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
     modelcode VARCHAR(14),
     `serial` VARCHAR(14),
     inserial VARCHAR(14),
     
     part1mod VARCHAR(14),
     part1desc VARCHAR(30),
     part1serial VARCHAR(34),
     
     part2mod VARCHAR(14),
     part2desc VARCHAR(30),
     part2serial VARCHAR(34),
     
     part3mod VARCHAR(14),
     part3desc VARCHAR(30),
     part3serial VARCHAR(34),
     
     part4mod VARCHAR(14),
     part4desc VARCHAR(30),
     part4serial VARCHAR(34),
     
     part5mod VARCHAR(14),
     part5desc VARCHAR(30),
     part5serial VARCHAR(34),
     
     part6mod VARCHAR(14),
     part6desc VARCHAR(30),
     part6serial VARCHAR(34),
     
     `time` TIMESTAMP, 
     inspector VARCHAR(20),
     lineno VARCHAR(4),
     INDEX idx_spamsi_serial (serial)
);

-- ---------------------------------------------------------
-- Table 2: SAFETY PARTS MONITORING SYSTEM OUTDOOR (SPAMSO)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS SPAMSO (
    id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    modelcode VARCHAR(14),
    `serial` VARCHAR(14),
    outmodel VARCHAR(14),
    outserial VARCHAR(44),
    
    part1mod VARCHAR(14),
    part1desc VARCHAR(30),
    part1serial VARCHAR(34),
    
    part2mod VARCHAR(14),
    part2desc VARCHAR(30),
    part2serial VARCHAR(34),
    
    part3mod VARCHAR(14),
    part3desc VARCHAR(30),
    part3serial VARCHAR(34),
    
    `time` TIMESTAMP, 
    inspector VARCHAR(20),
    lineno VARCHAR(4),
    INDEX idx_spamso_serial (serial)
);

-- ================================================================
-- Add SPAMSI and SPAMSO to linestat
-- ================================================================

-- 1. Add 23 new columns to linestat
ALTER TABLE linestat
    ADD COLUMN inmodelcode VARCHAR(14),
    ADD COLUMN invar INTEGER,
    ADD COLUMN inunique VARCHAR(4),
    ADD COLUMN inpart1mod VARCHAR(14), ADD COLUMN inpart1desc VARCHAR(30),
    ADD COLUMN inpart2mod VARCHAR(14), ADD COLUMN inpart2desc VARCHAR(30),
    ADD COLUMN inpart3mod VARCHAR(14), ADD COLUMN inpart3desc VARCHAR(30),
    ADD COLUMN inpart4mod VARCHAR(14), ADD COLUMN inpart4desc VARCHAR(30),
    ADD COLUMN inpart5mod VARCHAR(14), ADD COLUMN inpart5desc VARCHAR(30),
    ADD COLUMN inpart6mod VARCHAR(14), ADD COLUMN inpart6desc VARCHAR(30),
    
    ADD COLUMN outmodelcode VARCHAR(14),
    ADD COLUMN outvar INTEGER,
    ADD COLUMN outpart1mod VARCHAR(14), ADD COLUMN outpart1desc VARCHAR(30),
    ADD COLUMN outpart2mod VARCHAR(14), ADD COLUMN outpart2desc VARCHAR(30),
    ADD COLUMN outpart3mod VARCHAR(14), ADD COLUMN outpart3desc VARCHAR(30);

-- 2. Add indexes to SPAMSI and SPAMSO
CREATE INDEX idx_spamsi_serial ON spamsi(`serial`);
CREATE INDEX idx_spamso_serial ON spamso(`serial`);

-- ================================================================
-- Refactor PartRef for SPAMSI and SPAMSO
-- ================================================================

-- 1. Update existing SPAMS to SPAMSI in PartRef
UPDATE `partref` SET `module` = 'SPAMSI' WHERE `module` = 'SPAMS';

-- 2. Update Modules Table
DELETE FROM `modules` WHERE `name` = 'SPAMS';
INSERT IGNORE INTO `modules` (`name`, `description`) VALUES
    ('SPAMSI', 'Safety Part And Measurement System (Indoor)'),
    ('SPAMSO', 'Safety Part And Measurement System (Outdoor)');

-- 3. Recreate partref_sort view
CREATE OR REPLACE VIEW `partref_sort` AS
SELECT
    `id`,
    `modelcode`,
    `module`,
    `partno`,
    `partdesc`,
    `usage`,
    `tag`
FROM `partref`
ORDER BY
    CASE
        WHEN UPPER(`module`) = 'CRS'    THEN 1
        WHEN UPPER(`module`) = 'GMS'    THEN 2
        WHEN UPPER(`module`) = 'SPAMSI' THEN 3
        WHEN UPPER(`module`) = 'SPAMSO' THEN 4
        WHEN UPPER(`module`) = 'CB'     THEN 5
        ELSE 6
    END ASC,
    `id` ASC;





-- Phase 1: Create unified modelref table


DELIMITER $$

DROP PROCEDURE IF EXISTS sp_linestat_shift_sequence$$
CREATE PROCEDURE sp_linestat_shift_sequence(IN p_station VARCHAR(10), IN p_lineno VARCHAR(4), IN p_current_model VARCHAR(14))
BEGIN
    DECLARE v_gascharge DECIMAL(4,2);
    DECLARE v_gmstolpos DECIMAL(2,0) DEFAULT 0;
    DECLARE v_gmstolneg DECIMAL(2,0) DEFAULT 0;
    DECLARE v_active_date DATE;
    DECLARE v_current_seq INT;
    DECLARE v_next_seq INT;
    DECLARE v_next_model VARCHAR(14);
    DECLARE v_next_plan INT;
    
    -- Variables for vertical BOM pivoting (CRS)
    DECLARE v_compmod VARCHAR(14);
    DECLARE v_fan1mod VARCHAR(14);
    DECLARE v_fan2mod VARCHAR(14);
    DECLARE v_crspart1mod VARCHAR(14); DECLARE v_crspart1desc VARCHAR(30);
    DECLARE v_crspart2mod VARCHAR(14); DECLARE v_crspart2desc VARCHAR(30);
    DECLARE v_crspart3mod VARCHAR(14); DECLARE v_crspart3desc VARCHAR(30);
    DECLARE v_crspart4mod VARCHAR(14); DECLARE v_crspart4desc VARCHAR(30);
    
    -- Variables for vertical BOM pivoting (SPAMSI)
    DECLARE v_inpart1mod VARCHAR(14); DECLARE v_inpart1desc VARCHAR(30);
    DECLARE v_inpart2mod VARCHAR(14); DECLARE v_inpart2desc VARCHAR(30);
    DECLARE v_inpart3mod VARCHAR(14); DECLARE v_inpart3desc VARCHAR(30);
    DECLARE v_inpart4mod VARCHAR(14); DECLARE v_inpart4desc VARCHAR(30);
    DECLARE v_inpart5mod VARCHAR(14); DECLARE v_inpart5desc VARCHAR(30);
    DECLARE v_inpart6mod VARCHAR(14); DECLARE v_inpart6desc VARCHAR(30);
    
    -- Variables for vertical BOM pivoting (SPAMSO)
    
    DECLARE v_area VARCHAR(14);
    DECLARE v_serialstart VARCHAR(6);
    
    -- Start Transaction for Concurrency Safety
    START TRANSACTION;
    
    -- Get active date from linestat (Solves Midnight Roll-Over Bug)
    SELECT active_date INTO v_active_date FROM linestat WHERE id = 1;
    IF v_active_date IS NULL THEN
        SET v_active_date = CURDATE();
        UPDATE linestat SET active_date = v_active_date WHERE id = 1;
    END IF;
    
    -- Find current sequence number for the completed model
    IF p_current_model IS NOT NULL THEN
        SELECT seq INTO v_current_seq FROM worksched 
        WHERE date = v_active_date AND lineno = p_lineno AND modelcode = p_current_model LIMIT 1;
    ELSE
        SET v_current_seq = -1; -- Start from beginning
    END IF;
    
    -- Find the next available sequence number for the active date
    SELECT MIN(seq) INTO v_next_seq FROM worksched 
    WHERE date = v_active_date AND lineno = p_lineno AND seq > v_current_seq;
    
    IF v_next_seq IS NOT NULL THEN
        -- Get next model details
        SELECT modelcode, plan INTO v_next_model, v_next_plan FROM worksched 
        WHERE date = v_active_date AND lineno = p_lineno AND seq = v_next_seq LIMIT 1;
        
        IF p_station = 'crs' THEN
            -- Solves BOM Pivot Crash: Extract individual parts vertically using correct tags
            SELECT partno INTO v_compmod FROM partref WHERE modelcode = v_next_model AND tag = 'Compressor' LIMIT 1;
            SELECT partno INTO v_fan1mod FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno INTO v_fan2mod FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 1;
            
            -- CRS Safety Parts (up to 4)
            SELECT partno, partdesc INTO v_crspart1mod, v_crspart1desc FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_crspart2mod, v_crspart2desc FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart3mod, v_crspart3desc FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_crspart4mod, v_crspart4desc FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 3;
            
            -- Get Serial Ref
            SELECT area, serialstart INTO v_area, v_serialstart FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            
            UPDATE linestat SET 
                status = 'Work', lineno = p_lineno,
                crsmodelcode = v_next_model, crsvar = v_next_plan, 
                updtime = CURRENT_TIMESTAMP, 
                area = v_area, serialstart = v_serialstart,
                compmod = v_compmod, fan1mod = v_fan1mod, fan2mod = v_fan2mod,
                crspart1mod = v_crspart1mod, crspart1desc = v_crspart1desc,
                crspart2mod = v_crspart2mod, crspart2desc = v_crspart2desc,
                crspart3mod = v_crspart3mod, crspart3desc = v_crspart3desc,
                crspart4mod = v_crspart4mod, crspart4desc = v_crspart4desc
            WHERE id = 1;
        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = v_next_model, attvar = v_next_plan, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'gms' THEN
            SELECT `usage` INTO v_gascharge FROM partref WHERE modelcode = v_next_model AND module = 'GMS' LIMIT 1;
            IF v_gascharge IS NULL THEN SET v_gascharge = 0; END IF;
            SELECT gmstolpos, gmstolneg INTO v_gmstolpos, v_gmstolneg FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            IF v_gmstolpos IS NULL THEN SET v_gmstolpos = 0; END IF;
            IF v_gmstolneg IS NULL THEN SET v_gmstolneg = 0; END IF;
            UPDATE linestat SET gmsmodelcode = v_next_model, gmsvar = v_next_plan, gascharge = v_gascharge, gmstolpos = v_gmstolpos, gmstolneg = v_gmstolneg, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'spamsi' THEN
            -- Extract SPAMSI Parts (up to 6)
            SELECT partno, partdesc INTO v_inpart1mod, v_inpart1desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_inpart2mod, v_inpart2desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_inpart3mod, v_inpart3desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_inpart4mod, v_inpart4desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT partno, partdesc INTO v_inpart5mod, v_inpart5desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 4;
            SELECT partno, partdesc INTO v_inpart6mod, v_inpart6desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 5;
            SELECT spamsi_unique INTO v_spamsi_unique_code FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            
            UPDATE linestat SET 
                inmodelcode = v_next_model, invar = v_next_plan, inunique = v_spamsi_unique_code, updtime = CURRENT_TIMESTAMP,
                inpart1mod = v_inpart1mod, inpart1desc = v_inpart1desc,
                inpart2mod = v_inpart2mod, inpart2desc = v_inpart2desc,
                inpart3mod = v_inpart3mod, inpart3desc = v_inpart3desc,
                inpart4mod = v_inpart4mod, inpart4desc = v_inpart4desc,
                inpart5mod = v_inpart5mod, inpart5desc = v_inpart5desc,
                inpart6mod = v_inpart6mod, inpart6desc = v_inpart6desc
            WHERE id = 1;
        ELSEIF p_station = 'spamso' THEN
            -- Extract SPAMSO Parts (up to 3)
            SELECT partno, partdesc INTO v_outpart1mod, v_outpart1desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_outpart2mod, v_outpart2desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_outpart3mod, v_outpart3desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' ORDER BY id LIMIT 1 OFFSET 2;
            
            UPDATE linestat SET 
                outmodelcode = v_next_model, outvar = v_next_plan, updtime = CURRENT_TIMESTAMP,
                outpart1mod = v_outpart1mod, outpart1desc = v_outpart1desc,
                outpart2mod = v_outpart2mod, outpart2desc = v_outpart2desc,
                outpart3mod = v_outpart3mod, outpart3desc = v_outpart3desc
            WHERE id = 1;
        END IF;
    ELSE
        -- No more sequences, clear the station
        IF p_station = 'crs' THEN
            UPDATE linestat SET 
                crsmodelcode = NULL, crsvar = 0, updtime = CURRENT_TIMESTAMP,
                compmod = NULL, fan1mod = NULL, fan2mod = NULL,
                crspart1mod = NULL, crspart1desc = NULL,
                crspart2mod = NULL, crspart2desc = NULL,
                crspart3mod = NULL, crspart3desc = NULL,
                crspart4mod = NULL, crspart4desc = NULL,
                area = NULL, serialstart = NULL
            WHERE id = 1;
        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = NULL, attvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'gms' THEN
            UPDATE linestat SET gmsmodelcode = NULL, gmsvar = 0, gascharge = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'spamsi' THEN
            UPDATE linestat SET 
                inmodelcode = NULL, invar = 0, inunique = NULL, updtime = CURRENT_TIMESTAMP,
                inpart1mod = NULL, inpart1desc = NULL,
                inpart2mod = NULL, inpart2desc = NULL,
                inpart3mod = NULL, inpart3desc = NULL,
                inpart4mod = NULL, inpart4desc = NULL,
                inpart5mod = NULL, inpart5desc = NULL,
                inpart6mod = NULL, inpart6desc = NULL
            WHERE id = 1;
        ELSEIF p_station = 'spamso' THEN
            UPDATE linestat SET 
                outmodelcode = NULL, outvar = 0, updtime = CURRENT_TIMESTAMP,
                outpart1mod = NULL, outpart1desc = NULL,
                outpart2mod = NULL, outpart2desc = NULL,
                outpart3mod = NULL, outpart3desc = NULL
            WHERE id = 1;
        END IF;
        
        -- If all stations are empty, set status back to No Work
        UPDATE linestat SET status = 'No Work', active_date = NULL 
        WHERE id = 1 
          AND crsmodelcode IS NULL 
          AND attmodelcode IS NULL 
          AND gmsmodelcode IS NULL 
          AND inmodelcode IS NULL 
          AND outmodelcode IS NULL;
    END IF;
    
    COMMIT;
END$$

-- Triggers have been moved to the merged 012_triggers.sql section


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
    `op_current_base`   DECIMAL(4,2) DEFAULT 0,
    `op_current_tolpos` DECIMAL(4,2) DEFAULT 0,
    `op_current_tolneg` DECIMAL(4,2) DEFAULT 0,
    -- Input Power Tolerance
    `in_power_base`   DECIMAL(4,2) DEFAULT 0,
    `in_power_tolpos`   DECIMAL(4,2) DEFAULT 0,
    `in_power_tolneg`   DECIMAL(4,2) DEFAULT 0,
    -- Temperature Difference Tolerance
    `temp_diff_base`   DECIMAL(4,2) DEFAULT 0,
    `temp_diff_tolpos`  DECIMAL(4,2) DEFAULT 0,
    `temp_diff_tolneg`  DECIMAL(4,2) DEFAULT 0,
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

-- Dynamic Area configuration. modelref.area remains the PLC-compatible value.
CREATE TABLE IF NOT EXISTS `areas` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `name`        VARCHAR(50) NOT NULL,
    `description` VARCHAR(255) NULL,
    `is_active`   BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_areas_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `areas` (`name`) VALUES
('Domestic'), ('HongKong'), ('Export'), ('Taiwan');

INSERT IGNORE INTO `areas` (`name`)
SELECT DISTINCT TRIM(`area`) FROM `modelref`
WHERE `area` IS NOT NULL AND TRIM(`area`) <> '';

CREATE TABLE IF NOT EXISTS `spamsi_unique_refs` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `unique_code` VARCHAR(4) NOT NULL,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_spamsi_unique_ref_modelcode` (`modelcode`),
    UNIQUE KEY `uq_spamsi_unique_ref_code` (`unique_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Drop deprecated tables
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS cb_pcb;
DROP TABLE IF EXISTS insp3_vib;

-- Add packaging table
CREATE TABLE packaging(
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14), 
	serial VARCHAR(14), 
	status1 VARCHAR(12), 
	status2 VARCHAR(12), 
	status3 VARCHAR(12),
	status4 VARCHAR(12),  
	time TIMESTAMP NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4) NOT NULL, 
	PRIMARY KEY (id)
);

-- Default Shifts
INSERT IGNORE INTO shifts (name, start_time, end_time) VALUES
('Day', '06:00:00', '14:00:00'),
('Night', '22:00:00', '06:00:00');

-- drop view
drop view partref_sort;
drop view worksched_today;

-- drop table
drop table cb_pcb; 
drop table insp3_vib;
drop table repair;
drop table spams;
drop table serialref;
drop table gastolref;
drop table audit_logs;

ALTER TABLE insp3_run 
MODIFY COLUMN operating_current DECIMAL(8,2) NULL,
MODIFY COLUMN input_power DECIMAL(8,2) NULL,
MODIFY COLUMN temp_diff DECIMAL(8,2) NULL;

-- =========================================================
-- Migration 005 (2026-09-02): SPAMSO Outdoor Model + GMS Tolerance DECIMAL(4,2)
-- =========================================================

-- 1. Upgrade gas tolerance precision from DECIMAL(2,0) to DECIMAL(4,2)
ALTER TABLE modelref MODIFY COLUMN gmstolpos DECIMAL(4,2) DEFAULT 0;
ALTER TABLE modelref MODIFY COLUMN gmstolneg DECIMAL(4,2) DEFAULT 0;

ALTER TABLE linestat MODIFY COLUMN gmstolpos DECIMAL(4,2) DEFAULT 0;
ALTER TABLE linestat MODIFY COLUMN gmstolneg DECIMAL(4,2) DEFAULT 0;

-- gastolref may have been dropped in earlier step above; wrapped safely:
-- ALTER TABLE gastolref MODIFY COLUMN gmstolpos DECIMAL(4,2) DEFAULT 0;
-- ALTER TABLE gastolref MODIFY COLUMN gmstolneg DECIMAL(4,2) DEFAULT 0;

-- 2. Add outmodel column to linestat after outvar (idempotent)
SET @col_exists := (SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'linestat' AND COLUMN_NAME = 'outmodel');
SET @add_col := IF(@col_exists > 0,
                   'SELECT ''outmodel already exists''',
                   'ALTER TABLE linestat ADD COLUMN outmodel VARCHAR(14) NULL AFTER outvar');
PREPARE _stmt FROM @add_col;
EXECUTE _stmt;
DEALLOCATE PREPARE _stmt;

-- 3. Create spamso_outmodel_refs lookup table (idempotent)
CREATE TABLE IF NOT EXISTS `spamso_outmodel_refs` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `outmodel`    VARCHAR(14) NOT NULL,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_spamso_outmodel_ref_modelcode` (`modelcode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Rebuild sp_linestat_shift_sequence
--    Changes vs previous version:
--      - DECIMAL(4,2) for gmstolpos / gmstolneg local variables
--      - SPAMSO branch now fetches outmodel from spamso_outmodel_refs and writes linestat.outmodel
--      - SPAMSO clear branch now also NULLs linestat.outmodel
DROP PROCEDURE IF EXISTS sp_linestat_shift_sequence;

DELIMITER $$
CREATE PROCEDURE sp_linestat_shift_sequence(IN p_station VARCHAR(10), IN p_lineno VARCHAR(4), IN p_current_model VARCHAR(14))
sp_block: BEGIN
    DECLARE v_gascharge DECIMAL(4,2);
    DECLARE v_gmstolpos DECIMAL(4,2) DEFAULT 0;
    DECLARE v_gmstolneg DECIMAL(4,2) DEFAULT 0;
    DECLARE v_active_date DATE;
    DECLARE v_current_seq INT;
    DECLARE v_next_seq INT;
    DECLARE v_next_model VARCHAR(14);
    DECLARE v_next_plan INT;

    -- CRS BOM variables
    DECLARE v_compmod VARCHAR(14);
    DECLARE v_fan1mod VARCHAR(14);
    DECLARE v_fan2mod VARCHAR(14);
    DECLARE v_crspart1mod VARCHAR(14); DECLARE v_crspart1desc VARCHAR(30);
    DECLARE v_crspart2mod VARCHAR(14); DECLARE v_crspart2desc VARCHAR(30);
    DECLARE v_crspart3mod VARCHAR(14); DECLARE v_crspart3desc VARCHAR(30);
    DECLARE v_crspart4mod VARCHAR(14); DECLARE v_crspart4desc VARCHAR(30);
    DECLARE v_area        VARCHAR(14);
    DECLARE v_serialstart VARCHAR(6);

    -- SPAMSI BOM variables
    DECLARE v_inpart1mod VARCHAR(14); DECLARE v_inpart1desc VARCHAR(30);
    DECLARE v_inpart2mod VARCHAR(14); DECLARE v_inpart2desc VARCHAR(30);
    DECLARE v_inpart3mod VARCHAR(14); DECLARE v_inpart3desc VARCHAR(30);
    DECLARE v_inpart4mod VARCHAR(14); DECLARE v_inpart4desc VARCHAR(30);
    DECLARE v_inpart5mod VARCHAR(14); DECLARE v_inpart5desc VARCHAR(30);
    DECLARE v_inpart6mod VARCHAR(14); DECLARE v_inpart6desc VARCHAR(30);

    -- SPAMSO BOM variables
    DECLARE v_spamso_outmodel    VARCHAR(14);

    DECLARE v_spamsi_unique_code VARCHAR(4);

    START TRANSACTION;

    -- Resolve active date (midnight roll-over safe)
    SELECT active_date INTO v_active_date FROM linestat WHERE id = 1;
    IF v_active_date IS NULL THEN
        SET v_active_date = CURDATE();
        UPDATE linestat SET active_date = v_active_date WHERE id = 1;
    END IF;

    -- Resolve current sequence (NULL p_current_model = "start from beginning")
    IF p_current_model IS NULL THEN
        SET v_current_seq = -1;          -- load first seq in worksched for today
    ELSE
        SELECT seq INTO v_current_seq
        FROM worksched
        WHERE lineno = p_lineno AND date = v_active_date AND modelcode = p_current_model
        ORDER BY seq DESC LIMIT 1;

        IF v_current_seq IS NULL THEN
            COMMIT;
            LEAVE sp_block;              -- unknown model for this line/date, bail safely
        END IF;
    END IF;

    -- Next pending sequence (act < plan)
    SELECT seq, modelcode, (plan - act)
    INTO v_next_seq, v_next_model, v_next_plan
    FROM worksched
    WHERE lineno = p_lineno AND date = v_active_date
      AND seq > v_current_seq
      AND act < plan
    ORDER BY seq ASC LIMIT 1;

    IF v_next_seq IS NOT NULL THEN
        -- ── Load next model into the appropriate station ──────────────────
        IF p_station = 'crs' THEN
            -- BOM pivot: compressor, fans, safety parts, serial ref
            SELECT partno INTO v_compmod  FROM partref WHERE modelcode = v_next_model AND tag = 'Compressor' LIMIT 1;
            SELECT partno INTO v_fan1mod  FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno INTO v_fan2mod  FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart1mod, v_crspart1desc FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_crspart2mod, v_crspart2desc FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart3mod, v_crspart3desc FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_crspart4mod, v_crspart4desc FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT area, serialstart INTO v_area, v_serialstart FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                status       = 'Work',
                lineno       = p_lineno,
                active_date  = v_active_date,
                crsmodelcode = v_next_model,
                crsvar       = v_next_plan,
                area         = v_area,
                serialstart  = v_serialstart,
                compmod      = v_compmod,
                fan1mod      = v_fan1mod,
                fan2mod      = v_fan2mod,
                crspart1mod  = v_crspart1mod, crspart1desc = v_crspart1desc,
                crspart2mod  = v_crspart2mod, crspart2desc = v_crspart2desc,
                crspart3mod  = v_crspart3mod, crspart3desc = v_crspart3desc,
                crspart4mod  = v_crspart4mod, crspart4desc = v_crspart4desc,
                updtime      = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = v_next_model, attvar = v_next_plan, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'gms' THEN
            SELECT `usage` INTO v_gascharge FROM partref WHERE modelcode = v_next_model AND module = 'GMS' LIMIT 1;
            IF v_gascharge IS NULL THEN SET v_gascharge = 0; END IF;
            SELECT gmstolpos, gmstolneg INTO v_gmstolpos, v_gmstolneg FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            IF v_gmstolpos IS NULL THEN SET v_gmstolpos = 0; END IF;
            IF v_gmstolneg IS NULL THEN SET v_gmstolneg = 0; END IF;
            UPDATE linestat SET
                gmsmodelcode = v_next_model, gmsvar = v_next_plan,
                gascharge = v_gascharge, gmstolpos = v_gmstolpos, gmstolneg = v_gmstolneg,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamsi' THEN
            SELECT partno, partdesc INTO v_inpart1mod, v_inpart1desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_inpart2mod, v_inpart2desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_inpart3mod, v_inpart3desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_inpart4mod, v_inpart4desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT partno, partdesc INTO v_inpart5mod, v_inpart5desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 4;
            SELECT partno, partdesc INTO v_inpart6mod, v_inpart6desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 5;
            SELECT spamsi_unique INTO v_spamsi_unique_code FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                inmodelcode = v_next_model, invar = v_next_plan, inunique = v_spamsi_unique_code,
                inpart1mod = v_inpart1mod, inpart1desc = v_inpart1desc,
                inpart2mod = v_inpart2mod, inpart2desc = v_inpart2desc,
                inpart3mod = v_inpart3mod, inpart3desc = v_inpart3desc,
                inpart4mod = v_inpart4mod, inpart4desc = v_inpart4desc,
                inpart5mod = v_inpart5mod, inpart5desc = v_inpart5desc,
                inpart6mod = v_inpart6mod, inpart6desc = v_inpart6desc,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamso' THEN
            SELECT partno INTO v_spamso_outmodel FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' AND tag = 'Outdoor Control Board' ORDER BY id LIMIT 1;
            UPDATE linestat SET
                outmodelcode = v_next_model, outvar = v_next_plan,
                outmodel = v_spamso_outmodel,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'wc' THEN
            UPDATE linestat SET wcmodelcode = v_next_model, wcvar = v_next_plan, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'ri' THEN
            SELECT program_h, program_f,
                   op_current_base, op_current_tolpos, op_current_tolneg,
                   in_power_base,   in_power_tolpos,   in_power_tolneg,
                   temp_diff_base,  temp_diff_tolpos,  temp_diff_tolneg
            INTO @prog_h, @prog_f,
                 @opcur, @opcur_pos, @opcur_neg,
                 @oppow, @oppow_pos, @oppow_neg,
                 @tempdiff, @tempdiff_pos, @tempdiff_neg
            FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                rimodelcode = v_next_model, rivar = v_next_plan,
                ri_progh = @prog_h, ri_progf = @prog_f,
                ri_opcur = @opcur, ri_opcur_pos = @opcur_pos, ri_opcur_neg = @opcur_neg,
                ri_oppow = @oppow, ri_oppow_pos = @oppow_pos, ri_oppow_neg = @oppow_neg,
                ri_tempdiff = @tempdiff, ri_tempdiff_pos = @tempdiff_pos, ri_tempdiff_neg = @tempdiff_neg,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'fi' THEN
            UPDATE linestat SET fimodelcode = v_next_model, fivar = v_next_plan, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'pit' THEN
            UPDATE linestat SET packmodelcode = v_next_model, packvar = v_next_plan, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        END IF;

    ELSE
        -- ── No more sequences — clear the finished station ────────────────
        IF p_station = 'crs' THEN
            UPDATE linestat SET crsmodelcode = NULL, crsvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = NULL, attvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'gms' THEN
            UPDATE linestat SET
                gmsmodelcode = NULL, gmsvar = 0, gascharge = 0, gmstolpos = 0, gmstolneg = 0,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamsi' THEN
            UPDATE linestat SET
                inmodelcode = NULL, invar = 0, inunique = NULL,
                inpart1mod = NULL, inpart1desc = NULL,
                inpart2mod = NULL, inpart2desc = NULL,
                inpart3mod = NULL, inpart3desc = NULL,
                inpart4mod = NULL, inpart4desc = NULL,
                inpart5mod = NULL, inpart5desc = NULL,
                inpart6mod = NULL, inpart6desc = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamso' THEN
            UPDATE linestat SET
                outmodelcode = NULL, outvar = 0, outmodel = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'wc' THEN
            UPDATE linestat SET wcmodelcode = NULL, wcvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'ri' THEN
            UPDATE linestat SET
                rimodelcode = NULL, rivar = 0,
                ri_progh = NULL, ri_progf = NULL,
                ri_opcur = NULL, ri_opcur_pos = NULL, ri_opcur_neg = NULL,
                ri_oppow = NULL, ri_oppow_pos = NULL, ri_oppow_neg = NULL,
                ri_tempdiff = NULL, ri_tempdiff_pos = NULL, ri_tempdiff_neg = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'fi' THEN
            UPDATE linestat SET fimodelcode = NULL, fivar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'pit' THEN
            UPDATE linestat SET packmodelcode = NULL, packvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        END IF;

        -- If all stations are empty → set status back to No Work
        UPDATE linestat SET status = 'No Work', active_date = NULL
        WHERE id = 1
          AND crsmodelcode IS NULL
          AND attmodelcode IS NULL
          AND gmsmodelcode IS NULL
          AND inmodelcode  IS NULL
          AND outmodelcode IS NULL
          AND wcmodelcode  IS NULL
          AND rimodelcode  IS NULL
          AND fimodelcode  IS NULL
          AND packmodelcode IS NULL;
    END IF;

    COMMIT;
END sp_block$$
DELIMITER ;
-- 009_apply_renames.sql
-- Massive table refactoring and linestat schema update

-- 1. Rename Tables
RENAME TABLE insp2 TO wci;
RENAME TABLE insp3_run TO rit;
RENAME TABLE insp4 TO fit;
RENAME TABLE packaging TO pit;

-- 2. Alter WCI
-- Note: Adjusting from the original python model (test_wiring_seq, etc.) to status1-4. 
-- If the DB was already partially altered, some of these might need tweaking.
ALTER TABLE wci 
    CHANGE test_wiring_seq status1 VARCHAR(12),
    CHANGE test_no_touching status2 VARCHAR(12),
    CHANGE test_no_misaligned status3 VARCHAR(12),
    CHANGE test_no_lacking status4 VARCHAR(12),
    CHANGE status overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 3. Alter RIT
ALTER TABLE rit
    CHANGE `insulation_resistance/withstand_voltage` status1 VARCHAR(12),
    CHANGE `airswing` status2 VARCHAR(12),
    CHANGE `comp_operation` status3 VARCHAR(12),
    CHANGE `fan_operation` status4 VARCHAR(12),
    CHANGE `evap_tubes_cool` status5 VARCHAR(12),
    CHANGE `evap_tubes_heat` status6 VARCHAR(12),
    CHANGE `cond_tubes_cool` status7 VARCHAR(12),
    CHANGE `cond_tubes_heat` status8 VARCHAR(12),
    CHANGE `leak_status` status9 VARCHAR(12),
    CHANGE `operating_current` data1 DECIMAL(4,2),
    CHANGE `input_power` data2 DECIMAL(4,2),
    CHANGE `temp_diff` data3 DECIMAL(4,2),
    CHANGE `prog_check_h` progh VARCHAR(6),
    CHANGE `prog_check_f` progf VARCHAR(6),
    CHANGE `leak_location` status10 VARCHAR(12), -- reusing column loosely
    ADD COLUMN status11 VARCHAR(12),
    ADD COLUMN status12 VARCHAR(12),
    ADD COLUMN overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 4. Alter FIT
ALTER TABLE fit
    CHANGE `insulation_resistance/withstand_voltage` status1 VARCHAR(12),
    CHANGE `operating_current/input_power` status2 VARCHAR(12),
    CHANGE `nameplate_match` status3 VARCHAR(12),
    CHANGE `model_label` status4 VARCHAR(12),
    CHANGE `correct_manual` status5 VARCHAR(12),
    CHANGE `has_remote` status6 VARCHAR(12),
    CHANGE `has_warranty` status7 VARCHAR(12),
    CHANGE `has_screws` status8 VARCHAR(12),
    CHANGE `grille_eel` status9 VARCHAR(12),
    ADD COLUMN overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 5. Alter PIT
ALTER TABLE pit
    ADD COLUMN overallstatus VARCHAR(12);

-- 6. Alter Linestat
ALTER TABLE linestat
    -- WCI
    CHANGE wcmodelcode wcimodelcode VARCHAR(14),
    CHANGE wcvar wcivar INTEGER,
    
    -- RIT
    CHANGE rimodelcode ritmodelcode VARCHAR(14),
    CHANGE rivar ritvar INTEGER,
    CHANGE ri_progh ritprogh VARCHAR(6),
    CHANGE ri_progf ritprogf VARCHAR(6),
    CHANGE ri_opcur ritdata1 DECIMAL(4,2),
    CHANGE ri_opcur_pos ritdata1tolpos DECIMAL(4,2),
    CHANGE ri_opcur_neg ritdata1tolneg DECIMAL(4,2),
    CHANGE ri_oppow ritdata2 DECIMAL(4,2),
    CHANGE ri_oppow_pos ritdata2tolpos DECIMAL(4,2),
    CHANGE ri_oppow_neg ritdata2tolneg DECIMAL(4,2),
    CHANGE ri_tempdiff ritdata3 DECIMAL(4,2),
    CHANGE ri_tempdiff_pos ritdata3tolpos DECIMAL(4,2),
    CHANGE ri_tempdiff_neg ritdata3tolneg DECIMAL(4,2),
    ADD COLUMN ritheat1 VARCHAR(2),
    ADD COLUMN ritheat2 VARCHAR(2),
    
    -- FIT
    CHANGE fimodelcode fitmodelcode VARCHAR(14),
    CHANGE fivar fitvar INTEGER,
    CHANGE fi_opcur fitdata1 DECIMAL(4,2),
    ADD COLUMN fitdata1tolpos DECIMAL(4,2),
    ADD COLUMN fitdata1tolneg DECIMAL(4,2),
    CHANGE fi_oppow fitdata2 DECIMAL(4,2),
    ADD COLUMN fitdata2tolpos DECIMAL(4,2),
    ADD COLUMN fitdata2tolneg DECIMAL(4,2),

    -- PIT
    CHANGE packmodelcode pitmodelcode VARCHAR(14),
    CHANGE packvar pitvar INTEGER;
-- =============================================================================
-- sp_linestat_shift_sequence  (canonical source — keep in sync with
-- migrations/002_add_to_server.sql Migration 005 SP block)
--
-- Changes vs previous scratch_sp.sql:
--   • NULL p_current_model now handled as "start from first seq" (initialize_line support)
--   • CRS branch restored: status/lineno/active_date/area/serialstart/compmod/fan*/crspart* populated
--   • v_area, v_serialstart DECLARE variables added
--   • CRS clear branch now also NULLs area/serialstart/compmod/fan*/crspart*
-- =============================================================================

DROP PROCEDURE IF EXISTS sp_linestat_shift_sequence;

DELIMITER $$
CREATE PROCEDURE sp_linestat_shift_sequence(IN p_station VARCHAR(10), IN p_lineno VARCHAR(4), IN p_current_model VARCHAR(14))
sp_block: BEGIN
    DECLARE v_gascharge   DECIMAL(4,2);
    DECLARE v_gmstolpos   DECIMAL(4,2) DEFAULT 0;
    DECLARE v_gmstolneg   DECIMAL(4,2) DEFAULT 0;
    DECLARE v_active_date DATE;
    DECLARE v_current_seq INT;
    DECLARE v_next_seq    INT;
    DECLARE v_next_model  VARCHAR(14);
    DECLARE v_next_plan   INT;

    -- CRS BOM variables
    DECLARE v_compmod     VARCHAR(14);
    DECLARE v_fan1mod     VARCHAR(14);
    DECLARE v_fan2mod     VARCHAR(14);
    DECLARE v_crspart1mod VARCHAR(14); DECLARE v_crspart1desc VARCHAR(30);
    DECLARE v_crspart2mod VARCHAR(14); DECLARE v_crspart2desc VARCHAR(30);
    DECLARE v_crspart3mod VARCHAR(14); DECLARE v_crspart3desc VARCHAR(30);
    DECLARE v_crspart4mod VARCHAR(14); DECLARE v_crspart4desc VARCHAR(30);
    DECLARE v_area        VARCHAR(14);
    DECLARE v_serialstart VARCHAR(6);

    -- SPAMSI BOM variables
    DECLARE v_inpart1mod VARCHAR(14); DECLARE v_inpart1desc VARCHAR(30);
    DECLARE v_inpart2mod VARCHAR(14); DECLARE v_inpart2desc VARCHAR(30);
    DECLARE v_inpart3mod VARCHAR(14); DECLARE v_inpart3desc VARCHAR(30);
    DECLARE v_inpart4mod VARCHAR(14); DECLARE v_inpart4desc VARCHAR(30);
    DECLARE v_inpart5mod VARCHAR(14); DECLARE v_inpart5desc VARCHAR(30);
    DECLARE v_inpart6mod VARCHAR(14); DECLARE v_inpart6desc VARCHAR(30);

    -- SPAMSO BOM variables
    DECLARE v_spamso_outmodel    VARCHAR(14);

    DECLARE v_spamsi_unique_code VARCHAR(4);

    START TRANSACTION;

    -- Resolve active date (midnight roll-over safe)
    SELECT active_date INTO v_active_date FROM linestat WHERE id = 1;
    IF v_active_date IS NULL THEN
        SET v_active_date = CURDATE();
        UPDATE linestat SET active_date = v_active_date WHERE id = 1;
    END IF;

    -- Resolve current sequence.
    -- NULL p_current_model signals "initialize from the very first scheduled seq"
    -- (used by initialize_line() after a work schedule is first added to an idle line).
    IF p_current_model IS NULL THEN
        SET v_current_seq = -1;          -- seq > -1 = find the lowest seq row
    ELSE
        SELECT seq INTO v_current_seq
        FROM   worksched
        WHERE  lineno      = p_lineno
          AND  date        = v_active_date
          AND  modelcode   = p_current_model
        ORDER  BY seq DESC LIMIT 1;

        IF v_current_seq IS NULL THEN
            COMMIT;
            LEAVE sp_block;              -- unknown model for this line/date — bail safely
        END IF;
    END IF;

    -- Next pending sequence (act < plan, seq strictly after current)
    SELECT seq, modelcode, (plan - act)
    INTO   v_next_seq, v_next_model, v_next_plan
    FROM   worksched
    WHERE  lineno = p_lineno AND date = v_active_date
      AND  seq    > v_current_seq
      AND  act    < plan
    ORDER  BY seq ASC LIMIT 1;

    IF v_next_seq IS NOT NULL THEN
        -- ── Load next model into the appropriate station ─────────────────────

        IF p_station = 'crs' THEN
            -- BOM pivot: compressor, fan motors, safety parts, serial/area reference
            SELECT partno INTO v_compmod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Compressor' LIMIT 1;
            SELECT partno INTO v_fan1mod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno INTO v_fan2mod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart1mod, v_crspart1desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_crspart2mod, v_crspart2desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart3mod, v_crspart3desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_crspart4mod, v_crspart4desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT area, serialstart INTO v_area, v_serialstart
              FROM modelref WHERE modelcode = v_next_model LIMIT 1;

            UPDATE linestat SET
                status       = 'Work',
                lineno       = p_lineno,
                active_date  = v_active_date,
                crsmodelcode = v_next_model,
                crsvar       = v_next_plan,
                area         = v_area,
                serialstart  = v_serialstart,
                compmod      = v_compmod,
                fan1mod      = v_fan1mod,
                fan2mod      = v_fan2mod,
                crspart1mod  = v_crspart1mod, crspart1desc = v_crspart1desc,
                crspart2mod  = v_crspart2mod, crspart2desc = v_crspart2desc,
                crspart3mod  = v_crspart3mod, crspart3desc = v_crspart3desc,
                crspart4mod  = v_crspart4mod, crspart4desc = v_crspart4desc,
                updtime      = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = v_next_model, attvar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'gms' THEN
            SELECT `usage` INTO v_gascharge
              FROM partref WHERE modelcode = v_next_model AND module = 'GMS' LIMIT 1;
            IF v_gascharge IS NULL THEN SET v_gascharge = 0; END IF;
            SELECT gmstolpos, gmstolneg INTO v_gmstolpos, v_gmstolneg
              FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            IF v_gmstolpos IS NULL THEN SET v_gmstolpos = 0; END IF;
            IF v_gmstolneg IS NULL THEN SET v_gmstolneg = 0; END IF;
            UPDATE linestat SET
                gmsmodelcode = v_next_model, gmsvar = v_next_plan,
                gascharge = v_gascharge, gmstolpos = v_gmstolpos, gmstolneg = v_gmstolneg,
                updtime   = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamsi' THEN
            SELECT partno, partdesc INTO v_inpart1mod, v_inpart1desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_inpart2mod, v_inpart2desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_inpart3mod, v_inpart3desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_inpart4mod, v_inpart4desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT partno, partdesc INTO v_inpart5mod, v_inpart5desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 4;
            SELECT partno, partdesc INTO v_inpart6mod, v_inpart6desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 5;
            SELECT spamsi_unique INTO v_spamsi_unique_code FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                inmodelcode = v_next_model, invar = v_next_plan, inunique = v_spamsi_unique_code,
                inpart1mod = v_inpart1mod, inpart1desc = v_inpart1desc,
                inpart2mod = v_inpart2mod, inpart2desc = v_inpart2desc,
                inpart3mod = v_inpart3mod, inpart3desc = v_inpart3desc,
                inpart4mod = v_inpart4mod, inpart4desc = v_inpart4desc,
                inpart5mod = v_inpart5mod, inpart5desc = v_inpart5desc,
                inpart6mod = v_inpart6mod, inpart6desc = v_inpart6desc,
                updtime    = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamso' THEN
            SELECT partno INTO v_spamso_outmodel FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' AND tag = 'Outdoor Control Board' ORDER BY id LIMIT 1;
            UPDATE linestat SET
                outmodelcode = v_next_model, outvar = v_next_plan,
                outmodel     = v_spamso_outmodel,
                updtime     = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'wc' THEN
            UPDATE linestat SET wcimodelcode = v_next_model, wcivar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'ri' THEN
            SELECT program_h, program_f,
                   op_current_base, op_current_tolpos, op_current_tolneg,
                   in_power_base,   in_power_tolpos,   in_power_tolneg,
                   temp_diff_base,  temp_diff_tolpos,  temp_diff_tolneg,
                   IF(ritheat1='ON', 'ON', NULL), IF(ritheat2='ON', 'ON', NULL)
            INTO @prog_h, @prog_f,
                 @opcur, @opcur_pos, @opcur_neg,
                 @oppow, @oppow_pos, @oppow_neg,
                 @tempdiff, @tempdiff_pos, @tempdiff_neg,
                 @heat1, @heat2
            FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                ritmodelcode = v_next_model, ritvar = v_next_plan,
                ritprogh    = @prog_h,       ritprogf       = @prog_f,
                ritdata1    = @opcur,        ritdata1tolpos = @opcur_pos, ritdata1tolneg = @opcur_neg,
                ritdata2    = @oppow,        ritdata2tolpos = @oppow_pos, ritdata2tolneg = @oppow_neg,
                ritdata3    = @tempdiff,     ritdata3tolpos = @tempdiff_pos, ritdata3tolneg = @tempdiff_neg,
                ritheat1    = @heat1,        ritheat2       = @heat2,
                updtime     = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'fi' THEN
            SELECT op_current_base, op_current_tolpos, op_current_tolneg,
                   in_power_base,   in_power_tolpos,   in_power_tolneg
            INTO @opcur, @opcur_pos, @opcur_neg,
                 @oppow, @oppow_pos, @oppow_neg
            FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET 
                fitmodelcode = v_next_model, fitvar = v_next_plan,
                fitdata1 = @opcur, fitdata1tolpos = @opcur_pos, fitdata1tolneg = @opcur_neg,
                fitdata2 = @oppow, fitdata2tolpos = @oppow_pos, fitdata2tolneg = @oppow_neg,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'pit' THEN
            UPDATE linestat SET pitmodelcode = v_next_model, pitvar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;
        END IF;

    ELSE
        -- ── No more sequences — clear the finished station ───────────────────

        IF p_station = 'crs' THEN
            UPDATE linestat SET
                crsmodelcode = NULL, crsvar = 0,
                compmod  = NULL, fan1mod = NULL, fan2mod = NULL,
                crspart1mod = NULL, crspart1desc = NULL,
                crspart2mod = NULL, crspart2desc = NULL,
                crspart3mod = NULL, crspart3desc = NULL,
                crspart4mod = NULL, crspart4desc = NULL,
                area = NULL, serialstart = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = NULL, attvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'gms' THEN
            UPDATE linestat SET
                gmsmodelcode = NULL, gmsvar = 0, gascharge = 0, gmstolpos = 0, gmstolneg = 0,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamsi' THEN
            UPDATE linestat SET
                inmodelcode = NULL, invar = 0, inunique = NULL,
                inpart1mod = NULL, inpart1desc = NULL,
                inpart2mod = NULL, inpart2desc = NULL,
                inpart3mod = NULL, inpart3desc = NULL,
                inpart4mod = NULL, inpart4desc = NULL,
                inpart5mod = NULL, inpart5desc = NULL,
                inpart6mod = NULL, inpart6desc = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamso' THEN
            UPDATE linestat SET
                outmodelcode = NULL, outvar = 0, outmodel = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'wc' THEN
            UPDATE linestat SET wcimodelcode = NULL, wcivar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'ri' THEN
            UPDATE linestat SET
                ritmodelcode = NULL, ritvar = 0,
                ritprogh = NULL, ritprogf = NULL,
                ritdata1 = NULL, ritdata1tolpos = NULL, ritdata1tolneg = NULL,
                ritdata2 = NULL, ritdata2tolpos = NULL, ritdata2tolneg = NULL,
                ritdata3 = NULL, ritdata3tolpos = NULL, ritdata3tolneg = NULL,
                ritheat1 = NULL, ritheat2 = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'fi' THEN
            UPDATE linestat SET 
                fitmodelcode = NULL, fitvar = 0, 
                fitdata1 = NULL, fitdata1tolpos = NULL, fitdata1tolneg = NULL,
                fitdata2 = NULL, fitdata2tolpos = NULL, fitdata2tolneg = NULL,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'pit' THEN
            UPDATE linestat SET pitmodelcode = NULL, pitvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        END IF;

        -- If ALL stations are empty → revert to No Work
        UPDATE linestat SET status = 'No Work', active_date = NULL
        WHERE id = 1
          AND crsmodelcode  IS NULL
          AND attmodelcode  IS NULL
          AND gmsmodelcode  IS NULL
          AND inmodelcode   IS NULL
          AND outmodelcode  IS NULL
          AND wcimodelcode   IS NULL
          AND ritmodelcode   IS NULL
          AND fitmodelcode   IS NULL
          AND pitmodelcode IS NULL;
    END IF;

    COMMIT;
END sp_block$$
DELIMITER ;


-- ==========================================
-- MERGED FROM: 002_add_modelref.sql
-- ==========================================

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
    `op_current_tolpos` DECIMAL(4,2) DEFAULT 0,
    `op_current_tolneg` DECIMAL(4,2) DEFAULT 0,
    -- Input Power Tolerance
    -- `in_power_base`   DECIMAL(4,2) DEFAULT 0,
    `in_power_tolpos`   DECIMAL(4,2) DEFAULT 0,
    `in_power_tolneg`   DECIMAL(4,2) DEFAULT 0,
    -- Temperature Difference Tolerance
    -- `temp_diff_base`   DECIMAL(4,2) DEFAULT 0,
    `temp_diff_tolpos`  DECIMAL(4,2) DEFAULT 0,
    `temp_diff_tolneg`  DECIMAL(4,2) DEFAULT 0,
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


-- ==========================================
-- MERGED FROM: 003_add_areas.sql
-- ==========================================

-- Dynamic Area configuration. Safe to run after modelref exists.
CREATE TABLE IF NOT EXISTS `areas` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `name`        VARCHAR(50) NOT NULL,
    `description` VARCHAR(255) NULL,
    `is_active`   BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_areas_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `areas` (`name`) VALUES
    ('Domestic'), ('HongKong'), ('Export'), ('Taiwan');

INSERT IGNORE INTO `areas` (`name`)
SELECT DISTINCT TRIM(`area`)
FROM `modelref`
WHERE `area` IS NOT NULL AND TRIM(`area`) <> '';


-- ==========================================
-- MERGED FROM: 004_add_spamsi_unique_codes.sql
-- ==========================================

-- Per-model SPAMSI code reference for the existing linestat.inunique field.
CREATE TABLE IF NOT EXISTS `spamsi_unique_refs` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `unique_code` VARCHAR(4) NOT NULL,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_spamsi_unique_ref_modelcode` (`modelcode`),
    UNIQUE KEY `uq_spamsi_unique_ref_code` (`unique_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- MERGED FROM: 005_add_spamso_outmodel_refs.sql
-- ==========================================

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


-- ==========================================
-- MERGED FROM: 006_new_linestat.sql
-- ==========================================

CREATE TABLE linestat (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	updtime TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	lineno VARCHAR(4), 
	active_date DATE, -- Not on PLC
	status VARCHAR(12) DEFAULT 'No Work', 

    -- CRS
	crsmodelcode VARCHAR(14), 
	compmod VARCHAR(14), 
	fan1mod VARCHAR(14), 
	fan2mod VARCHAR(14), 
	crspart1mod VARCHAR(14), 
	crspart1desc VARCHAR(30), 
	crspart2mod VARCHAR(14), 
	crspart2desc VARCHAR(30), 
	crspart3mod VARCHAR(14), 
	crspart3desc VARCHAR(30), 
	crspart4mod VARCHAR(14), 
	crspart4desc VARCHAR(30), 
	area VARCHAR(14), 
	serialstart VARCHAR(6), 
	crsvar INTEGER, 
	reserve1 VARCHAR(20), 

    -- ATT
	attmodelcode VARCHAR(14), 
	attvar INTEGER, 

    -- GMS
	gmsmodelcode VARCHAR(14), 
	gmsvar INTEGER, 
	gascharge DECIMAL(4, 2) NOT NULL DEFAULT 0.00, 
	gmstolpos DECIMAL(2, 0) DEFAULT 0, 
	gmstolneg DECIMAL(2, 0) DEFAULT 0,

    -- SPAMSI 
	inmodelcode VARCHAR(14),
	invar INTEGER,
	inunique VARCHAR(4),
	inpart1mod VARCHAR(14), inpart1desc VARCHAR(30),
	inpart2mod VARCHAR(14), inpart2desc VARCHAR(30),
	inpart3mod VARCHAR(14), inpart3desc VARCHAR(30),
	inpart4mod VARCHAR(14), inpart4desc VARCHAR(30),
	inpart5mod VARCHAR(14), inpart5desc VARCHAR(30),
	inpart6mod VARCHAR(14), inpart6desc VARCHAR(30),

    -- SPAMSO
	outmodelcode VARCHAR(14),
	outvar INTEGER,
    outmodel VARCHAR(14), 
	outpart1mod VARCHAR(14), outpart1desc VARCHAR(30),
	outpart2mod VARCHAR(14), outpart2desc VARCHAR(30),
	outpart3mod VARCHAR(14), outpart3desc VARCHAR(30),

    -- WCI
    wcimodelcode VARCHAR(14),       -- wcmodelcode VARCHAR(14),     
    wcivar INTEGER,                 -- wcvar INTEGER,    

    -- RIT
    ritmodelcode VARCHAR(14),       -- rimodelcode VARCHAR(14),
    ritvar INTEGER,                 -- rivar INTEGER,
    ritprogh VARCHAR(6),            -- ri_progh VARCHAR(6),
    ritprogf VARCHAR(6),            -- ri_progf VARCHAR(6),
    ritdata1 DECIMAL (4,2),         -- ri_opcur DECIMAL (8,2),
    ritdata1tolpos DECIMAL (4,2),   -- ri_opcur_pos DECIMAL (2,0),
    ritdata1tolneg DECIMAL (4,2),   -- ri_opcur_neg DECIMAL (2,0),
    ritdata2 DECIMAL (4,2),         -- ri_oppow DECIMAL (8,2),
    ritdata2tolpos DECIMAL (4,2),   -- ri_oppow_pos DECIMAL (2,0),
    ritdata2tolneg DECIMAL (4,2),   -- ri_oppow_neg DECIMAL (2,0),
    ritdata3 DECIMAL (4,2),         -- ri_tempdiff DECIMAL (8,2),
    ritdata3tolpos DECIMAL (4,2),   -- ri_tempdiff_pos DECIMAL (2,0),
    ritdata3tolneg DECIMAL (4,2),   -- ri_tempdiff_neg DECIMAL (2,0),
    ritheat1 VARCHAR(2),            -- on the new model we will add a new textbox to ask if this model is "on" or null for heating of evaporator tubes
    ritheat2 VARCHAR(2),            -- on the new model we will add a new textbox to ask if this model is "on" or null for heating of condenser tubes

    -- FIT
    fitmodelcode VARCHAR(14),       -- fimodelcode VARCHAR(14),      
    fitvar INTEGER,                 -- fivar INTEGER,     
    fitdata1 DECIMAL (4,2),         -- fi_opcur DECIMAL (5,2), base of operating current (from modelref) depends on modelcode of the station
    fitdata1tolpos DECIMAL (4,2),   -- tolerance from the positive side of operating current (from modelref)
    fitdata1tolneg DECIMAL (4,2),   -- tolerance from the negative side of operating current (from modelref)
    fitdata2 DECIMAL (4,2),         -- fi_oppow DECIMAL (5,2), base of input power (from modelref) depends on modelcode of the station
    fitdata2tolpos DECIMAL (4,2),   -- tolerance from the positive side of input power (from modelref)
    fitdata2tolneg DECIMAL (4,2),   -- tolerance from the negative side of input power (from modelref)

    -- PIT
    pitmodelcode VARCHAR(14),        -- packmodelcode VARCHAR(14),
    pitvar INTEGER,                  -- packvar INTEGER,

	PRIMARY KEY (id) 
);




-- ==========================================
-- MERGED FROM: 007_new_splinestat.sql
-- ==========================================

-- =============================================================================
-- sp_linestat_shift_sequence  (canonical source — keep in sync with
-- migrations/002_add_to_server.sql Migration 005 SP block)
--
-- Changes vs previous scratch_sp.sql:
--   • NULL p_current_model now handled as "start from first seq" (initialize_line support)
--   • CRS branch restored: status/lineno/active_date/area/serialstart/compmod/fan*/crspart* populated
--   • v_area, v_serialstart DECLARE variables added
--   • CRS clear branch now also NULLs area/serialstart/compmod/fan*/crspart*
-- =============================================================================

DROP PROCEDURE IF EXISTS sp_linestat_shift_sequence;

DELIMITER $$
CREATE PROCEDURE sp_linestat_shift_sequence(IN p_station VARCHAR(10), IN p_lineno VARCHAR(4), IN p_current_model VARCHAR(14))
sp_block: BEGIN
    DECLARE v_gascharge   DECIMAL(4,2);
    DECLARE v_gmstolpos   DECIMAL(4,2) DEFAULT 0;
    DECLARE v_gmstolneg   DECIMAL(4,2) DEFAULT 0;
    DECLARE v_active_date DATE;
    DECLARE v_current_seq INT;
    DECLARE v_next_seq    INT;
    DECLARE v_next_model  VARCHAR(14);
    DECLARE v_next_plan   INT;

    -- CRS BOM variables
    DECLARE v_compmod     VARCHAR(14);
    DECLARE v_fan1mod     VARCHAR(14);
    DECLARE v_fan2mod     VARCHAR(14);
    DECLARE v_crspart1mod VARCHAR(14); DECLARE v_crspart1desc VARCHAR(30);
    DECLARE v_crspart2mod VARCHAR(14); DECLARE v_crspart2desc VARCHAR(30);
    DECLARE v_crspart3mod VARCHAR(14); DECLARE v_crspart3desc VARCHAR(30);
    DECLARE v_crspart4mod VARCHAR(14); DECLARE v_crspart4desc VARCHAR(30);
    DECLARE v_area        VARCHAR(14);
    DECLARE v_serialstart VARCHAR(6);

    -- SPAMSI BOM variables
    DECLARE v_inpart1mod VARCHAR(14); DECLARE v_inpart1desc VARCHAR(30);
    DECLARE v_inpart2mod VARCHAR(14); DECLARE v_inpart2desc VARCHAR(30);
    DECLARE v_inpart3mod VARCHAR(14); DECLARE v_inpart3desc VARCHAR(30);
    DECLARE v_inpart4mod VARCHAR(14); DECLARE v_inpart4desc VARCHAR(30);
    DECLARE v_inpart5mod VARCHAR(14); DECLARE v_inpart5desc VARCHAR(30);
    DECLARE v_inpart6mod VARCHAR(14); DECLARE v_inpart6desc VARCHAR(30);

    -- SPAMSO BOM variables
    DECLARE v_spamso_outmodel    VARCHAR(14);

    DECLARE v_spamsi_unique_code VARCHAR(4);

    START TRANSACTION;

    -- Resolve active date (midnight roll-over safe)
    SELECT active_date INTO v_active_date FROM linestat WHERE id = 1;
    IF v_active_date IS NULL THEN
        SET v_active_date = CURDATE();
        UPDATE linestat SET active_date = v_active_date WHERE id = 1;
    END IF;

    -- Resolve current sequence.
    -- NULL p_current_model signals "initialize from the very first scheduled seq"
    -- (used by initialize_line() after a work schedule is first added to an idle line).
    IF p_current_model IS NULL THEN
        SET v_current_seq = -1;          -- seq > -1 = find the lowest seq row
    ELSE
        SELECT seq INTO v_current_seq
        FROM   worksched
        WHERE  lineno      = p_lineno
          AND  date        = v_active_date
          AND  modelcode   = p_current_model
        ORDER  BY seq DESC LIMIT 1;

        IF v_current_seq IS NULL THEN
            COMMIT;
            LEAVE sp_block;              -- unknown model for this line/date — bail safely
        END IF;
    END IF;

    -- Next pending sequence (act < plan, seq strictly after current)
    SELECT seq, modelcode, (plan - act)
    INTO   v_next_seq, v_next_model, v_next_plan
    FROM   worksched
    WHERE  lineno = p_lineno AND date = v_active_date
      AND  seq    > v_current_seq
      AND  act    < plan
    ORDER  BY seq ASC LIMIT 1;

    IF v_next_seq IS NOT NULL THEN
        -- ── Load next model into the appropriate station ─────────────────────

        IF p_station = 'crs' THEN
            -- BOM pivot: compressor, fan motors, safety parts, serial/area reference
            SELECT partno INTO v_compmod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Compressor' LIMIT 1;
            SELECT partno INTO v_fan1mod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno INTO v_fan2mod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart1mod, v_crspart1desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_crspart2mod, v_crspart2desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart3mod, v_crspart3desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_crspart4mod, v_crspart4desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT area, serialstart INTO v_area, v_serialstart
              FROM modelref WHERE modelcode = v_next_model LIMIT 1;

            UPDATE linestat SET
                status       = 'Work',
                lineno       = p_lineno,
                active_date  = v_active_date,
                crsmodelcode = v_next_model,
                crsvar       = v_next_plan,
                area         = v_area,
                serialstart  = v_serialstart,
                compmod      = v_compmod,
                fan1mod      = v_fan1mod,
                fan2mod      = v_fan2mod,
                crspart1mod  = v_crspart1mod, crspart1desc = v_crspart1desc,
                crspart2mod  = v_crspart2mod, crspart2desc = v_crspart2desc,
                crspart3mod  = v_crspart3mod, crspart3desc = v_crspart3desc,
                crspart4mod  = v_crspart4mod, crspart4desc = v_crspart4desc,
                updtime      = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = v_next_model, attvar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'gms' THEN
            SELECT `usage` INTO v_gascharge
              FROM partref WHERE modelcode = v_next_model AND module = 'GMS' LIMIT 1;
            IF v_gascharge IS NULL THEN SET v_gascharge = 0; END IF;
            SELECT gmstolpos, gmstolneg INTO v_gmstolpos, v_gmstolneg
              FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            IF v_gmstolpos IS NULL THEN SET v_gmstolpos = 0; END IF;
            IF v_gmstolneg IS NULL THEN SET v_gmstolneg = 0; END IF;
            UPDATE linestat SET
                gmsmodelcode = v_next_model, gmsvar = v_next_plan,
                gascharge = v_gascharge, gmstolpos = v_gmstolpos, gmstolneg = v_gmstolneg,
                updtime   = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamsi' THEN
            SELECT partno, partdesc INTO v_inpart1mod, v_inpart1desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_inpart2mod, v_inpart2desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_inpart3mod, v_inpart3desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_inpart4mod, v_inpart4desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT partno, partdesc INTO v_inpart5mod, v_inpart5desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 4;
            SELECT partno, partdesc INTO v_inpart6mod, v_inpart6desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 5;
            SELECT spamsi_unique INTO v_spamsi_unique_code FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                inmodelcode = v_next_model, invar = v_next_plan, inunique = v_spamsi_unique_code,
                inpart1mod = v_inpart1mod, inpart1desc = v_inpart1desc,
                inpart2mod = v_inpart2mod, inpart2desc = v_inpart2desc,
                inpart3mod = v_inpart3mod, inpart3desc = v_inpart3desc,
                inpart4mod = v_inpart4mod, inpart4desc = v_inpart4desc,
                inpart5mod = v_inpart5mod, inpart5desc = v_inpart5desc,
                inpart6mod = v_inpart6mod, inpart6desc = v_inpart6desc,
                updtime    = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamso' THEN
            SELECT partno INTO v_spamso_outmodel FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' AND tag = 'Outdoor Control Board' ORDER BY id LIMIT 1;
            UPDATE linestat SET
                outmodelcode = v_next_model, outvar = v_next_plan,
                outmodel     = v_spamso_outmodel,
                updtime     = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'wc' THEN
            UPDATE linestat SET wcmodelcode = v_next_model, wcvar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'ri' THEN
            SELECT program_h, program_f,
                   op_current_base, op_current_tolpos, op_current_tolneg,
                   in_power_base,   in_power_tolpos,   in_power_tolneg,
                   temp_diff_base,  temp_diff_tolpos,  temp_diff_tolneg
            INTO @prog_h, @prog_f,
                 @opcur, @opcur_pos, @opcur_neg,
                 @oppow, @oppow_pos, @oppow_neg,
                 @tempdiff, @tempdiff_pos, @tempdiff_neg
            FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                rimodelcode = v_next_model, rivar = v_next_plan,
                ri_progh    = @prog_h,      ri_progf     = @prog_f,
                ri_opcur    = @opcur,       ri_opcur_pos = @opcur_pos, ri_opcur_neg = @opcur_neg,
                ri_oppow    = @oppow,       ri_oppow_pos = @oppow_pos, ri_oppow_neg = @oppow_neg,
                ri_tempdiff = @tempdiff,    ri_tempdiff_pos = @tempdiff_pos, ri_tempdiff_neg = @tempdiff_neg,
                updtime     = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'fi' THEN
            UPDATE linestat SET fimodelcode = v_next_model, fivar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'pit' THEN
            UPDATE linestat SET packmodelcode = v_next_model, packvar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;
        END IF;

    ELSE
        -- ── No more sequences — clear the finished station ───────────────────

        IF p_station = 'crs' THEN
            UPDATE linestat SET
                crsmodelcode = NULL, crsvar = 0,
                compmod  = NULL, fan1mod = NULL, fan2mod = NULL,
                crspart1mod = NULL, crspart1desc = NULL,
                crspart2mod = NULL, crspart2desc = NULL,
                crspart3mod = NULL, crspart3desc = NULL,
                crspart4mod = NULL, crspart4desc = NULL,
                area = NULL, serialstart = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = NULL, attvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'gms' THEN
            UPDATE linestat SET
                gmsmodelcode = NULL, gmsvar = 0, gascharge = 0, gmstolpos = 0, gmstolneg = 0,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamsi' THEN
            UPDATE linestat SET
                inmodelcode = NULL, invar = 0, inunique = NULL,
                inpart1mod = NULL, inpart1desc = NULL,
                inpart2mod = NULL, inpart2desc = NULL,
                inpart3mod = NULL, inpart3desc = NULL,
                inpart4mod = NULL, inpart4desc = NULL,
                inpart5mod = NULL, inpart5desc = NULL,
                inpart6mod = NULL, inpart6desc = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamso' THEN
            UPDATE linestat SET
                outmodelcode = NULL, outvar = 0, outmodel = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'wc' THEN
            UPDATE linestat SET wcmodelcode = NULL, wcvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'ri' THEN
            UPDATE linestat SET
                rimodelcode = NULL, rivar = 0,
                ri_progh = NULL, ri_progf = NULL,
                ri_opcur = NULL, ri_opcur_pos = NULL, ri_opcur_neg = NULL,
                ri_oppow = NULL, ri_oppow_pos = NULL, ri_oppow_neg = NULL,
                ri_tempdiff = NULL, ri_tempdiff_pos = NULL, ri_tempdiff_neg = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'fi' THEN
            UPDATE linestat SET fimodelcode = NULL, fivar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;

        ELSEIF p_station = 'pit' THEN
            UPDATE linestat SET packmodelcode = NULL, packvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        END IF;

        -- If ALL stations are empty → revert to No Work
        UPDATE linestat SET status = 'No Work', active_date = NULL
        WHERE id = 1
          AND crsmodelcode  IS NULL
          AND attmodelcode  IS NULL
          AND gmsmodelcode  IS NULL
          AND inmodelcode   IS NULL
          AND outmodelcode  IS NULL
          AND wcmodelcode   IS NULL
          AND rimodelcode   IS NULL
          AND fimodelcode   IS NULL
          AND packmodelcode IS NULL;
    END IF;

    COMMIT;
END sp_block$$
DELIMITER ;


-- ==========================================
-- MERGED FROM: 008_new_tables.sql
-- ==========================================

-- Table insp2 to wci 
CREATE TABLE wci (                      -- CREATE TABLE insp2 (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
    status1 VARCHAR(12) NOT NULL, 
    status2 VARCHAR(12) NOT NULL, 
    status3 VARCHAR(12) NOT NULL, 
    status4 VARCHAR(12) NOT NULL, 
    -- alter column overallstatus VARCHAR(12),
	time TIMESTAMP NOT NULL,            -- alter column time_in
    inspector VARCHAR(20),              -- time TIMESTAMP NOT NULL,
	lineno VARCHAR(4),
	PRIMARY KEY (id)
);

-- Table insp3_run to rit
CREATE TABLE rit (                                          -- CREATE TABLE insp3_run (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
	status1 VARCHAR(12), 
	status2 VARCHAR(12),
	status3 VARCHAR(12), 
	status4 VARCHAR(12), 
	status5 VARCHAR(12), 
	status6 VARCHAR(12),
	status7 VARCHAR(12),
	status8 VARCHAR(12),
	status9 VARCHAR(12),
    data1 DECIMAL(4,2),
	status10 VARCHAR(12),
    data2 DECIMAL(4,2),
    status11 VARCHAR(12),
    data3 DECIMAL(4,2),
    status12 VARCHAR(12),
    progh VARCHAR(6),
    progf VARCHAR(6),
    overallstatus VARCHAR(12),
    time TIMESTAMP NOT NULL,
	inspector VARCHAR(20), 
    lineno VARCHAR(4),
	PRIMARY KEY (id)
);

-- Table insp4 to fit
CREATE TABLE fit (                      -- CREATE TABLE insp4 (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL,  
	status1 VARCHAR(12), 
    status2 VARCHAR(12),
    status3 VARCHAR(12),
    status4 VARCHAR(12),
    status5 VARCHAR(12),
    status6 VARCHAR(12),
    status7 VARCHAR(12),
    status8 VARCHAR(12),
    status9 VARCHAR(12),
    overallstatus VARCHAR(12),
    time TIMESTAMP NOT NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4),
	PRIMARY KEY (id)
);

-- Table packaging to pit
CREATE TABLE pit(
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14), 
	serial VARCHAR(14), 
	status1 VARCHAR(12), 
	status2 VARCHAR(12), 
	status3 VARCHAR(12),
	status4 VARCHAR(12),
    overallstatus VARCHAR(12),  
	time TIMESTAMP NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4) NOT NULL, 
	PRIMARY KEY (id)
);



-- ==========================================
-- MERGED FROM: 009_apply_renames.sql
-- ==========================================

-- 009_apply_renames.sql
-- Massive table refactoring and linestat schema update

-- 1. Rename Tables
RENAME TABLE insp2 TO wci;
RENAME TABLE insp3_run TO rit;
RENAME TABLE insp4 TO fit;
RENAME TABLE packaging TO pit;

-- 2. Alter WCI
-- Note: Adjusting from the original python model (test_wiring_seq, etc.) to status1-4. 
-- If the DB was already partially altered, some of these might need tweaking.
ALTER TABLE wci 
    CHANGE test_wiring_seq status1 VARCHAR(12),
    CHANGE test_no_touching status2 VARCHAR(12),
    CHANGE test_no_misaligned status3 VARCHAR(12),
    CHANGE test_no_lacking status4 VARCHAR(12),
    CHANGE status overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 3. Alter RIT
ALTER TABLE rit
    CHANGE `insulation_resistance/withstand_voltage` status1 VARCHAR(12),
    CHANGE `airswing` status2 VARCHAR(12),
    CHANGE `comp_operation` status3 VARCHAR(12),
    CHANGE `fan_operation` status4 VARCHAR(12),
    CHANGE `evap_tubes_cool` status5 VARCHAR(12),
    CHANGE `evap_tubes_heat` status6 VARCHAR(12),
    CHANGE `cond_tubes_cool` status7 VARCHAR(12),
    CHANGE `cond_tubes_heat` status8 VARCHAR(12),
    CHANGE `leak_status` status9 VARCHAR(12),
    CHANGE `operating_current` data1 DECIMAL(4,2),
    CHANGE `input_power` data2 DECIMAL(4,2),
    CHANGE `temp_diff` data3 DECIMAL(4,2),
    CHANGE `prog_check_h` progh VARCHAR(6),
    CHANGE `prog_check_f` progf VARCHAR(6),
    CHANGE `leak_location` status10 VARCHAR(12), -- reusing column loosely
    ADD COLUMN status11 VARCHAR(12),
    ADD COLUMN status12 VARCHAR(12),
    ADD COLUMN overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 4. Alter FIT
ALTER TABLE fit
    CHANGE `insulation_resistance/withstand_voltage` status1 VARCHAR(12),
    CHANGE `operating_current/input_power` status2 VARCHAR(12),
    CHANGE `nameplate_match` status3 VARCHAR(12),
    CHANGE `model_label` status4 VARCHAR(12),
    CHANGE `correct_manual` status5 VARCHAR(12),
    CHANGE `has_remote` status6 VARCHAR(12),
    CHANGE `has_warranty` status7 VARCHAR(12),
    CHANGE `has_screws` status8 VARCHAR(12),
    CHANGE `grille_eel` status9 VARCHAR(12),
    ADD COLUMN overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 5. Alter PIT
ALTER TABLE pit
    ADD COLUMN overallstatus VARCHAR(12);

-- 6. Alter Linestat
ALTER TABLE linestat
    -- WCI
    CHANGE wcmodelcode wcimodelcode VARCHAR(14),
    CHANGE wcvar wcivar INTEGER,
    
    -- RIT
    CHANGE rimodelcode ritmodelcode VARCHAR(14),
    CHANGE rivar ritvar INTEGER,
    CHANGE ri_progh ritprogh VARCHAR(6),
    CHANGE ri_progf ritprogf VARCHAR(6),
    CHANGE ri_opcur ritdata1 DECIMAL(4,2),
    CHANGE ri_opcur_pos ritdata1tolpos DECIMAL(4,2),
    CHANGE ri_opcur_neg ritdata1tolneg DECIMAL(4,2),
    CHANGE ri_oppow ritdata2 DECIMAL(4,2),
    CHANGE ri_oppow_pos ritdata2tolpos DECIMAL(4,2),
    CHANGE ri_oppow_neg ritdata2tolneg DECIMAL(4,2),
    CHANGE ri_tempdiff ritdata3 DECIMAL(4,2),
    CHANGE ri_tempdiff_pos ritdata3tolpos DECIMAL(4,2),
    CHANGE ri_tempdiff_neg ritdata3tolneg DECIMAL(4,2),
    ADD COLUMN ritheat1 VARCHAR(2),
    ADD COLUMN ritheat2 VARCHAR(2),
    
    -- FIT
    CHANGE fimodelcode fitmodelcode VARCHAR(14),
    CHANGE fivar fitvar INTEGER,
    CHANGE fi_opcur fitdata1 DECIMAL(4,2),
    ADD COLUMN fitdata1tolpos DECIMAL(4,2),
    ADD COLUMN fitdata1tolneg DECIMAL(4,2),
    CHANGE fi_oppow fitdata2 DECIMAL(4,2),
    ADD COLUMN fitdata2tolpos DECIMAL(4,2),
    ADD COLUMN fitdata2tolneg DECIMAL(4,2),

    -- PIT
    CHANGE packmodelcode pitmodelcode VARCHAR(14),
    CHANGE packvar pitvar INTEGER;


-- 7. Alter ModelRef
ALTER TABLE modelref ADD COLUMN ritheat1 VARCHAR(2) NULL, ADD COLUMN ritheat2 VARCHAR(2) NULL;


-- ==========================================
-- MERGED FROM: scratch_sp.sql
-- ==========================================

-- =============================================================================
-- sp_linestat_shift_sequence  
-- =============================================================================

DROP PROCEDURE IF EXISTS sp_linestat_shift_sequence;

DELIMITER $$
CREATE PROCEDURE sp_linestat_shift_sequence(IN p_station VARCHAR(10), IN p_lineno VARCHAR(4), IN p_current_model VARCHAR(14))
sp_block: BEGIN
    DECLARE v_gascharge   DECIMAL(4,2);
    DECLARE v_gmstolpos   DECIMAL(4,2) DEFAULT 0;
    DECLARE v_gmstolneg   DECIMAL(4,2) DEFAULT 0;
    DECLARE v_active_date DATE;
    DECLARE v_linestat_id INT;
    DECLARE v_current_seq INT;
    DECLARE v_next_seq    INT;
    DECLARE v_next_model  VARCHAR(14);
    DECLARE v_next_plan   INT;

    -- CRS BOM variables
    DECLARE v_compmod     VARCHAR(14);
    DECLARE v_fan1mod     VARCHAR(14);
    DECLARE v_fan2mod     VARCHAR(14);
    DECLARE v_crspart1mod VARCHAR(14); DECLARE v_crspart1desc VARCHAR(30);
    DECLARE v_crspart2mod VARCHAR(14); DECLARE v_crspart2desc VARCHAR(30);
    DECLARE v_crspart3mod VARCHAR(14); DECLARE v_crspart3desc VARCHAR(30);
    DECLARE v_crspart4mod VARCHAR(14); DECLARE v_crspart4desc VARCHAR(30);
    DECLARE v_area        VARCHAR(14);
    DECLARE v_serialstart VARCHAR(6);

    -- SPAMSI BOM variables
    DECLARE v_inpart1mod VARCHAR(14); DECLARE v_inpart1desc VARCHAR(30);
    DECLARE v_inpart2mod VARCHAR(14); DECLARE v_inpart2desc VARCHAR(30);
    DECLARE v_inpart3mod VARCHAR(14); DECLARE v_inpart3desc VARCHAR(30);
    DECLARE v_inpart4mod VARCHAR(14); DECLARE v_inpart4desc VARCHAR(30);
    DECLARE v_inpart5mod VARCHAR(14); DECLARE v_inpart5desc VARCHAR(30);
    DECLARE v_inpart6mod VARCHAR(14); DECLARE v_inpart6desc VARCHAR(30);

    -- SPAMSO BOM variables
    DECLARE v_spamso_outmodel    VARCHAR(14);

    DECLARE v_spamsi_unique_code VARCHAR(4);

    -- Resolve active date (midnight roll-over safe)
    SELECT id, active_date INTO v_linestat_id, v_active_date FROM linestat WHERE lineno = p_lineno LIMIT 1;
    IF v_active_date IS NULL THEN
        SET v_active_date = CURDATE();
        UPDATE linestat SET active_date = v_active_date WHERE id = v_linestat_id;
    END IF;

    -- Resolve current sequence.
    -- NULL p_current_model signals "initialize from the very first scheduled seq"
    -- (used by initialize_line() after a work schedule is first added to an idle line).
    IF p_current_model IS NULL THEN
        SET v_current_seq = -1;          -- seq > -1 = find the lowest seq row
    ELSE
        SELECT seq INTO v_current_seq
        FROM   worksched
        WHERE  lineno      = p_lineno
          AND  date        = v_active_date
          AND  modelcode   = p_current_model
        ORDER  BY seq DESC LIMIT 1;

        IF v_current_seq IS NULL THEN
            LEAVE sp_block;              -- unknown model for this line/date — bail safely
        END IF;
    END IF;

    -- Next pending sequence (act < plan, seq strictly after current)
    SELECT seq, modelcode, (plan - act)
    INTO   v_next_seq, v_next_model, v_next_plan
    FROM   worksched
    WHERE  lineno = p_lineno AND date = v_active_date
      AND  seq    > v_current_seq
      AND  act    < plan
    ORDER  BY seq ASC LIMIT 1;

    IF v_next_seq IS NOT NULL THEN
        -- ── Load next model into the appropriate station ─────────────────────

        IF p_station = 'crs' THEN
            -- BOM pivot: compressor, fan motors, safety parts, serial/area reference
            SELECT partno INTO v_compmod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Compressor' LIMIT 1;
            SELECT partno INTO v_fan1mod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno INTO v_fan2mod
              FROM partref WHERE modelcode = v_next_model AND tag = 'Fan Motor' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart1mod, v_crspart1desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_crspart2mod, v_crspart2desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_crspart3mod, v_crspart3desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_crspart4mod, v_crspart4desc
              FROM partref WHERE modelcode = v_next_model AND module = 'CRS' AND tag = 'Safety Part' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT area, serialstart INTO v_area, v_serialstart
              FROM modelref WHERE modelcode = v_next_model LIMIT 1;

            UPDATE linestat SET
                status       = 'Work',
                lineno       = p_lineno,
                active_date  = v_active_date,
                crsmodelcode = v_next_model,
                crsvar       = v_next_plan,
                area         = v_area,
                serialstart  = v_serialstart,
                compmod      = v_compmod,
                fan1mod      = v_fan1mod,
                fan2mod      = v_fan2mod,
                crspart1mod  = v_crspart1mod, crspart1desc = v_crspart1desc,
                crspart2mod  = v_crspart2mod, crspart2desc = v_crspart2desc,
                crspart3mod  = v_crspart3mod, crspart3desc = v_crspart3desc,
                crspart4mod  = v_crspart4mod, crspart4desc = v_crspart4desc,
                updtime      = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = v_next_model, attvar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;

        ELSEIF p_station = 'gms' THEN
            SELECT `usage` INTO v_gascharge
              FROM partref WHERE modelcode = v_next_model AND module = 'GMS' LIMIT 1;
            IF v_gascharge IS NULL THEN SET v_gascharge = 0; END IF;
            SELECT gmstolpos, gmstolneg INTO v_gmstolpos, v_gmstolneg
              FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            IF v_gmstolpos IS NULL THEN SET v_gmstolpos = 0; END IF;
            IF v_gmstolneg IS NULL THEN SET v_gmstolneg = 0; END IF;
            UPDATE linestat SET
                gmsmodelcode = v_next_model, gmsvar = v_next_plan,
                gascharge = v_gascharge, gmstolpos = v_gmstolpos, gmstolneg = v_gmstolneg,
                updtime   = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'spamsi' THEN
            SELECT partno, partdesc INTO v_inpart1mod, v_inpart1desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_inpart2mod, v_inpart2desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_inpart3mod, v_inpart3desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 2;
            SELECT partno, partdesc INTO v_inpart4mod, v_inpart4desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 3;
            SELECT partno, partdesc INTO v_inpart5mod, v_inpart5desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 4;
            SELECT partno, partdesc INTO v_inpart6mod, v_inpart6desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSI' ORDER BY id LIMIT 1 OFFSET 5;
            SELECT spamsi_unique INTO v_spamsi_unique_code FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                inmodelcode = v_next_model, invar = v_next_plan, inunique = v_spamsi_unique_code,
                inpart1mod = v_inpart1mod, inpart1desc = v_inpart1desc,
                inpart2mod = v_inpart2mod, inpart2desc = v_inpart2desc,
                inpart3mod = v_inpart3mod, inpart3desc = v_inpart3desc,
                inpart4mod = v_inpart4mod, inpart4desc = v_inpart4desc,
                inpart5mod = v_inpart5mod, inpart5desc = v_inpart5desc,
                inpart6mod = v_inpart6mod, inpart6desc = v_inpart6desc,
                updtime    = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'spamso' THEN
            SELECT partno INTO v_spamso_outmodel FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' AND tag = 'Outdoor Control Board' ORDER BY id LIMIT 1;
            UPDATE linestat SET
                outmodelcode = v_next_model, outvar = v_next_plan,
                outmodel     = v_spamso_outmodel,
                outpart1mod  = NULL, outpart1desc = NULL,
                outpart2mod  = NULL, outpart2desc = NULL,
                outpart3mod  = NULL, outpart3desc = NULL,
                updtime     = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'wci' THEN
            UPDATE linestat SET wcimodelcode = v_next_model, wcivar = v_next_plan,
                updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;

        ELSEIF p_station = 'rit' THEN
            SELECT program_h, program_f,
                   op_current_base, op_current_tolpos, op_current_tolneg,
                   in_power_base,   in_power_tolpos,   in_power_tolneg,
                   temp_diff_base,  temp_diff_tolpos,  temp_diff_tolneg,
                   IF(ritheat1='ON', 'ON', NULL), IF(ritheat2='ON', 'ON', NULL)
            INTO @prog_h, @prog_f,
                 @opcur, @opcur_pos, @opcur_neg,
                 @oppow, @oppow_pos, @oppow_neg,
                 @tempdiff, @tempdiff_pos, @tempdiff_neg,
                 @heat1, @heat2
            FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                ritmodelcode = v_next_model, ritvar = v_next_plan,
                ritprogh    = @prog_h,       ritprogf       = @prog_f,
                ritdata1    = @opcur,        ritdata1tolpos = @opcur_pos, ritdata1tolneg = @opcur_neg,
                ritdata2    = @oppow,        ritdata2tolpos = @oppow_pos, ritdata2tolneg = @oppow_neg,
                ritdata3    = @tempdiff,     ritdata3tolpos = @tempdiff_pos, ritdata3tolneg = @tempdiff_neg,
                ritheat1    = @heat1,        ritheat2       = @heat2,
                updtime     = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'fit' THEN
            SELECT op_current_base, op_current_tolpos, op_current_tolneg,
                   in_power_base,   in_power_tolpos,   in_power_tolneg
            INTO @opcur, @opcur_pos, @opcur_neg,
                 @oppow, @oppow_pos, @oppow_neg
            FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET 
                fitmodelcode = v_next_model, fitvar = v_next_plan,
                fitdata1 = @opcur, fitdata1tolpos = @opcur_pos, fitdata1tolneg = @opcur_neg,
                fitdata2 = @oppow, fitdata2tolpos = @oppow_pos, fitdata2tolneg = @oppow_neg,
                updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;

        ELSEIF p_station = 'pit' THEN
            SELECT IF(pittws='ON', 'ON', NULL) INTO @pittws FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET pitmodelcode = v_next_model, pitvar = v_next_plan, pittws = @pittws,
                updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        END IF;

    ELSE
        -- ── No more sequences — clear the finished station ───────────────────

        IF p_station = 'crs' THEN
            UPDATE linestat SET
                crsmodelcode = NULL, crsvar = 0,
                compmod  = NULL, fan1mod = NULL, fan2mod = NULL,
                crspart1mod = NULL, crspart1desc = NULL,
                crspart2mod = NULL, crspart2desc = NULL,
                crspart3mod = NULL, crspart3desc = NULL,
                crspart4mod = NULL, crspart4desc = NULL,
                area = NULL, serialstart = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'att' THEN
            UPDATE linestat SET attmodelcode = NULL, attvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;

        ELSEIF p_station = 'gms' THEN
            UPDATE linestat SET
                gmsmodelcode = NULL, gmsvar = 0, gascharge = 0, gmstolpos = 0, gmstolneg = 0,
                updtime = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'spamsi' THEN
            UPDATE linestat SET
                inmodelcode = NULL, invar = 0, inunique = NULL,
                inpart1mod = NULL, inpart1desc = NULL,
                inpart2mod = NULL, inpart2desc = NULL,
                inpart3mod = NULL, inpart3desc = NULL,
                inpart4mod = NULL, inpart4desc = NULL,
                inpart5mod = NULL, inpart5desc = NULL,
                inpart6mod = NULL, inpart6desc = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'spamso' THEN
            UPDATE linestat SET
                outmodelcode = NULL, outvar = 0, outmodel = NULL,
                outpart1mod  = NULL, outpart1desc = NULL,
                outpart2mod  = NULL, outpart2desc = NULL,
                outpart3mod  = NULL, outpart3desc = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'wci' THEN
            UPDATE linestat SET wcimodelcode = NULL, wcivar = 0, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;

        ELSEIF p_station = 'rit' THEN
            UPDATE linestat SET
                ritmodelcode = NULL, ritvar = 0,
                ritprogh = NULL, ritprogf = NULL,
                ritdata1 = NULL, ritdata1tolpos = NULL, ritdata1tolneg = NULL,
                ritdata2 = NULL, ritdata2tolpos = NULL, ritdata2tolneg = NULL,
                ritdata3 = NULL, ritdata3tolpos = NULL, ritdata3tolneg = NULL,
                ritheat1 = NULL, ritheat2 = NULL,
                updtime = CURRENT_TIMESTAMP
            WHERE id = v_linestat_id;

        ELSEIF p_station = 'fit' THEN
            UPDATE linestat SET 
                fitmodelcode = NULL, fitvar = 0, 
                fitdata1 = NULL, fitdata1tolpos = NULL, fitdata1tolneg = NULL,
                fitdata2 = NULL, fitdata2tolpos = NULL, fitdata2tolneg = NULL,
                updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;

        ELSEIF p_station = 'pit' THEN
            UPDATE linestat SET pitmodelcode = NULL, pitvar = 0, pittws = NULL, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        END IF;

        -- If ALL stations are empty → revert to No Work
        UPDATE linestat SET status = 'No Work', active_date = NULL
        WHERE id = v_linestat_id
          AND crsmodelcode  IS NULL
          AND attmodelcode  IS NULL
          AND gmsmodelcode  IS NULL
          AND inmodelcode   IS NULL
          AND outmodelcode  IS NULL
          AND wcimodelcode   IS NULL
          AND ritmodelcode   IS NULL
          AND fitmodelcode   IS NULL
          AND pitmodelcode IS NULL;
    END IF;

END sp_block$$
DELIMITER ;

-- =======================================================
-- Triggers File for all Inspection Stations (CRS to PIT)
-- =======================================================

SET SQL_SAFE_UPDATES = 0;

DELIMITER $$

-- =======================================================
-- 1. DROP ALL EXISTING AND LEGACY TRIGGERS
-- =======================================================

-- Legacy Triggers
DROP TRIGGER IF EXISTS after_insp2_insert$$
DROP TRIGGER IF EXISTS after_insp3_run_insert$$
DROP TRIGGER IF EXISTS after_insp4_insert$$
DROP TRIGGER IF EXISTS after_packaging_insert$$

-- 9 BEFORE Triggers
DROP TRIGGER IF EXISTS before_crs_insert$$
DROP TRIGGER IF EXISTS before_att_insert$$
DROP TRIGGER IF EXISTS before_gms_insert$$
DROP TRIGGER IF EXISTS before_spamsi_insert$$
DROP TRIGGER IF EXISTS before_spamso_insert$$
DROP TRIGGER IF EXISTS before_wci_insert$$
DROP TRIGGER IF EXISTS before_rit_insert$$
DROP TRIGGER IF EXISTS before_fit_insert$$
DROP TRIGGER IF EXISTS before_pit_insert$$

-- 9 AFTER Triggers
DROP TRIGGER IF EXISTS after_crs_insert$$
DROP TRIGGER IF EXISTS after_att_insert$$
DROP TRIGGER IF EXISTS after_gms_insert$$
DROP TRIGGER IF EXISTS after_spamsi_insert$$
DROP TRIGGER IF EXISTS after_spamso_insert$$
DROP TRIGGER IF EXISTS after_wci_insert$$
DROP TRIGGER IF EXISTS after_rit_insert$$
DROP TRIGGER IF EXISTS after_fit_insert$$
DROP TRIGGER IF EXISTS after_pit_insert$$

-- =======================================================
-- 2. CREATE BEFORE TRIGGERS (Validation & Logic)
-- =======================================================

-- CRS BEFORE Trigger
CREATE TRIGGER before_crs_insert BEFORE INSERT ON crs
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR crsmodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- ATT BEFORE Trigger
CREATE TRIGGER before_att_insert BEFORE INSERT ON att
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR attmodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- GMS BEFORE Trigger
CREATE TRIGGER before_gms_insert BEFORE INSERT ON gms
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR gmsmodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- SPAMSI BEFORE Trigger
CREATE TRIGGER before_spamsi_insert BEFORE INSERT ON spamsi
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR inmodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- SPAMSO BEFORE Trigger
CREATE TRIGGER before_spamso_insert BEFORE INSERT ON spamso
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR outmodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- WCI BEFORE Trigger
CREATE TRIGGER before_wci_insert BEFORE INSERT ON wci
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR wcimodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- RIT BEFORE Trigger
CREATE TRIGGER before_rit_insert BEFORE INSERT ON rit
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR ritmodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- FIT BEFORE Trigger
CREATE TRIGGER before_fit_insert BEFORE INSERT ON fit
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR fitmodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- PIT BEFORE Trigger
CREATE TRIGGER before_pit_insert BEFORE INSERT ON pit
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    -- Strict PLC Verification
    SELECT 1, lineno INTO v_valid, v_active_lineno
    FROM linestat
    WHERE (NEW.lineno IS NULL OR NEW.lineno = '' OR lineno = NEW.lineno)
      AND (NEW.modelcode IS NULL OR pitmodelcode = NEW.modelcode)
      AND status = 'Work'
    ORDER BY id ASC LIMIT 1;
    
    IF v_valid = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'PLC Insert Rejected: Mismatching Model Code or Inactive Line.';
    END IF;
    
    -- Auto-heal missing lineno
    IF NEW.lineno IS NULL OR NEW.lineno = '' THEN
        SET NEW.lineno = v_active_lineno;
    END IF;
END$$

-- =======================================================
-- 3. CREATE AFTER TRIGGERS (Variance & Shifting)
-- =======================================================

-- CRS AFTER Trigger
CREATE TRIGGER after_crs_insert AFTER INSERT ON crs
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT id, status, crsvar, crsmodelcode
    INTO v_linestat_id, v_status, v_var, v_model
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET crsvar = crsvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('crs', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- ATT AFTER Trigger
CREATE TRIGGER after_att_insert AFTER INSERT ON att
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT id, status, attvar, attmodelcode
    INTO v_linestat_id, v_status, v_var, v_model
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET attvar = attvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('att', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- GMS AFTER Trigger
CREATE TRIGGER after_gms_insert AFTER INSERT ON gms
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT id, status, gmsvar, gmsmodelcode
    INTO v_linestat_id, v_status, v_var, v_model
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET gmsvar = gmsvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('gms', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- SPAMSI AFTER Trigger
CREATE TRIGGER after_spamsi_insert AFTER INSERT ON spamsi
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT id, status, invar, inmodelcode
    INTO v_linestat_id, v_status, v_var, v_model
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET invar = invar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('spamsi', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- SPAMSO AFTER Trigger
CREATE TRIGGER after_spamso_insert AFTER INSERT ON spamso
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT id, status, outvar, outmodelcode
    INTO v_linestat_id, v_status, v_var, v_model
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET outvar = outvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('spamso', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- WCI AFTER Trigger
CREATE TRIGGER after_wci_insert AFTER INSERT ON wci
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT id, status, wcivar, wcimodelcode
    INTO v_linestat_id, v_status, v_var, v_model
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET wcivar = wcivar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('wci', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- RIT AFTER Trigger
CREATE TRIGGER after_rit_insert AFTER INSERT ON rit
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT id, status, ritvar, ritmodelcode
    INTO v_linestat_id, v_status, v_var, v_model
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET ritvar = ritvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('rit', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- FIT AFTER Trigger
CREATE TRIGGER after_fit_insert AFTER INSERT ON fit
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT id, status, fitvar, fitmodelcode
    INTO v_linestat_id, v_status, v_var, v_model
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET fitvar = fitvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('fit', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- PIT AFTER Trigger
CREATE TRIGGER after_pit_insert AFTER INSERT ON pit
FOR EACH ROW
BEGIN
    DECLARE v_linestat_id INT;
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    DECLARE v_active_date DATE;
    DECLARE v_worksched_id INT;
    
    SELECT id, status, pitvar, pitmodelcode, active_date 
    INTO v_linestat_id, v_status, v_var, v_model, v_active_date
    FROM linestat 
    WHERE lineno = NEW.lineno
    LIMIT 1;
    
    IF v_linestat_id IS NOT NULL AND v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET pitvar = pitvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = v_linestat_id;
        SET v_var = v_var - 1;
        
        -- Retrieve the Primary Key to bypass Safe Update mode
        SELECT id INTO v_worksched_id FROM worksched 
        WHERE date = v_active_date 
          AND lineno = NEW.lineno 
          AND modelcode = v_model 
        LIMIT 1;
        
        IF v_worksched_id IS NOT NULL THEN
            UPDATE worksched 
            SET act = act + 1 
            WHERE id = v_worksched_id;
        END IF;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('pit', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

DELIMITER ;



-- 7. Alter ModelRef
ALTER TABLE modelref ADD COLUMN ritheat1 VARCHAR(2) NULL, ADD COLUMN ritheat2 VARCHAR(2) NULL;


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


CREATE TABLE linestat (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	updtime TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
	lineno VARCHAR(4), 
	active_date DATE, -- Not on PLC
	status VARCHAR(12) DEFAULT 'No Work', 

    -- CRS
	crsmodelcode VARCHAR(14), 
	compmod VARCHAR(14), 
	fan1mod VARCHAR(14), 
	fan2mod VARCHAR(14), 
	crspart1mod VARCHAR(14), 
	crspart1desc VARCHAR(30), 
	crspart2mod VARCHAR(14), 
	crspart2desc VARCHAR(30), 
	crspart3mod VARCHAR(14), 
	crspart3desc VARCHAR(30), 
	crspart4mod VARCHAR(14), 
	crspart4desc VARCHAR(30), 
	area VARCHAR(14), 
	serialstart VARCHAR(6), 
	crsvar INTEGER, 
	reserve1 VARCHAR(20), 

    -- ATT
	attmodelcode VARCHAR(14), 
	attvar INTEGER, 

    -- GMS
	gmsmodelcode VARCHAR(14), 
	gmsvar INTEGER, 
	gascharge DECIMAL(4, 2) NOT NULL DEFAULT 0.00, 
	gmstolpos DECIMAL(2, 0) DEFAULT 0, 
	gmstolneg DECIMAL(2, 0) DEFAULT 0,

    -- SPAMSI 
	inmodelcode VARCHAR(14),
	invar INTEGER,
	inunique VARCHAR(4),
	inpart1mod VARCHAR(14), inpart1desc VARCHAR(30),
	inpart2mod VARCHAR(14), inpart2desc VARCHAR(30),
	inpart3mod VARCHAR(14), inpart3desc VARCHAR(30),
	inpart4mod VARCHAR(14), inpart4desc VARCHAR(30),
	inpart5mod VARCHAR(14), inpart5desc VARCHAR(30),
	inpart6mod VARCHAR(14), inpart6desc VARCHAR(30),

    -- SPAMSO
	outmodelcode VARCHAR(14),
	outvar INTEGER,
    outmodel VARCHAR(14), 
	outpart1mod VARCHAR(14), outpart1desc VARCHAR(30),
	outpart2mod VARCHAR(14), outpart2desc VARCHAR(30),
	outpart3mod VARCHAR(14), outpart3desc VARCHAR(30),

    -- WCI
    wcimodelcode VARCHAR(14),       -- wcmodelcode VARCHAR(14),     
    wcivar INTEGER,                 -- wcvar INTEGER,    

    -- RIT
    ritmodelcode VARCHAR(14),       -- rimodelcode VARCHAR(14),
    ritvar INTEGER,                 -- rivar INTEGER,
    ritprogh VARCHAR(6),            -- ri_progh VARCHAR(6),
    ritprogf VARCHAR(6),            -- ri_progf VARCHAR(6),
    ritdata1 DECIMAL (4,2),         -- ri_opcur DECIMAL (8,2),
    ritdata1tolpos DECIMAL (4,2),   -- ri_opcur_pos DECIMAL (2,0),
    ritdata1tolneg DECIMAL (4,2),   -- ri_opcur_neg DECIMAL (2,0),
    ritdata2 DECIMAL (4,2),         -- ri_oppow DECIMAL (8,2),
    ritdata2tolpos DECIMAL (4,2),   -- ri_oppow_pos DECIMAL (2,0),
    ritdata2tolneg DECIMAL (4,2),   -- ri_oppow_neg DECIMAL (2,0),
    ritdata3 DECIMAL (4,2),         -- ri_tempdiff DECIMAL (8,2),
    ritdata3tolpos DECIMAL (4,2),   -- ri_tempdiff_pos DECIMAL (2,0),
    ritdata3tolneg DECIMAL (4,2),   -- ri_tempdiff_neg DECIMAL (2,0),
    ritheat1 VARCHAR(2),            -- on the new model we will add a new textbox to ask if this model is "on" or null for heating of evaporator tubes
    ritheat2 VARCHAR(2),            -- on the new model we will add a new textbox to ask if this model is "on" or null for heating of condenser tubes

    -- FIT
    fitmodelcode VARCHAR(14),       -- fimodelcode VARCHAR(14),      
    fitvar INTEGER,                 -- fivar INTEGER,     
    fitdata1 DECIMAL (4,2),         -- fi_opcur DECIMAL (5,2), base of operating current (from modelref) depends on modelcode of the station
    fitdata1tolpos DECIMAL (4,2),   -- tolerance from the positive side of operating current (from modelref)
    fitdata1tolneg DECIMAL (4,2),   -- tolerance from the negative side of operating current (from modelref)
    fitdata2 DECIMAL (4,2),         -- fi_oppow DECIMAL (5,2), base of input power (from modelref) depends on modelcode of the station
    fitdata2tolpos DECIMAL (4,2),   -- tolerance from the positive side of input power (from modelref)
    fitdata2tolneg DECIMAL (4,2),   -- tolerance from the negative side of input power (from modelref)

    -- PIT
    ptmodelcode VARCHAR(14),        -- packmodelcode VARCHAR(14),
    ptvar INTEGER,                  -- packvar INTEGER,

	PRIMARY KEY (id) 
);

-- Dynamic Area configuration. Safe to run after modelref exists.
CREATE TABLE IF NOT EXISTS `areas` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `name`        VARCHAR(50) NOT NULL,
    `description` VARCHAR(255) NULL,
    `is_active`   BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_areas_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `areas` (`name`) VALUES
    ('Domestic'), ('HongKong'), ('Export'), ('Taiwan');

INSERT IGNORE INTO `areas` (`name`)
SELECT DISTINCT TRIM(`area`)
FROM `modelref`
WHERE `area` IS NOT NULL AND TRIM(`area`) <> '';

-- Per-model SPAMSI code reference for the existing linestat.inunique field.
CREATE TABLE IF NOT EXISTS `spamsi_unique_refs` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `unique_code` VARCHAR(4) NOT NULL,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_spamsi_unique_ref_modelcode` (`modelcode`),
    UNIQUE KEY `uq_spamsi_unique_ref_code` (`unique_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


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

-- Table insp2 to wci 
CREATE TABLE wci (                      -- CREATE TABLE insp2 (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
    status1 VARCHAR(12) NOT NULL, 
    status2 VARCHAR(12) NOT NULL, 
    status3 VARCHAR(12) NOT NULL, 
    status4 VARCHAR(12) NOT NULL, 
    overallstatus VARCHAR(12),
	time TIMESTAMP NOT NULL,            -- alter column time_in
    inspector VARCHAR(20),              -- time TIMESTAMP NOT NULL,
	lineno VARCHAR(4),
	PRIMARY KEY (id)
);

-- Table insp3_run to rit
CREATE TABLE rit (                                          -- CREATE TABLE insp3_run (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
	status1 VARCHAR(12), 
	status2 VARCHAR(12),
	status3 VARCHAR(12), 
	status4 VARCHAR(12), 
	status5 VARCHAR(12), 
	status6 VARCHAR(12),
	status7 VARCHAR(12),
	status8 VARCHAR(12),
	status9 VARCHAR(12),
    data1 DECIMAL(4,2),
	status10 VARCHAR(12),
    data2 DECIMAL(4,2),
    status11 VARCHAR(12),
    data3 DECIMAL(4,2),
    status12 VARCHAR(12),
    progh VARCHAR(6),
    progf VARCHAR(6),
    overallstatus VARCHAR(12),
    time TIMESTAMP NOT NULL,
	inspector VARCHAR(20), 
    lineno VARCHAR(4),
	PRIMARY KEY (id)
);

-- Table insp4 to fit
CREATE TABLE fit (                      -- CREATE TABLE insp4 (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL,  
	status1 VARCHAR(12), 
    status2 VARCHAR(12),
    status3 VARCHAR(12),
    data1 DECIMAL(4,2),
    data2 DECIMAL(4,2),
    status4 VARCHAR(12),
    status5 VARCHAR(12),
    status6 VARCHAR(12),
    status7 VARCHAR(12),
    status8 VARCHAR(12),
    status9 VARCHAR(12),
    status10 VARCHAR(12),
    overallstatus VARCHAR(12),
    time TIMESTAMP NOT NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4),
	PRIMARY KEY (id)
);

-- Table packaging to pit
CREATE TABLE pit(
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14), 
	serial VARCHAR(14), 
	status1 VARCHAR(12), 
	status2 VARCHAR(12), 
	status3 VARCHAR(12),
	status4 VARCHAR(12),
    overallstatus VARCHAR(12),  
	time TIMESTAMP NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4) NOT NULL, 
	PRIMARY KEY (id)
);

-- 009_apply_renames.sql
-- Massive table refactoring and linestat schema update

-- 1. Rename Tables
RENAME TABLE insp2 TO wci;
RENAME TABLE insp3_run TO rit;
RENAME TABLE insp4 TO fit;
RENAME TABLE packaging TO pit;

-- 2. Alter WCI
-- Note: Adjusting from the original python model (test_wiring_seq, etc.) to status1-4. 
-- If the DB was already partially altered, some of these might need tweaking.
ALTER TABLE wci 
    CHANGE test_wiring_seq status1 VARCHAR(12),
    CHANGE test_no_touching status2 VARCHAR(12),
    CHANGE test_no_misaligned status3 VARCHAR(12),
    CHANGE test_no_lacking status4 VARCHAR(12),
    CHANGE status overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 3. Alter RIT
ALTER TABLE rit
    CHANGE `insulation_resistance/withstand_voltage` status1 VARCHAR(12),
    CHANGE `airswing` status2 VARCHAR(12),
    CHANGE `comp_operation` status3 VARCHAR(12),
    CHANGE `fan_operation` status4 VARCHAR(12),
    CHANGE `evap_tubes_cool` status5 VARCHAR(12),
    CHANGE `evap_tubes_heat` status6 VARCHAR(12),
    CHANGE `cond_tubes_cool` status7 VARCHAR(12),
    CHANGE `cond_tubes_heat` status8 VARCHAR(12),
    CHANGE `leak_status` status9 VARCHAR(12),
    CHANGE `operating_current` data1 DECIMAL(4,2),
    CHANGE `input_power` data2 DECIMAL(4,2),
    CHANGE `temp_diff` data3 DECIMAL(4,2),
    CHANGE `prog_check_h` progh VARCHAR(6),
    CHANGE `prog_check_f` progf VARCHAR(6),
    CHANGE `leak_location` status10 VARCHAR(12), -- reusing column loosely
    ADD COLUMN status11 VARCHAR(12),
    ADD COLUMN status12 VARCHAR(12),
    ADD COLUMN overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 4. Alter FIT
ALTER TABLE fit
    CHANGE `insulation_resistance/withstand_voltage` status1 VARCHAR(12),
    CHANGE `operating_current/input_power` status2 VARCHAR(12),
    CHANGE `nameplate_match` status3 VARCHAR(12),
    CHANGE `model_label` status4 VARCHAR(12),
    CHANGE `correct_manual` status5 VARCHAR(12),
    CHANGE `has_remote` status6 VARCHAR(12),
    CHANGE `has_warranty` status7 VARCHAR(12),
    CHANGE `has_screws` status8 VARCHAR(12),
    CHANGE `grille_eel` status9 VARCHAR(12),
    ADD COLUMN overallstatus VARCHAR(12),
    ADD COLUMN lineno VARCHAR(4);

-- 5. Alter PIT
ALTER TABLE pit
    ADD COLUMN overallstatus VARCHAR(12);

-- 6. Alter Linestat
ALTER TABLE linestat
    -- WCI
    CHANGE wcmodelcode wcimodelcode VARCHAR(14),
    CHANGE wcvar wcivar INTEGER,
    
    -- RIT
    CHANGE rimodelcode ritmodelcode VARCHAR(14),
    CHANGE rivar ritvar INTEGER,
    CHANGE ri_progh ritprogh VARCHAR(6),
    CHANGE ri_progf ritprogf VARCHAR(6),
    CHANGE ri_opcur ritdata1 DECIMAL(4,2),
    CHANGE ri_opcur_pos ritdata1tolpos DECIMAL(4,2),
    CHANGE ri_opcur_neg ritdata1tolneg DECIMAL(4,2),
    CHANGE ri_oppow ritdata2 DECIMAL(4,2),
    CHANGE ri_oppow_pos ritdata2tolpos DECIMAL(4,2),
    CHANGE ri_oppow_neg ritdata2tolneg DECIMAL(4,2),
    CHANGE ri_tempdiff ritdata3 DECIMAL(4,2),
    CHANGE ri_tempdiff_pos ritdata3tolpos DECIMAL(4,2),
    CHANGE ri_tempdiff_neg ritdata3tolneg DECIMAL(4,2),
    ADD COLUMN ritheat1 VARCHAR(2),
    ADD COLUMN ritheat2 VARCHAR(2),
    
    -- FIT
    CHANGE fimodelcode fitmodelcode VARCHAR(14),
    CHANGE fivar fitvar INTEGER,
    CHANGE fi_opcur fitdata1 DECIMAL(4,2),
    ADD COLUMN fitdata1tolpos DECIMAL(4,2),
    ADD COLUMN fitdata1tolneg DECIMAL(4,2),
    CHANGE fi_oppow fitdata2 DECIMAL(4,2),
    ADD COLUMN fitdata2tolpos DECIMAL(4,2),
    ADD COLUMN fitdata2tolneg DECIMAL(4,2),

    -- PIT
    CHANGE packmodelcode ptmodelcode VARCHAR(14),
    CHANGE packvar ptvar INTEGER;


-- 7. Alter ModelRef
ALTER TABLE modelref ADD COLUMN ritheat1 VARCHAR(2) NULL, ADD COLUMN ritheat2 VARCHAR(2) NULL;

ALTER TABLE modelref
    MODIFY COLUMN op_current_base DECIMAL(4,2),
    MODIFY COLUMN op_current_tolpos DECIMAL(4,2),
    MODIFY COLUMN op_current_tolneg DECIMAL(4,2),
    MODIFY COLUMN in_power_base DECIMAL(4,2),
    MODIFY COLUMN in_power_tolpos DECIMAL(4,2),
    MODIFY COLUMN in_power_tolneg DECIMAL(4,2),
    MODIFY COLUMN temp_diff_base DECIMAL(4,2),
    MODIFY COLUMN temp_diff_tolpos DECIMAL(4,2),
    MODIFY COLUMN temp_diff_tolneg DECIMAL(4,2);

ALTER TABLE linestat 
    CHANGE ptmodelcode pitmodelcode VARCHAR(14),
    CHANGE ptvar pitvar INTEGER;

-- 8. Refactor CRS part serials and SPAMSO
ALTER TABLE crs 
    MODIFY part1serial VARCHAR(34), 
    MODIFY part2serial VARCHAR(34), 
    MODIFY part3serial VARCHAR(34), 
    MODIFY part4serial VARCHAR(34);

ALTER TABLE spamso 
    MODIFY outserial VARCHAR(14);

CREATE INDEX idx_spamsi_serial ON spamsi (serial);
CREATE INDEX idx_spamso_serial ON spamso (serial);

-- 9. Add overallstatus to ATT and idx_att_serial
ALTER TABLE att ADD COLUMN overallstatus VARCHAR(12) AFTER status3;
CREATE INDEX idx_att_serial ON att (serial);

-- 10. Add status5, status6, status7 to WCI
ALTER TABLE wci 
    ADD COLUMN status5 VARCHAR(12) AFTER status4,
    ADD COLUMN status6 VARCHAR(12) AFTER status5,
    ADD COLUMN status7 VARCHAR(12) AFTER status6;
CREATE INDEX idx_wci_serial ON wci (serial);

-- 11. Add serial indexes to GMS, RIT, FIT, PIT
CREATE INDEX idx_gms_serial ON gms (serial);
CREATE INDEX idx_rit_serial ON rit (serial);
CREATE INDEX idx_fit_serial ON fit (serial);
CREATE INDEX idx_pit_serial ON pit (serial);

-- 12. Migrate SPAMSO outmodel to partref and drop spamso_outmodel_refs
INSERT INTO partref (modelcode, module, partno, partdesc, `usage`, tag)
SELECT modelcode, 'SPAMSO', outmodel, 'Outdoor Control Board', 1, 'Outdoor Control Board'
FROM spamso_outmodel_refs
WHERE outmodel IS NOT NULL AND outmodel != '';
DROP TABLE IF EXISTS `spamso_outmodel_refs`;

-- 13. Widen tags to VARCHAR(30) and register Outdoor Control Board tag
ALTER TABLE `partref` MODIFY COLUMN `tag` VARCHAR(30) NOT NULL;
ALTER TABLE `tags` MODIFY COLUMN `name` VARCHAR(30) NOT NULL;
INSERT IGNORE INTO `tags` (`name`, `description`, `is_active`) VALUES ('Outdoor Control Board', 'SPAMSO Outdoor Control Board reference', 1);

-- 14. Widen spamso.outserial to VARCHAR(44)
ALTER TABLE `spamso` MODIFY COLUMN `outserial` VARCHAR(44);


