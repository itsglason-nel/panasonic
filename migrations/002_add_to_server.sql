ALTER TABLE linestat ADD COLUMN gascharge DECIMAL(4,2) NOT NULL DEFAULT 0.00 AFTER gmsvar;

ALTER TABLE linestat
    ADD COLUMN wcmodelcode VARCHAR(14), ADD COLUMN wcvar INTEGER,
    
    ADD COLUMN rimodelcode VARCHAR(14), ADD COLUMN rivar INTEGER,
    ADD COLUMN ri_progh VARCHAR(6), ADD COLUMN ri_progf VARCHAR(6),
    ADD COLUMN ri_opcur DECIMAL(8,2), ADD COLUMN ri_opcur_pos DECIMAL(2,0), ADD COLUMN ri_opcur_neg DECIMAL(2,0),
    ADD COLUMN ri_oppow DECIMAL(8,2), ADD COLUMN ri_oppow_pos DECIMAL(2,0), ADD COLUMN ri_oppow_neg DECIMAL(2,0),
    ADD COLUMN ri_tempdiff DECIMAL(8,2), ADD COLUMN ri_tempdiff_pos DECIMAL(2,0), ADD COLUMN ri_tempdiff_neg DECIMAL(2,0),
    
    ADD COLUMN fimodelcode VARCHAR(14), ADD COLUMN fivar INTEGER,
    ADD COLUMN fi_opcur DECIMAL(5,2), ADD COLUMN fi_oppow DECIMAL(5,2),
    
    ADD COLUMN packmodelcode VARCHAR(14), ADD COLUMN packvar INTEGER;


-- Drop users table 
INSERT IGNORE INTO `users` (`id`, `username`, `password_hash`, `full_name`, `role`, `must_change_password`) VALUES
    (2, 'dev_glaee', 'scrypt:32768:8:1$BGIEyY4lKmHpdNCF$8afb6db376d8f1197525e44cc281f4bbe3b77fa39625f6bc61b61c1dabcec5a8642ee5bb2917401c28504e39c7e34c2bdc32c2b3873cb5021672eb0d70a92dc0', 'System Administrator', 'admin', 1);

-- ---------------------------------------------------------
-- Table 1: SAFETY PARTS MONITORING SYSTEM INDOOR (SPAMSI)
-- ---------------------------------------------------------
CREATE TABLE SPAMSI (
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
     lineno VARCHAR(4)
);

-- ---------------------------------------------------------
-- Table 2: SAFETY PARTS MONITORING SYSTEM OUTDOOR (SPAMSO)
-- ---------------------------------------------------------
CREATE TABLE SPAMSO (
    id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    modelcode VARCHAR(14),
    `serial` VARCHAR(14),
    outmodel VARCHAR(14),
    outserial VARCHAR(30),
    
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
    lineno VARCHAR(4)
);

-- ================================================================
-- Add SPAMSI and SPAMSO to linestat
-- ================================================================

-- 1. Add 23 new columns to linestat
ALTER TABLE linestat
    ADD COLUMN inmodelcode VARCHAR(14),
    ADD COLUMN invar INTEGER,
    ADD COLUMN inuniqe VARCHAR(4),
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
    DECLARE v_outpart1mod VARCHAR(14); DECLARE v_outpart1desc VARCHAR(30);
    DECLARE v_outpart2mod VARCHAR(14); DECLARE v_outpart2desc VARCHAR(30);
    DECLARE v_outpart3mod VARCHAR(14); DECLARE v_outpart3desc VARCHAR(30);
    
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
            SELECT unique_code INTO v_spamsi_unique_code FROM spamsi_unique_refs WHERE modelcode = v_next_model LIMIT 1;
            
            UPDATE linestat SET 
                inmodelcode = v_next_model, invar = v_next_plan, inuniqe = v_spamsi_unique_code, updtime = CURRENT_TIMESTAMP,
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
                inmodelcode = NULL, invar = 0, inuniqe = NULL, updtime = CURRENT_TIMESTAMP,
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

