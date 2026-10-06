-- ================================================================
-- Panasonic Data Logger — Initial Schema 
-- MySQL 8.x | InnoDB | utf8mb4_unicode_ci
-- Schema: plcdata
-- ================================================================

CREATE DATABASE IF NOT EXISTS plcdata
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
    
-- DROP DATABASE plcdata;

USE plcdata;

-- ────────────────────────────────────────────
-- Table Definitions 
-- ────────────────────────────────────────────

CREATE TABLE linestat (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, 
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

    -- General
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
	gascharge DECIMAL(4, 2) DEFAULT 0.00, 
	gmstolpos DECIMAL(4, 2) DEFAULT 0, 
	gmstolneg DECIMAL(4, 2) DEFAULT 0,

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
    wcimodelcode VARCHAR(14),            
    wcivar INTEGER,                     

    -- RIT
    ritmodelcode VARCHAR(14),       
    ritvar INTEGER,                 
    ritprogh VARCHAR(6),          
    ritprogf VARCHAR(6),       
    ritdata1 DECIMAL(4, 2),         
    ritdata1tolpos DECIMAL(4, 2),   
    ritdata1tolneg DECIMAL(4, 2),   
    ritdata2 DECIMAL(4, 2),         
    ritdata2tolpos DECIMAL(4, 2),   
    ritdata2tolneg DECIMAL(4, 2),   
    ritdata3 DECIMAL(4, 2),         
    ritdata3tolpos DECIMAL(4, 2),   
    ritdata3tolneg DECIMAL(4, 2),   
    ritheat1 VARCHAR(2),            
    ritheat2 VARCHAR(2),            

    -- FIT
    fitmodelcode VARCHAR(14),            
    fitvar INTEGER,                     
    fitdata1 DECIMAL(4, 2),         
    fitdata1tolpos DECIMAL(4, 2),   
    fitdata1tolneg DECIMAL(4, 2),   
    fitdata2 DECIMAL(4, 2),         
    fitdata2tolpos DECIMAL(4, 2),   
    fitdata2tolneg DECIMAL(4, 2),   

    -- PIT
    pitmodelcode VARCHAR(14),       
    pitvar INTEGER,                  
    pittws VARCHAR(2)
);

INSERT INTO `linestat` (
    -- General / Line State
    `lineno`, `active_date`, `status`,
    
    -- CRS (Compressor Room Station)
    `crsmodelcode`, `compmod`, `fan1mod`, `fan2mod`, 
    `crspart1mod`, `crspart1desc`, `crspart2mod`, `crspart2desc`, 
    `crspart3mod`, `crspart3desc`, `crspart4mod`, `crspart4desc`,
    `area`, `serialstart`, `crsvar`, `reserve1`,
    
    -- ATT (Assembly Tracking)
    `attmodelcode`, `attvar`,
    
    -- GMS (Gas Measurement Station)
    `gmsmodelcode`, `gmsvar`, `gascharge`, `gmstolpos`, `gmstolneg`,
    
    -- SPAMSI (Sub-Part Assembly In)
    `inmodelcode`, `invar`, `inunique`, 
    `inpart1mod`, `inpart1desc`, `inpart2mod`, `inpart2desc`, 
    `inpart3mod`, `inpart3desc`, `inpart4mod`, `inpart4desc`, 
    `inpart5mod`, `inpart5desc`, `inpart6mod`, `inpart6desc`,
    
    -- SPAMSO (Sub-Part Assembly Out)
    `outmodelcode`, `outvar`, `outmodel`, 
    `outpart1mod`, `outpart1desc`, `outpart2mod`, `outpart2desc`, 
    `outpart3mod`, `outpart3desc`,
    
    -- WCI (Wiring Check Inspection)
    `wcimodelcode`, `wcivar`,
    
    -- RIT (Running Inspection Test)
    `ritmodelcode`, `ritvar`, `ritprogh`, `ritprogf`, 
    `ritdata1`, `ritdata1tolpos`, `ritdata1tolneg`, 
    `ritdata2`, `ritdata2tolpos`, `ritdata2tolneg`, 
    `ritdata3`, `ritdata3tolpos`, `ritdata3tolneg`, 
    `ritheat1`, `ritheat2`,
    
    -- FIT (Final Inspection Test)
    `fitmodelcode`, `fitvar`, 
    `fitdata1`, `fitdata1tolpos`, `fitdata1tolneg`, 
    `fitdata2`, `fitdata2tolpos`, `fitdata2tolneg`,
    
    -- PIT (Packaging Inspection Test)
    `pitmodelcode`, `pitvar`, `pittws`
) VALUES (
    -- General / Line State
    'L1', CURRENT_DATE, 'No Work',
    
    -- CRS
    NULL, NULL, NULL, NULL, 
    NULL, NULL, NULL, NULL, 
    NULL, NULL, NULL, NULL,
    NULL, NULL, 0, NULL,
    
    -- ATT
    NULL, 0,
    
    -- GMS
    NULL, 0, 0.00, 0.00, 0.00,
    
    -- SPAMSI
    NULL, 0, NULL, 
    NULL, NULL, NULL, NULL, 
    NULL, NULL, NULL, NULL, 
    NULL, NULL, NULL, NULL,
    
    -- SPAMSO
    NULL, 0, NULL, 
    NULL, NULL, NULL, NULL, 
    NULL, NULL,
    
    -- WCI
    NULL, 0,
    
    -- RIT
    NULL, 0, NULL, NULL, 
    NULL, NULL, NULL, 
    NULL, NULL, NULL, 
    NULL, NULL, NULL, 
    NULL, NULL,
    
    -- FIT
    NULL, 0, 
    NULL, NULL, NULL, 
    NULL, NULL, NULL,
    
    -- PIT
    NULL, 0, NULL
);


