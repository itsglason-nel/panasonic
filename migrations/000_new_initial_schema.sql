-- ================================================================
-- Panasonic Data Logger — Consolidated Initial Schema (v2)
-- MySQL 8.x | InnoDB | utf8mb4_unicode_ci
-- Schema: plcdata
-- ================================================================

CREATE DATABASE IF NOT EXISTS plcdata
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
    
-- DROP DATABASE plcdata;

USE plcdata;


-- ────────────────────────────────────────────
-- 1. Table Definitions (Generated from current App Models)
-- ────────────────────────────────────────────

-- ==========================================
-- ==========================================

CREATE TABLE IF NOT EXISTS `crs` (
    `id`          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `serial`      VARCHAR(14) NOT NULL,
    `compmod`     VARCHAR(14) NOT NULL,
    `compserial`  VARCHAR(30) NOT NULL,
    `fan1mod`     VARCHAR(14) NULL,
    `fan1serial`  VARCHAR(60) NULL, 
    `fan2mod`     VARCHAR(14) NULL,
    `fan2serial`  VARCHAR(60) NULL, 
    `part1mod`    VARCHAR(14) NULL,
    `part1desc`   VARCHAR(30) NULL,
    `part1serial` VARCHAR(60) NULL, 
    `part2mod`    VARCHAR(14) NULL,
    `part2desc`   VARCHAR(30) NULL,
    `part2serial` VARCHAR(60) NULL, 
    `part3mod`    VARCHAR(14) NULL,
    `part3desc`   VARCHAR(30) NULL,
    `part3serial` VARCHAR(60) NULL, 
    `part4mod`    VARCHAR(14) NULL,
    `part4desc`   VARCHAR(30) NULL,
    `part4serial` VARCHAR(60) NULL, 
	`time`        TIMESTAMP NOT NULL,
    `inspector`   VARCHAR(20) NULL,
    `lineno`	  VARCHAR(4) NOT NULL, 
    INDEX idx_crs_serial (serial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE att (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14), 
	serial VARCHAR(14), 
	status1 VARCHAR(12), 
	status2 VARCHAR(12), 
	status3 VARCHAR(12), 
	time TIMESTAMP NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4) NOT NULL, 
	brazzer1 VARCHAR(20), 
	brazzer2 VARCHAR(20), 
	brazzer3 VARCHAR(20), 
	brazzer4 VARCHAR(20), 
	brazzer5 VARCHAR(20), 
	brazzer6 VARCHAR(20), 
	brazzer7 VARCHAR(20), 
	PRIMARY KEY (id)
);





