-- =======================================================
-- Triggers File for all Inspection Stations (CRS to PIT)
-- =======================================================

SET SQL_SAFE_UPDATES = 0;

DELIMITER $$

-- =======================================================
-- 1. CREATE BEFORE TRIGGERS (Validation & Logic)
-- =======================================================

-- CRS BEFORE Trigger
CREATE TRIGGER before_crs_insert BEFORE INSERT ON crs
FOR EACH ROW
BEGIN
    DECLARE v_valid INT DEFAULT 0;
    DECLARE v_active_lineno VARCHAR(4);
    
    IF NEW.serial IS NOT NULL THEN SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', '')); END IF;
    IF NEW.modelcode IS NOT NULL THEN SET NEW.modelcode = TRIM(REPLACE(REPLACE(REPLACE(NEW.modelcode, CHAR(0), ''), '\r', ''), '\n', '')); END IF;
    IF NEW.lineno IS NOT NULL THEN SET NEW.lineno = TRIM(REPLACE(REPLACE(REPLACE(NEW.lineno, CHAR(0), ''), '\r', ''), '\n', '')); END IF;

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
    
    IF NEW.serial IS NOT NULL THEN SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', '')); END IF;
    IF NEW.modelcode IS NOT NULL THEN SET NEW.modelcode = TRIM(REPLACE(REPLACE(REPLACE(NEW.modelcode, CHAR(0), ''), '\r', ''), '\n', '')); END IF;
    IF NEW.lineno IS NOT NULL THEN SET NEW.lineno = TRIM(REPLACE(REPLACE(REPLACE(NEW.lineno, CHAR(0), ''), '\r', ''), '\n', '')); END IF;

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
    
    IF NEW.serial IS NOT NULL THEN SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', '')); END IF;
    IF NEW.modelcode IS NOT NULL THEN SET NEW.modelcode = TRIM(REPLACE(REPLACE(REPLACE(NEW.modelcode, CHAR(0), ''), '\r', ''), '\n', '')); END IF;
    IF NEW.lineno IS NOT NULL THEN SET NEW.lineno = TRIM(REPLACE(REPLACE(REPLACE(NEW.lineno, CHAR(0), ''), '\r', ''), '\n', '')); END IF;

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
    
    -- Clean serial
    IF NEW.serial IS NOT NULL THEN
        SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', ''));
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
    
    -- Clean serial
    IF NEW.serial IS NOT NULL THEN
        SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', ''));
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
    
    -- Clean serial
    IF NEW.serial IS NOT NULL THEN
        SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', ''));
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
    
    -- Clean serial
    IF NEW.serial IS NOT NULL THEN
        SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', ''));
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
    
    -- Clean serial
    IF NEW.serial IS NOT NULL THEN
        SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', ''));
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
    
    -- Clean serial
    IF NEW.serial IS NOT NULL THEN
        SET NEW.serial = TRIM(REPLACE(REPLACE(REPLACE(NEW.serial, CHAR(0), ''), '\r', ''), '\n', ''));
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
        
        -- Retrieve the Primary Key for the currently active schedule
        SELECT id INTO v_worksched_id FROM worksched 
        WHERE date = v_active_date 
          AND lineno = NEW.lineno 
          AND modelcode = v_model 
          AND act < plan
        ORDER BY seq ASC
        LIMIT 1;
        
        -- Fallback if all sequences for this model are completed
        IF v_worksched_id IS NULL THEN
            SELECT id INTO v_worksched_id FROM worksched 
            WHERE date = v_active_date 
              AND lineno = NEW.lineno 
              AND modelcode = v_model 
            ORDER BY seq DESC
            LIMIT 1;
        END IF;
        
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