CREATE TABLE IF NOT EXISTS `crs` (
    `id`          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14),
    `serial`      VARCHAR(14),
    `compmod`     VARCHAR(14),
    `compserial`  VARCHAR(30),
    `fan1mod`     VARCHAR(14),
    `fan1serial`  VARCHAR(60),
    `fan2mod`     VARCHAR(14),
    `fan2serial`  VARCHAR(60),
    `part1mod`    VARCHAR(14),
    `part1desc`   VARCHAR(30),
    `part1serial` VARCHAR(34), 
    `part2mod`    VARCHAR(14),
    `part2desc`   VARCHAR(30),
    `part2serial` VARCHAR(34), 
    `part3mod`    VARCHAR(14),
    `part3desc`   VARCHAR(30),
    `part3serial` VARCHAR(34), 
    `part4mod`    VARCHAR(14),
    `part4desc`   VARCHAR(30),
    `part4serial` VARCHAR(34), 
	`time`        TIMESTAMP,
    `inspector`   VARCHAR(20),
    `lineno`	  VARCHAR(4), 
    INDEX idx_crs_serial (serial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE att (
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,  
	modelcode VARCHAR(14), 
	`serial` VARCHAR(14), 
	status1 VARCHAR(12), 
	status2 VARCHAR(12), 
	status3 VARCHAR(12),
	overallstatus VARCHAR(12),
	`time` TIMESTAMP NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4), 
	brazzer1 VARCHAR(20), 
	brazzer2 VARCHAR(20), 
	brazzer3 VARCHAR(20), 
	brazzer4 VARCHAR(20), 
	brazzer5 VARCHAR(20), 
	brazzer6 VARCHAR(20), 
	brazzer7 VARCHAR(20),
	INDEX idx_att_serial (serial)
);


CREATE TABLE gms (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, 
	modelcode VARCHAR(14), 
	`serial` VARCHAR(14), 
	gascharge DECIMAL(4, 2), 
	status VARCHAR(12), 
	`time` TIMESTAMP, 
	inspector VARCHAR(20),
	lineno VARCHAR(4),
	INDEX idx_gms_serial (serial)
);