CREATE TABLE crs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
	compmod VARCHAR(14) NOT NULL, 
	compserial VARCHAR(30) NOT NULL, 
	fan1mod VARCHAR(14), 
	fan1serial VARCHAR(60), 
	fan2mod VARCHAR(14), 
	fan2serial VARCHAR(60), 
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
	time TIMESTAMP NOT NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE gms (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
	gascharge DECIMAL(4,2) NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	time TIMESTAMP NOT NULL, 
	inspector VARCHAR(20),
	lineno VARCHAR(4) NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE insp2 (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
    status1 VARCHAR(12) NOT NULL, 
    status2 VARCHAR(12) NOT NULL, 
    status3 VARCHAR(12) NOT NULL, 
    status4 VARCHAR(12) NOT NULL, 
	inspector VARCHAR(20), 
	time TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE insp3_run (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
	insulation_resistance/withstand_voltage VARCHAR(20), 
	prog_check_h VARCHAR(6), 
	prog_check_f VARCHAR(6), 
	airswing VARCHAR(12), 
	comp_operation VARCHAR(12), 
	fan_operation VARCHAR(12), 
	evap_tubes_cool VARCHAR(12), 
	evap_tubes_heat VARCHAR(12), 
	cond_tubes_cool VARCHAR(12), 
	cond_tubes_heat VARCHAR(12), 
	operating_current DECIMAL(8,2), 
	input_power DECIMAL(8,2),
	temp_diff DECIMAL(8,2), 
    leak_status VARCHAR(12),
    leak_location VARCHAR(60),   
	inspector VARCHAR(20), 
	time TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);



CREATE TABLE insp4 (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL,  
	insulation_resistance/withstand_voltage VARCHAR(12), 
	operating_current/input_power VARCHAR(12), 
	nameplate_match VARCHAR(12), 
	model_label VARCHAR(12),
    correct_manual  VARCHAR(12),
	has_remote VARCHAR(12), 
	has_warranty VARCHAR(12), 
	has_screws VARCHAR(12), 
	grille_eel VARCHAR(12), 
	grille_model VARCHAR(12), 
	grille_logo VARCHAR(12), 
	inspector VARCHAR(20), 
	time TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE `lines` (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	lineno VARCHAR(4) NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (lineno)
);

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
	inuniqe VARCHAR(4),
	inpart1mod VARCHAR(14), inpart1desc VARCHAR(30),
	inpart2mod VARCHAR(14), inpart2desc VARCHAR(30),
	inpart3mod VARCHAR(14), inpart3desc VARCHAR(30),
	inpart4mod VARCHAR(14), inpart4desc VARCHAR(30),
	inpart5mod VARCHAR(14), inpart5desc VARCHAR(30),
	inpart6mod VARCHAR(14), inpart6desc VARCHAR(30),

    -- SPAMSO
	outmodelcode VARCHAR(14),
	outvar INTEGER,
    outmodel VARCHAR(14), -- newly added
	outpart1mod VARCHAR(14), outpart1desc VARCHAR(30),
	outpart2mod VARCHAR(14), outpart2desc VARCHAR(30),
	outpart3mod VARCHAR(14), outpart3desc VARCHAR(30),

    -- WIRING & CONSTRUCTION
    wcmodelcode VARCHAR(14), 
    wcvar INTEGER,

    -- RUNNING INSPECTION
    rimodelcode VARCHAR(14),
    rivar INTEGER,
    ri_progh VARCHAR(6),
    ri_progf VARCHAR(6),
    ri_opcur DECIMAL (8,2),
    ri_opcur_pos DECIMAL (2,0),
    ri_opcur_neg DECIMAL (2,0),
    ri_oppow DECIMAL (8,2),
    ri_oppow_pos DECIMAL (2,0),
    ri_oppow_neg DECIMAL (2,0),
    ri_tempdiff DECIMAL (8,2),
    ri_tempdiff_pos DECIMAL (2,0),
    ri_tempdiff_neg DECIMAL (2,0),

    -- FINAL INSPECTION
    fimodelcode VARCHAR(14),
    fivar INTEGER,
    fi_opcur DECIMAL (5,2),
    fi_oppow DECIMAL (5,2),
    

    -- PACKAGING
    packmodelcode VARCHAR(14),
    packvar INTEGER,

	PRIMARY KEY (id) -- Not on PLC
);

CREATE TABLE modules (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(50) NOT NULL, 
	description VARCHAR(255), 
	is_active BOOL NOT NULL, 
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE partref (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	module VARCHAR(8) NOT NULL, 
	partno VARCHAR(14) NOT NULL, 
	partdesc VARCHAR(60) NOT NULL, 
	`usage` FLOAT NOT NULL, 
	tag VARCHAR(14) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE repair (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14) NOT NULL, 
	serial VARCHAR(14) NOT NULL, 
	station_origin VARCHAR(30), 
	defect_type VARCHAR(60), 
	action_taken VARCHAR(120), 
	status VARCHAR(12) NOT NULL, 
	inspector VARCHAR(20), 
	time TIMESTAMP NOT NULL, 
	remarks TEXT, 
	PRIMARY KEY (id)
);

CREATE TABLE serialref (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	modelcode VARCHAR(14), 
	area VARCHAR(14), 
	serialstart VARCHAR(6), 
	PRIMARY KEY (id)
);

CREATE TABLE gastolref (
	id INTEGER NOT NULL AUTO_INCREMENT,
	modelcode VARCHAR(14) UNIQUE,
	gmstolpos DECIMAL(2,0) DEFAULT 0,
	gmstolneg DECIMAL(2,0) DEFAULT 0,
	PRIMARY KEY (id)
);

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

CREATE TABLE shifts (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(50) NOT NULL, 
	start_time TIME NOT NULL, 
	end_time TIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE tags (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(50) NOT NULL, 
	description VARCHAR(255), 
	is_active BOOL NOT NULL, 
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(50) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(100), 
	`role` ENUM('super_admin','admin','supervisor','operator','inspector') NOT NULL, 
	is_active BOOL NOT NULL, 
	must_change_password BOOL NOT NULL, 
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);

CREATE TABLE worksched (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	lineno VARCHAR(4) NOT NULL, 
	seq SMALLINT NOT NULL, 
	modelcode VARCHAR(14) NOT NULL, 
	plan INTEGER NOT NULL, 
	act INTEGER NOT NULL, 
	takttime INTEGER NOT NULL, 
	date DATE NOT NULL DEFAULT (CURRENT_DATE), 
	finalized BOOL NOT NULL, 
	finalized_at DATETIME, 
	finalized_by VARCHAR(50), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_worksched_line_date_model UNIQUE (lineno, date, modelcode)
);


-- ────────────────────────────────────────────
-- 1b. Performance Indexes (Restored from Original Schema)
-- ────────────────────────────────────────────
CREATE INDEX idx_crs_serial ON crs(serial);
CREATE INDEX idx_att_serial ON att(serial);
CREATE INDEX idx_gms_serial ON gms(serial);

CREATE INDEX idx_spamsi_serial ON SPAMSI(serial);
CREATE INDEX idx_spamso_serial ON SPAMSO(serial);

CREATE INDEX idx_cbpcb_serial ON cb_pcb(serial);
CREATE INDEX idx_cbpcb_time ON cb_pcb(time);

CREATE INDEX idx_insp2_serial ON insp2(serial);
CREATE INDEX idx_insp2_time ON insp2(time);

CREATE INDEX idx_insp3run_serial ON insp3_run(serial);
CREATE INDEX idx_insp3run_time ON insp3_run(time);

CREATE INDEX idx_insp3vib_serial ON insp3_vib(serial);
CREATE INDEX idx_insp3vib_time ON insp3_vib(time);

CREATE INDEX idx_insp4_serial ON insp4(serial);
CREATE INDEX idx_insp4_time ON insp4(time);

CREATE INDEX idx_repair_serial ON repair(serial);
CREATE INDEX idx_repair_time ON repair(time);

CREATE INDEX idx_ws_lineno_date ON worksched(lineno, date);

-- ────────────────────────────────────────────
-- 2. Initial Data (Users, Lines, Modules, Tags)
-- ────────────────────────────────────────────

INSERT IGNORE INTO `users` (`id`, `username`, `password_hash`, `full_name`, `role`, `must_change_password`) VALUES
    (1, 'superadmin', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'Super Administrator', 'super_admin', 1);


INSERT IGNORE INTO `users` (`id`, `username`, `password_hash`, `full_name`, `role`, `must_change_password`) VALUES
    (2, 'dev_glaee', 'scrypt:32768:8:1$BGIEyY4lKmHpdNCF$8afb6db376d8f1197525e44cc281f4bbe3b77fa39625f6bc61b61c1dabcec5a8642ee5bb2917401c28504e39c7e34c2bdc32c2b3873cb5021672eb0d70a92dc0', 'System Administrator', 'admin', 1);


INSERT IGNORE INTO `users` (`username`, `password_hash`, `full_name`, `role`, `must_change_password`) VALUES
    ('sfisline1', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'Line 1 Operator', 'operator', 1),
    ('sfisline2', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'Line 2 Operator', 'operator', 1),
    ('sfisline3', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'Line 3 Operator', 'operator', 1);


INSERT IGNORE INTO `lines` (`lineno`, `name`) VALUES
    ('L1', 'Line 1'),
    ('L2', 'Line 2'),
    ('L3', 'Line 3');


INSERT IGNORE INTO `modules` (`name`, `description`) VALUES
    ('CRS', 'Compressor Registration System'),
    ('GMS', 'Gas Management System'),
    ('SPAMSI', 'Safety Part And Measurement System (Indoor)'),
    ('SPAMSO', 'Safety Part And Measurement System (Outdoor)'),
    ('CB', 'Control Board');


INSERT IGNORE INTO `tags` (`name`, `description`) VALUES
    ('Compressor', 'Compressor Registration System'),
    ('Fan Motor', 'Fan Motor'),
    ('Safety Part', 'Safety Part'),
    ('Gas Charge', 'Gas Charge');


INSERT INTO `worksched` 
    (`lineno`, `seq`, `modelcode`, `plan`, `act`, `takttime`, `date`) 
VALUES 
    ('L1', 1, 'CW-U921JPH', 100, 95, 60, '2026-07-09'),
    ('L1', 2, 'CU-HZ12BWA', 50, 50, 45, '2026-07-09'),
    ('L2', 1, 'CW-N620JPH', 200, 190, 30, '2026-07-09'),
    ('L2', 2, 'CW-N820JPH', 150, 145, 30, '2026-07-09'),
    ('L2', 3, 'CW-N920JPH', 100, 100, 35, '2026-07-09');


INSERT INTO `partref`
    (`modelcode`, `module`, `partno`, `partdesc`, `usage`, `tag`)
VALUES
    ('CW-U921JPH', 'CRS', '9SS064XHA21', 'COMPRESSOR', 1.0, 'Compressor'),
    ('CW-U921JPH', 'GMS', 'Z71R32', 'REFRIGERANT', 0.41, 'Gas Charge'),
    ('CU-HZ12BWA', 'CRS', '9SS080XDD41', 'COMPRESSOR', 1.0, 'Compressor'),
    ('CU-HZ12BWA', 'CRS', 'ACXA98-03370', 'FAN MOTOR', 1.0, 'Fan Motor'),
    ('CU-HZ12BWA', 'GMS', 'Z71R32', 'REFRIGERANT', 0.66, 'Gas Charge');


INSERT INTO `crs` (
    `modelcode`, `serial`, `compmod`, `compserial`, 
    `fan1mod`, `fan1serial`, `fan2mod`, `fan2serial`, 
    `part1mod`, `part1desc`, `part1serial`, 
    `part2mod`, `part2desc`, `part2serial`, 
    `part3mod`, `part3desc`, `part3serial`, `time`
) VALUES 
    ('CW-U921JPH', 'JPH-0001', '9SS064XHA21', 'CMP-JPH-001', 'ACXA98-02590', 'F1-JPH-001', 'ACXA98-02600', 'F2-JPH-001', 'G0C702K00002', 'REACTOR', 'P1-JPH-001', 'ACXA43C07110', 'EXP VALVE COIL', 'P2-JPH-001', 'ACXB05-00010', 'EXP VALVE', 'P3-JPH-001', '2026-07-03 06:15:00'),
    ('CW-U921JPH', 'JPH-0002', '9SS064XHA21', 'CMP-JPH-002', 'ACXA98-02590', 'F1-JPH-002', 'ACXA98-02600', 'F2-JPH-002', 'G0C702K00002', 'REACTOR', 'P1-JPH-002', 'ACXA43C07110', 'EXP VALVE COIL', 'P2-JPH-002', 'ACXB05-00010', 'EXP VALVE', 'P3-JPH-002', '2026-07-03 06:20:00'),
    ('CU-HZ12BWA', 'BWA-0001', '9SS080XDD41', 'CMP-BWA-001', 'ACXA98-03370', 'F1-BWA-001', 'N/A', 'N/A', 'ACXB05-01320', 'EXPANSION VALVE', 'P1-BWA-001', 'ACXA43C07310', 'EXPANSION COIL', 'P2-BWA-001', 'ACXB01-05840', '3 WAY VALVE', 'P3-BWA-001', '2026-07-03 07:05:00'),
    ('CU-HZ12BWA', 'BWA-0002', '9SS080XDD41', 'CMP-BWA-002', 'ACXA98-03370', 'F1-BWA-002', 'N/A', 'N/A', 'ACXB05-01320', 'EXPANSION VALVE', 'P1-BWA-002', 'ACXA43C07310', 'EXPANSION COIL', 'P2-BWA-002', 'ACXB01-05840', '3 WAY VALVE', 'P3-BWA-002', '2026-07-03 07:10:00'),
    ('CU-HZ12BWA', 'BWA-0003', '9SS080XDD41', 'CMP-BWA-003', 'ACXA98-03370', 'F1-BWA-003', 'N/A', 'N/A', 'ACXB05-01320', 'EXPANSION VALVE', 'P1-BWA-003', 'ACXA43C07310', 'EXPANSION COIL', 'P2-BWA-003', 'ACXB01-05840', '3 WAY VALVE', 'P3-BWA-003', '2026-07-03 07:15:00');


INSERT INTO `att` 
    (`modelcode`, `serial`, `status1`, `time`, `lineno`) 
VALUES 
    ('CW-U921JPH', 'JPH-0001', 'GOOD',  '2026-07-03 07:15:00', 'L1'),
    ('CW-U921JPH', 'JPH-0002', 'GOOD',  '2026-07-03 07:20:00', 'L1'),
    ('CU-HZ12BWA', 'BWA-0001', 'NO GOOD',  '2026-07-03 08:05:00', 'L2'),
    ('CU-HZ12BWA', 'BWA-0002', 'GOOD',  '2026-07-03 08:10:00', 'L2'),
    ('CU-HZ12BWA', 'BWA-0003', 'NO GOOD', '2026-07-03 08:15:00', 'L2');


INSERT INTO `gms` 
    (`modelcode`, `serial`, `gascharge`, `status`, `time`, `lineno`) 
VALUES 
    ('CW-U921JPH', 'JPH-0001', 0.41, 'GOOD',  '2026-07-03 08:15:00', 'L1'),
    ('CW-U921JPH', 'JPH-0002', 0.41, 'GOOD',  '2026-07-03 08:20:00', 'L1'),
    ('CU-HZ12BWA', 'BWA-0001', 0.66, 'NO GOOD',  '2026-07-03 09:05:00', 'L2'),
    ('CU-HZ12BWA', 'BWA-0002', 0.66, 'GOOD',  '2026-07-03 09:10:00', 'L2'),
    ('CU-HZ12BWA', 'BWA-0003', 0.66, 'NO GOOD', '2026-07-03 09:15:00', 'L2');

-- Insert the single memory block row for linestat
INSERT IGNORE INTO `linestat` (`id`, `status`) VALUES (1, 'No Work');

CREATE TABLE IF NOT EXISTS system_state (
    `key_name`   VARCHAR(50)  NOT NULL PRIMARY KEY,
    `value`      VARCHAR(255) NOT NULL,
    `updated_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `system_state` (`key_name`, `value`) VALUES (	'last_autoclose_date', '2026-07-28');

-- ────────────────────────────────────────────
-- 3. Views
-- ────────────────────────────────────────────

CREATE OR REPLACE VIEW worksched_today AS
SELECT
    id,
    lineno,
    seq,
    modelcode,
    plan,
    act,
    takttime,
    date
FROM worksched
WHERE date = current_date();


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


-- ────────────────────────────────────────────
-- 4. Stored Procedures & Triggers
-- ────────────────────────────────────────────

DELIMITER $$

-- Stored Procedure: Handle Sequence Shifting
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
    DECLARE v_spamsi_unique_code VARCHAR(4);
    
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

-- Trigger: AFTER INSERT ON crs
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

-- Trigger: AFTER INSERT ON att
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

-- Trigger: AFTER INSERT ON gms (remove worksched.act increment)
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

-- Trigger: AFTER INSERT ON spamsi
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

-- Trigger: AFTER INSERT ON spamso (includes worksched.act increment)
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

DELIMITER ;


-- ────────────────────────────────────────────
-- 5. Configuration & Privileges
-- ────────────────────────────────────────────

CREATE USER IF NOT EXISTS 'panasonic'@'192.168.0.11' IDENTIFIED WITH mysql_native_password BY 'MIndS2026';
ALTER USER 'panasonic'@'192.168.0.11' IDENTIFIED WITH mysql_native_password BY 'MIndS2026';
    
GRANT ALL PRIVILEGES ON plcdata.* TO 'panasonic'@'192.168.0.11';
FLUSH PRIVILEGES;

SET GLOBAL max_allowed_packet = 67108864;   -- 64 MB
SET GLOBAL net_read_timeout = 120;          -- 2 minutes
SET GLOBAL net_write_timeout = 120;         -- 2 minutes


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


-- note: UPDATE linestat SET id = 1 WHERE id = 12; (add this when moving from testing to production)

-- Newly added integration triggers & SP update --
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