DROP TRIGGER IF EXISTS after_crs_insert$$
CREATE TRIGGER after_crs_insert AFTER INSERT ON crs
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT status, crsvar, crsmodelcode INTO v_status, v_var, v_model FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET crsvar = crsvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('crs', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS after_att_insert$$
CREATE TRIGGER after_att_insert AFTER INSERT ON att
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT status, attvar, attmodelcode INTO v_status, v_var, v_model FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET attvar = attvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('att', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS after_gms_insert$$
CREATE TRIGGER after_gms_insert AFTER INSERT ON gms
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT status, gmsvar, gmsmodelcode
    INTO v_status, v_var, v_model 
    FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET gmsvar = gmsvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('gms', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS after_spamsi_insert$$
CREATE TRIGGER after_spamsi_insert AFTER INSERT ON spamsi
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT status, invar, inmodelcode INTO v_status, v_var, v_model FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET invar = invar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('spamsi', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS after_spamso_insert$$
CREATE TRIGGER after_spamso_insert AFTER INSERT ON spamso
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    DECLARE v_lineno VARCHAR(4) DEFAULT 'L1';
    DECLARE v_active_date DATE;
    
    SELECT status, outvar, outmodelcode, active_date 
    INTO v_status, v_var, v_model, v_active_date 
    FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        -- Decrement the local station variable in linestat
        UPDATE linestat SET outvar = outvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        -- Increment the actual worksched act count
        UPDATE worksched 
        SET act = act + 1 
        WHERE date = v_active_date 
          AND lineno = v_lineno 
          AND modelcode = v_model;
          
        -- If schedule completed at this station, pivot to the next sequence
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('spamso', v_lineno, v_model);
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS after_insp2_insert$$
CREATE TRIGGER after_insp2_insert AFTER INSERT ON insp2
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    -- insp2 doesn't have a lineno column? Let's check schema. Assuming we can pass a dummy 'L1' or get from CRS
    -- Wait, the new triggers need NEW.lineno if it has it. Let's assume insp2 doesn't have lineno?
    -- Actually, we can get lineno from linestat itself!
    DECLARE v_lineno VARCHAR(4);
    SELECT status, wcvar, wcmodelcode, lineno INTO v_status, v_var, v_model, v_lineno FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET wcvar = wcvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('wc', v_lineno, v_model);
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS after_insp3_run_insert$$
CREATE TRIGGER after_insp3_run_insert AFTER INSERT ON insp3_run
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    DECLARE v_lineno VARCHAR(4);
    
    SELECT status, rivar, rimodelcode, lineno INTO v_status, v_var, v_model, v_lineno FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET rivar = rivar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('ri', v_lineno, v_model);
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS after_insp4_insert$$
CREATE TRIGGER after_insp4_insert AFTER INSERT ON insp4
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    DECLARE v_lineno VARCHAR(4);
    
    SELECT status, fivar, fimodelcode, lineno INTO v_status, v_var, v_model, v_lineno FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET fivar = fivar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('fi', v_lineno, v_model);
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS after_packaging_insert$$
CREATE TRIGGER after_packaging_insert AFTER INSERT ON packaging
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    DECLARE v_lineno VARCHAR(4);
    DECLARE v_active_date DATE;
    
    SELECT status, packvar, packmodelcode, lineno, active_date INTO v_status, v_var, v_model, v_lineno, v_active_date FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET packvar = packvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        -- Increment the actual worksched act count
        UPDATE worksched 
        SET act = act + 1 
        WHERE date = v_active_date 
          AND lineno = v_lineno 
          AND modelcode = v_model;
          
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('pack', v_lineno, v_model);
        END IF;
    END IF;
END$$

DELIMITER ;

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
    `op_current_base`   DECIMAL(8,2) DEFAULT 0,
    `op_current_tolpos` DECIMAL(2,0) DEFAULT 0,
    `op_current_tolneg` DECIMAL(2,0) DEFAULT 0,
    -- Input Power Tolerance
    `in_power_base`   DECIMAL(8,2) DEFAULT 0,
    `in_power_tolpos`   DECIMAL(2,0) DEFAULT 0,
    `in_power_tolneg`   DECIMAL(2,0) DEFAULT 0,
    -- Temperature Difference Tolerance
    `temp_diff_base`   DECIMAL(8,2) DEFAULT 0,
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
('Morning', '06:00:00', '14:00:00'),
('Afternoon', '14:00:00', '22:00:00'),
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

    -- SPAMSI BOM variables
    DECLARE v_inpart1mod VARCHAR(14); DECLARE v_inpart1desc VARCHAR(30);
    DECLARE v_inpart2mod VARCHAR(14); DECLARE v_inpart2desc VARCHAR(30);
    DECLARE v_inpart3mod VARCHAR(14); DECLARE v_inpart3desc VARCHAR(30);
    DECLARE v_inpart4mod VARCHAR(14); DECLARE v_inpart4desc VARCHAR(30);
    DECLARE v_inpart5mod VARCHAR(14); DECLARE v_inpart5desc VARCHAR(30);
    DECLARE v_inpart6mod VARCHAR(14); DECLARE v_inpart6desc VARCHAR(30);

    -- SPAMSO BOM variables
    DECLARE v_outpart1mod VARCHAR(14); DECLARE v_outpart1desc VARCHAR(30);
    DECLARE v_outpart2mod VARCHAR(14); DECLARE v_outpart2desc VARCHAR(30);
    DECLARE v_outpart3mod VARCHAR(14); DECLARE v_outpart3desc VARCHAR(30);

    DECLARE v_spamsi_unique_code VARCHAR(4);
    DECLARE v_spamso_outmodel    VARCHAR(14);

    START TRANSACTION;

    -- Resolve active date (midnight roll-over safe)
    SELECT active_date INTO v_active_date FROM linestat WHERE id = 1;
    IF v_active_date IS NULL THEN
        SET v_active_date = CURDATE();
        UPDATE linestat SET active_date = v_active_date WHERE id = 1;
    END IF;

    -- Current sequence for this station+model
    SELECT seq INTO v_current_seq
    FROM worksched
    WHERE lineno = p_lineno AND date = v_active_date AND modelcode = p_current_model
    ORDER BY seq DESC LIMIT 1;

    IF v_current_seq IS NULL THEN
        COMMIT;
        LEAVE sp_block;
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
            UPDATE linestat SET crsmodelcode = v_next_model, crsvar = v_next_plan, updtime = CURRENT_TIMESTAMP WHERE id = 1;

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
            SELECT unique_code INTO v_spamsi_unique_code FROM spamsi_unique_refs WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                inmodelcode = v_next_model, invar = v_next_plan, inuniqe = v_spamsi_unique_code,
                inpart1mod = v_inpart1mod, inpart1desc = v_inpart1desc,
                inpart2mod = v_inpart2mod, inpart2desc = v_inpart2desc,
                inpart3mod = v_inpart3mod, inpart3desc = v_inpart3desc,
                inpart4mod = v_inpart4mod, inpart4desc = v_inpart4desc,
                inpart5mod = v_inpart5mod, inpart5desc = v_inpart5desc,
                inpart6mod = v_inpart6mod, inpart6desc = v_inpart6desc,
                updtime = CURRENT_TIMESTAMP
            WHERE id = 1;

        ELSEIF p_station = 'spamso' THEN
            SELECT partno, partdesc INTO v_outpart1mod, v_outpart1desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' ORDER BY id LIMIT 1 OFFSET 0;
            SELECT partno, partdesc INTO v_outpart2mod, v_outpart2desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' ORDER BY id LIMIT 1 OFFSET 1;
            SELECT partno, partdesc INTO v_outpart3mod, v_outpart3desc FROM partref WHERE modelcode = v_next_model AND module = 'SPAMSO' ORDER BY id LIMIT 1 OFFSET 2;
            -- Auto-populate outmodel from spamso_outmodel_refs
            SELECT outmodel INTO v_spamso_outmodel FROM spamso_outmodel_refs WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET
                outmodelcode = v_next_model, outvar = v_next_plan,
                outmodel = v_spamso_outmodel,
                outpart1mod = v_outpart1mod, outpart1desc = v_outpart1desc,
                outpart2mod = v_outpart2mod, outpart2desc = v_outpart2desc,
                outpart3mod = v_outpart3mod, outpart3desc = v_outpart3desc,
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

        ELSEIF p_station = 'pack' THEN
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
                inmodelcode = NULL, invar = 0, inuniqe = NULL,
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
                outpart1mod = NULL, outpart1desc = NULL,
                outpart2mod = NULL, outpart2desc = NULL,
                outpart3mod = NULL, outpart3desc = NULL,
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

        ELSEIF p_station = 'pack' THEN
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
