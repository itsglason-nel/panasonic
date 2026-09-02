DELIMITER $$

-- Modify SPAMSO Trigger
DROP TRIGGER IF EXISTS after_spamso_insert$$
CREATE TRIGGER after_spamso_insert AFTER INSERT ON spamso
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(12);
    DECLARE v_var INT;
    DECLARE v_model VARCHAR(14);
    
    SELECT status, outvar, outmodelcode INTO v_status, v_var, v_model FROM linestat WHERE id = 1;
    
    IF v_status = 'Work' AND v_var > 0 THEN
        UPDATE linestat SET outvar = outvar - 1, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        SET v_var = v_var - 1;
        
        IF v_var = 0 THEN
            CALL sp_linestat_shift_sequence('spamso', NEW.lineno, v_model);
        END IF;
    END IF;
END$$

-- WC (insp2) Trigger
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

-- RI (insp3_run) Trigger
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

-- FI (insp4) Trigger
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

-- PACK (packaging) Trigger
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