CREATE TABLE SPAMSI (
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
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

CREATE TABLE SPAMSO (
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
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

CREATE TABLE wci (
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	modelcode VARCHAR(14), 
	`serial` VARCHAR(14), 
    status1 VARCHAR(12), 
    status2 VARCHAR(12), 
    status3 VARCHAR(12), 
    status4 VARCHAR(12),
	status5 VARCHAR(12),
	status6 VARCHAR(12),
	status7 VARCHAR(12),
    overallstatus VARCHAR(12),
	`time` TIMESTAMP,
    inspector VARCHAR(20),
	lineno VARCHAR(4),
	INDEX idx_wci_serial (serial)
); 

CREATE TABLE rit (
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, 
	modelcode VARCHAR(14), 
	`serial` VARCHAR(14), 
	status1 VARCHAR(12), 
	status2 VARCHAR(12),
	status3 VARCHAR(12), 
	status4 VARCHAR(12), 
	status5 VARCHAR(12), 
	status6 VARCHAR(12),
	status7 VARCHAR(12),
	data1 DECIMAL(4, 2),
	status8 VARCHAR(12),
	data2 DECIMAL(4, 2),
	status9 VARCHAR(12),
    data3 DECIMAL(4, 2),
	status10 VARCHAR(12),
    progh VARCHAR(6),
    progf VARCHAR(6),
    overallstatus VARCHAR(12),
    `time` TIMESTAMP,
	inspector VARCHAR(20), 
    lineno VARCHAR(4),
	INDEX idx_rit_serial (serial)
);

-- refactor fit table
CREATE TABLE fit (
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	modelcode VARCHAR(14), 
	`serial` VARCHAR(14),  
	status1 VARCHAR(12),
    status2 VARCHAR(12),
    status3 VARCHAR(12),
	data1 DECIMAL(4, 2),
    data2 DECIMAL(4, 2),
    status4 VARCHAR(12),
    status5 VARCHAR(12),
    status6 VARCHAR(12),
    status7 VARCHAR(12),
    status8 VARCHAR(12),
    status9 VARCHAR(12),
	status10 VARCHAR(12),
    overallstatus VARCHAR(12),
    `time` TIMESTAMP, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4),
	INDEX idx_fit_serial (serial)
);

CREATE TABLE pit(
	id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, 
	modelcode VARCHAR(14), 
	`serial` VARCHAR(14), 
	status1 VARCHAR(12), 
	status2 VARCHAR(12), 
	status3 VARCHAR(12),
	status4 VARCHAR(12),
    overallstatus VARCHAR(12),  
	`time` TIMESTAMP NULL, 
	inspector VARCHAR(20), 
	lineno VARCHAR(4),
	INDEX idx_pit_serial (serial)
);

-- ────────────────────────────────────────────

CREATE TABLE `lines` (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	lineno VARCHAR(4) NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (lineno)
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
	partdesc VARCHAR(30) NOT NULL,  
	`usage` DECIMAL(4,2) NOT NULL, -- Changed from FLOAT to DECIMAL(4,2) with 2 decimal places
	tag VARCHAR(30) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE shifts (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(50) NOT NULL, 
	start_time TIME NOT NULL, 
	end_time TIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

INSERT IGNORE INTO shifts (name, start_time, end_time) VALUES
('Day', '06:00:00', '14:00:00'),
('Night', '22:00:00', '06:00:00');

CREATE TABLE tags (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(50) NOT NULL, 
	description VARCHAR(255), 
	is_active BOOL NOT NULL, 
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

-- Users | Admin = Developer, Operator = Panasonic admin
-- Carlos Joaquin Mojica
CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(50) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(100), 
	`role` ENUM('admin','operator') NOT NULL, 
	is_active BOOL NOT NULL, 
	must_change_password BOOL NOT NULL, 
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);

INSERT IGNORE INTO `users` (`id`, `username`, `password_hash`, `full_name`, `role`, `is_active`, `must_change_password`) VALUES
    (1, 'dev_glaee', 'scrypt:32768:8:1$BGIEyY4lKmHpdNCF$8afb6db376d8f1197525e44cc281f4bbe3b77fa39625f6bc61b61c1dabcec5a8642ee5bb2917401c28504e39c7e34c2bdc32c2b3873cb5021672eb0d70a92dc0', 'System Administrator', 'admin', true, 1),
    (3, 'CJ Mojica', 'scrypt:32768:8:1$xDQqBjiidI6qm8iI$768397462c02c73a4145bb44b7005add3077baf3a2e8e5c59d582cb9f26cb7fd5de3275489316b89c1a152ec5390e63ba8ff481ac5083b116f28ab3915f9ebe9', 'Carlos Joaquin Mojica', 'operator', true, 0);


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

INSERT IGNORE INTO worksched (lineno, seq, modelcode, plan, act, takttime, date, finalized) VALUES
('L1', 1, 'CW-U921JPH', 100, 20, 45, '2026-10-01', 0);

CREATE TABLE IF NOT EXISTS system_state (
    `key_name`   VARCHAR(50)  NOT NULL PRIMARY KEY,		
    `value`      VARCHAR(255) NOT NULL,
    `updated_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `system_state` (`key_name`, `value`) VALUES (	'last_autoclose_date', '2026-07-28');

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
    `gmstolpos`         DECIMAL(4,4) DEFAULT 0,
    `gmstolneg`         DECIMAL(4,4) DEFAULT 0,
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
    `updated_at`        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	`ritheat1`		VARCHAR(2) NULL,
	`ritheat2`		VARCHAR(2) NULL,
	`pittws`		VARCHAR(2) NULL,
    `spamsi_unique`     VARCHAR(4) NULL,
    UNIQUE KEY `uq_modelref_spamsi_unique` (`spamsi_unique`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `areas` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `name`        VARCHAR(50) NOT NULL,
    `description` VARCHAR(255) NULL,
    `is_active`   BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_areas_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE transfer_slips (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ref_number VARCHAR(20) UNIQUE NOT NULL,
    production_date DATE NOT NULL,
    line VARCHAR(10) NOT NULL,
    shift VARCHAR(10) NOT NULL,
    modelcode VARCHAR(20) NOT NULL,
    total_qty INT NOT NULL,
    created_by VARCHAR(50),
    `time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    serials_json TEXT NOT NULL
);

-- ────────────────────────────────────────────
-- Configuration & Privileges
-- ────────────────────────────────────────────

CREATE USER IF NOT EXISTS 'panasonic'@'192.168.0.11' IDENTIFIED WITH mysql_native_password BY 'MIndS2026';
ALTER USER 'panasonic'@'192.168.0.11' IDENTIFIED WITH mysql_native_password BY 'MIndS2026';
    
GRANT ALL PRIVILEGES ON plcdata.* TO 'panasonic'@'192.168.0.11';
FLUSH PRIVILEGES;

SET GLOBAL max_allowed_packet = 67108864;   -- 64 MB
SET GLOBAL net_read_timeout = 120;          -- 2 minutes
SET GLOBAL net_write_timeout = 120;         -- 2 minutes
