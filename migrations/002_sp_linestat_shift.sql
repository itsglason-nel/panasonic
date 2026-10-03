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

    DECLARE v_next_date DATE;

    -- Resolve active date (midnight roll-over safe)
    SELECT id, active_date INTO v_linestat_id, v_active_date FROM linestat WHERE lineno = p_lineno LIMIT 1;
    IF v_active_date IS NULL THEN
        SET v_active_date = CURDATE();
        UPDATE linestat SET active_date = v_active_date WHERE id = v_linestat_id;
    END IF;

    -- Resolve current sequence.
    -- NULL p_current_model signals "initialize from the very first scheduled seq"
    IF p_current_model IS NULL THEN
        SET v_current_seq = -1;
    ELSE
        SELECT seq INTO v_current_seq
        FROM   worksched
        WHERE  lineno      = p_lineno
          AND  date        = v_active_date
          AND  modelcode   = p_current_model
        ORDER  BY seq DESC LIMIT 1;

        IF v_current_seq IS NULL THEN
            LEAVE sp_block;
        END IF;
    END IF;

    -- Next pending sequence globally (strictly chronological)
    SELECT date, seq, modelcode, (plan - act)
    INTO   v_next_date, v_next_seq, v_next_model, v_next_plan
    FROM   worksched
    WHERE  lineno = p_lineno
      AND  (date > v_active_date OR (date = v_active_date AND seq > v_current_seq))
      AND  act    < plan
    ORDER  BY date ASC, seq ASC LIMIT 1;

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
                active_date  = v_next_date,
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
