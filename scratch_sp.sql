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

    -- RI Variables
    DECLARE v_ri_progh VARCHAR(6);
    DECLARE v_ri_progf VARCHAR(6);
    DECLARE v_ri_opcur DECIMAL(8,2);
    DECLARE v_ri_opcur_pos DECIMAL(2,0);
    DECLARE v_ri_opcur_neg DECIMAL(2,0);
    DECLARE v_ri_oppow DECIMAL(8,2);
    DECLARE v_ri_oppow_pos DECIMAL(2,0);
    DECLARE v_ri_oppow_neg DECIMAL(2,0);
    DECLARE v_ri_tempdiff DECIMAL(8,2);
    DECLARE v_ri_tempdiff_pos DECIMAL(2,0);
    DECLARE v_ri_tempdiff_neg DECIMAL(2,0);

    -- FI Variables
    DECLARE v_fi_opcur DECIMAL(5,2);
    DECLARE v_fi_oppow DECIMAL(5,2);
    
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
        ELSEIF p_station = 'wc' THEN
            UPDATE linestat SET wcmodelcode = v_next_model, wcvar = v_next_plan, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'ri' THEN
            SELECT program_h, program_f, op_current_base, op_current_tolpos, op_current_tolneg, in_power_base, in_power_tolpos, in_power_tolneg, temp_diff_base, temp_diff_tolpos, temp_diff_tolneg 
            INTO v_ri_progh, v_ri_progf, v_ri_opcur, v_ri_opcur_pos, v_ri_opcur_neg, v_ri_oppow, v_ri_oppow_pos, v_ri_oppow_neg, v_ri_tempdiff, v_ri_tempdiff_pos, v_ri_tempdiff_neg 
            FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            
            UPDATE linestat SET rimodelcode = v_next_model, rivar = v_next_plan, 
                ri_progh = v_ri_progh, ri_progf = v_ri_progf, 
                ri_opcur = v_ri_opcur, ri_opcur_pos = v_ri_opcur_pos, ri_opcur_neg = v_ri_opcur_neg,
                ri_oppow = v_ri_oppow, ri_oppow_pos = v_ri_oppow_pos, ri_oppow_neg = v_ri_oppow_neg,
                ri_tempdiff = v_ri_tempdiff, ri_tempdiff_pos = v_ri_tempdiff_pos, ri_tempdiff_neg = v_ri_tempdiff_neg,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'fi' THEN
            SELECT op_current_base, in_power_base INTO v_fi_opcur, v_fi_oppow FROM modelref WHERE modelcode = v_next_model LIMIT 1;
            UPDATE linestat SET fimodelcode = v_next_model, fivar = v_next_plan, fi_opcur = v_fi_opcur, fi_oppow = v_fi_oppow, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'pack' THEN
            UPDATE linestat SET packmodelcode = v_next_model, packvar = v_next_plan, updtime = CURRENT_TIMESTAMP WHERE id = 1;
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
        ELSEIF p_station = 'wc' THEN
            UPDATE linestat SET wcmodelcode = NULL, wcvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'ri' THEN
            UPDATE linestat SET rimodelcode = NULL, rivar = 0, 
                ri_progh = NULL, ri_progf = NULL, 
                ri_opcur = NULL, ri_opcur_pos = NULL, ri_opcur_neg = NULL,
                ri_oppow = NULL, ri_oppow_pos = NULL, ri_oppow_neg = NULL,
                ri_tempdiff = NULL, ri_tempdiff_pos = NULL, ri_tempdiff_neg = NULL,
                updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'fi' THEN
            UPDATE linestat SET fimodelcode = NULL, fivar = 0, fi_opcur = NULL, fi_oppow = NULL, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        ELSEIF p_station = 'pack' THEN
            UPDATE linestat SET packmodelcode = NULL, packvar = 0, updtime = CURRENT_TIMESTAMP WHERE id = 1;
        END IF;
        
        -- If all stations are empty, set status back to No Work
        UPDATE linestat SET status = 'No Work', active_date = NULL 
        WHERE id = 1 
          AND crsmodelcode IS NULL 
          AND attmodelcode IS NULL 
          AND gmsmodelcode IS NULL 
          AND inmodelcode IS NULL 
          AND outmodelcode IS NULL
          AND wcmodelcode IS NULL
          AND rimodelcode IS NULL
          AND fimodelcode IS NULL
          AND packmodelcode IS NULL;
    END IF;
    
    COMMIT;
END$$

DELIMITER ;
