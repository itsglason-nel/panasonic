-- 005_fix_pit_trigger.sql
-- Fixes the Continuous Queue bug where PIT station loses track of the worksched if the active_date shifts forward.
-- Replaces date = v_active_date lookup with a global chronological lookup.

DELIMITER $$

DROP TRIGGER IF EXISTS after_pit_insert$$

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
        
        -- Retrieve the Primary Key for the chronologically oldest unfinished schedule for this model.
        -- We drop the 'date = v_active_date' constraint so that if CRS shifted the date forward, 
        -- PIT can still find and increment the historical schedule that these units belong to.
        SELECT id INTO v_worksched_id FROM worksched 
        WHERE lineno = NEW.lineno 
          AND modelcode = v_model 
          AND act < plan
        ORDER BY date ASC, seq ASC
        LIMIT 1;
        
        -- Fallback if all sequences for this model are completed (overshooting)
        IF v_worksched_id IS NULL THEN
            SELECT id INTO v_worksched_id FROM worksched 
            WHERE lineno = NEW.lineno 
              AND modelcode = v_model 
            ORDER BY date DESC, seq DESC
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
