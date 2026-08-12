-- ================================================================
-- Panasonic Data Logger — Initial Database Schema
-- MySQL 8.x | InnoDB | utf8mb4_unicode_ci
-- Schema: plcdata
-- ================================================================
CREATE DATABASE IF NOT EXISTS plcdata
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
    
-- DROP DATABASE plcdata;

USE plcdata;

-- ────────────────────────────────────────────
-- 0a. Users
-- ────────────────────────────────────────────
-- NOTE: If upgrading an existing DB, run this first:
-- ALTER TABLE users MODIFY role ENUM('super_admin','admin','supervisor','operator','inspector') NOT NULL;

select * from users;

CREATE TABLE IF NOT EXISTS `users` (
    `id`                    INT AUTO_INCREMENT PRIMARY KEY,
    `username`              VARCHAR(50) NOT NULL UNIQUE,
    `password_hash`         VARCHAR(255) NOT NULL,
    `full_name`             VARCHAR(100),
    `role`                  ENUM('super_admin','admin','supervisor','operator','inspector') NOT NULL,
    `is_active`             TINYINT(1) NOT NULL DEFAULT 1,
    `must_change_password`  TINYINT(1) NOT NULL DEFAULT 0,
    `created_at`            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Default super_admin user (password: admin123) — MUST change password on first login
INSERT IGNORE INTO `users` (`id`, `username`, `password_hash`, `full_name`, `role`, `must_change_password`) VALUES
    (1, 'superadmin', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'Super Administrator', 'super_admin', 1);

-- Default admin user (password: admin123) — MUST change password on first login
INSERT IGNORE INTO `users` (`id`, `username`, `password_hash`, `full_name`, `role`, `must_change_password`) VALUES
    (2, 'admin', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'System Administrator', 'admin', 1);

-- Legacy line operator users — MUST change password on first login
INSERT IGNORE INTO `users` (`username`, `password_hash`, `full_name`, `role`, `must_change_password`) VALUES
    ('sfisline1', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'Line 1 Operator', 'operator', 1),
    ('sfisline2', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'Line 2 Operator', 'operator', 1),
    ('sfisline3', 'scrypt:32768:8:1$x9MVMl9dKjqq6zLt$96cfd01ea696093bd60fbd0391eaac98b9d81579d9c3732e94d3a3a7496699bb094394e61eac703e5a3869dd61dbd3f8112273bbb035092cb9360dad44cad1b3', 'Line 3 Operator', 'operator', 1);

-- ────────────────────────────────────────────
-- 0b. Production Lines (managed by super_admin)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `lines` (
    `id`         INT AUTO_INCREMENT PRIMARY KEY,
    `lineno`     VARCHAR(4) NOT NULL UNIQUE,
    `name`       VARCHAR(50) NOT NULL,
    `is_active`  TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `lines` (`lineno`, `name`) VALUES
    ('L1', 'Line 1'),
    ('L2', 'Line 2'),
    ('L3', 'Line 3');

-- ────────────────────────────────────────────
-- 0c. Dynamic Modules (managed by super_admin)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `modules` (
    `id`         INT AUTO_INCREMENT PRIMARY KEY,
    `name`       VARCHAR(50) NOT NULL UNIQUE,
    `description` VARCHAR(255) DEFAULT NULL,
    `is_active`  TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `modules` (`name`, `description`) VALUES
    ('CRS', 'Compressor Registration System'),
    ('GMS', 'Gas Management System'),
    ('SPAMS', 'Safety Part And Measurement System'),
    ('CB', 'Control Board');

-- ────────────────────────────────────────────
-- 0d. Dynamic Tags (managed by super_admin)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `tags` (
    `id`         INT AUTO_INCREMENT PRIMARY KEY,
    `name`       VARCHAR(50) NOT NULL UNIQUE,
    `description` VARCHAR(255) DEFAULT NULL,
    `is_active`  TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `tags` (`name`, `description`) VALUES
    ('Compressor', 'Compressor Registration System'),
    ('Fan1 Motor', 'Fan1 Motor'),
    ('Fan2 Motor', 'Fan2 Motor'),
    ('Safety Part', 'Safety Part'),
    ('Gas Charge', 'Gas Charge');


-- ────────────────────────────────────────────
-- 1. Work schedule
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `worksched` (
    `id`        	INT AUTO_INCREMENT PRIMARY KEY,
    `lineno`		VARCHAR(4) NOT NULL,
    `seq`      		SMALLINT NOT NULL,
    `modelcode` 	VARCHAR(14) NOT NULL,
    `plan`			INT NOT NULL,
    `act`			INT NOT NULL,
    `takttime`		INT NOT NULL,
    `date`          DATE NOT NULL DEFAULT (CURRENT_DATE),
    `finalized`		TINYINT(1) NOT NULL DEFAULT 0, 
    `finalized_at`	DATETIME NULL,
    `finalized_by`	VARCHAR(50) NULL,
    UNIQUE KEY uq_ws_line_seq_date (lineno, seq, date),
    INDEX idx_ws_lineno_date (lineno, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- drop table worksched;
-- select * from worksched;

INSERT INTO `worksched` 
    (`lineno`, `seq`, `modelcode`, `plan`, `act`, `takttime`, `date`) 
VALUES 
    ('L1', 1, 'CW-U921JPH', 100, 95, 60, '2026-07-09'),
    ('L1', 2, 'CU-HZ12BWA', 50, 50, 45, '2026-07-09'),
    ('L2', 1, 'CW-N620JPH', 200, 190, 30, '2026-07-09'),
    ('L2', 2, 'CW-N820JPH', 150, 145, 30, '2026-07-09'),
    ('L2', 3, 'CW-N920JPH', 100, 100, 35, '2026-07-09');

create view worksched_today AS
SELECT
id,
lineno,
seq,
modelcode,
plan,
act,
takttime,
date
from worksched
where date = current_date();

select * from worksched_today;


-- ────────────────────────────────────────────
-- 2. Part Reference (BOM) — formerly `modelref`
-- ────────────────────────────────────────────
-- NOTE: If `modelref` already exists in DB, run: RENAME TABLE `modelref` TO `partref`;
-- Then skip the CREATE TABLE below (it's guarded by IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS `partref` (
    `id`         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`  VARCHAR(14) NOT NULL,
    `module`     VARCHAR(8) NOT NULL,
    `partno`     VARCHAR(14) NOT NULL,
    `partdesc`   VARCHAR(60) NOT NULL,
    `usage`      REAL NOT NULL,
    `tag`        VARCHAR(14) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `partref`
    (`modelcode`, `module`, `partno`, `partdesc`, `usage`, `tag`)
VALUES
    ('CW-U921JPH', 'CRS', '9SS064XHA21', 'COMPRESSOR', 1.0, 'Compressor'),
    ('CW-U921JPH', 'GMS', 'Z71R32', 'REFRIGERANT', 0.41, 'Gas Charge'),
    ('CU-HZ12BWA', 'CRS', '9SS080XDD41', 'COMPRESSOR', 1.0, 'Compressor'),
    ('CU-HZ12BWA', 'CRS', 'ACXA98-03370', 'FAN MOTOR', 1.0, 'Fan Motor'),
    ('CU-HZ12BWA', 'GMS', 'Z71R32', 'REFRIGERANT', 0.66, 'Gas Charge');

-- ────────────────────────────────────────────
-- 2b. Model Reference (Serial Start)
--     Stores the serial number prefix per model/area
--     so inspectors can identify which series a unit belongs to.
--     area values: 'Domestic', 'HongKong', 'Export', 'Taiwan'
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `modelref` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NULL,
    `area`        VARCHAR(14) NULL,
    `serialstart` VARCHAR(6)  NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ────────────────────────────────────────────
-- 3. Compressor registration system
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `crs` (
    `id`          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `serial`      VARCHAR(14) NOT NULL,
    `compmod`     VARCHAR(14) NOT NULL,
    `compserial`  VARCHAR(30) NOT NULL,
    `fan1mod`     VARCHAR(14) NULL,
    `fan1serial`  VARCHAR(30) NULL,
    `fan2mod`     VARCHAR(14) NULL,
    `fan2serial`  VARCHAR(30) NULL,
    `part1mod`    VARCHAR(14) NULL,
    `part1desc`   VARCHAR(30) NULL,
    `part1serial` VARCHAR(30) NULL,
    `part2mod`    VARCHAR(14) NULL,
    `part2desc`   VARCHAR(30) NULL,
    `part2serial` VARCHAR(30) NULL,
    `part3mod`    VARCHAR(14) NULL,
    `part3desc`   VARCHAR(30) NULL,
    `part3serial` VARCHAR(30) NULL,
    `part4mod`    VARCHAR(14) NULL,
    `part4desc`   VARCHAR(30) NULL,
    `part4serial` VARCHAR(30) NULL,
	`time`        TIMESTAMP NOT NULL,
    `inspector`   VARCHAR(20) NULL,
    `lineno`	  VARCHAR(4) NOT NULL, -- newly added
    INDEX idx_crs_serial (serial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

-- ────────────────────────────────────────────
-- 3a. Fix CRS test
-- ────────────────────────────────────────────

alter table crs modify fan1serial varchar(60);
alter table crs modify fan2serial varchar(60);
alter table crs modify part1serial varchar(34);
alter table crs modify part2serial varchar(34);
alter table crs modify part3serial varchar(34);
alter table crs modify part4serial varchar(34);

CREATE TABLE IF NOT EXISTS `crs` (
    `id`          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `serial`      VARCHAR(14) NOT NULL,
    `compmod`     VARCHAR(14) NOT NULL,
    `compserial`  VARCHAR(30) NOT NULL,
    `fan1mod`     VARCHAR(14) NULL,
    `fan1serial`  VARCHAR(60) NULL, -- change
    `fan2mod`     VARCHAR(14) NULL,
    `fan2serial`  VARCHAR(60) NULL, -- change
    `part1mod`    VARCHAR(14) NULL,
    `part1desc`   VARCHAR(30) NULL,
    `part1serial` VARCHAR(34) NULL, -- change
    `part2mod`    VARCHAR(14) NULL,
    `part2desc`   VARCHAR(30) NULL,
    `part2serial` VARCHAR(34) NULL, -- change
    `part3mod`    VARCHAR(14) NULL,
    `part3desc`   VARCHAR(30) NULL,
    `part3serial` VARCHAR(34) NULL, -- change
    `part4mod`    VARCHAR(14) NULL,
    `part4desc`   VARCHAR(30) NULL,
    `part4serial` VARCHAR(34) NULL, -- change
	`time`        TIMESTAMP NOT NULL,
    `inspector`   VARCHAR(20) NULL,
    `lineno`	  VARCHAR(4) NOT NULL, -- newly added
    INDEX idx_crs_serial (serial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────
-- 4. Air tight test
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `att` (
    `id`        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode` VARCHAR(14) NULL,
    `serial`    VARCHAR(14) NULL,
    `status1`    VARCHAR(12) NULL,
    `status2`    VARCHAR(12) NULL,
    `status3`    VARCHAR(12) NULL,
    `time`      TIMESTAMP NULL,
    `inspector`   VARCHAR(20) NULL,
    `lineno`	  VARCHAR(4) NOT NULL,
    `brazzer1`    VARCHAR(20) NULL,
    `brazzer2`    VARCHAR(20) NULL,
    `brazzer3`    VARCHAR(20) NULL,
    `brazzer4`    VARCHAR(20) NULL,
    `brazzer5`    VARCHAR(20) NULL,
    `brazzer6`    VARCHAR(20) NULL,
    `brazzer7`    VARCHAR(20) NULL,
    INDEX idx_att_serial (serial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `att` 
    (`modelcode`, `serial`, `status1`, `time`, `lineno`) 
VALUES 
    ('CW-U921JPH', 'JPH-0001', 'GOOD',  '2026-07-03 07:15:00', 'L1'),
    ('CW-U921JPH', 'JPH-0002', 'GOOD',  '2026-07-03 07:20:00', 'L1'),
    ('CU-HZ12BWA', 'BWA-0001', 'NO GOOD',  '2026-07-03 08:05:00', 'L2'),
    ('CU-HZ12BWA', 'BWA-0002', 'GOOD',  '2026-07-03 08:10:00', 'L2'),
    ('CU-HZ12BWA', 'BWA-0003', 'NO GOOD', '2026-07-03 08:15:00', 'L2');
    
-- ────────────────────────────────────────────
-- 5. Gas management system
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `gms` (
    `id`        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode` VARCHAR(14) NOT NULL,
    `serial`    VARCHAR(14) NOT NULL,
    `gascharge` REAL NOT NULL,
    `status`    VARCHAR(12) NOT NULL,
    `time`      TIMESTAMP NOT NULL,
    `inspector`   VARCHAR(20) NULL,
    `lineno`	  VARCHAR(4) NOT NULL, -- newly added   
    INDEX idx_gms_serial (serial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `gms` 
    (`modelcode`, `serial`, `gascharge`, `status`, `time`) 
VALUES 
    ('CW-U921JPH', 'JPH-0001', 0.41, 'GOOD',  '2026-07-03 08:15:00'),
    ('CW-U921JPH', 'JPH-0002', 0.41, 'GOOD',  '2026-07-03 08:20:00'),
    ('CU-HZ12BWA', 'BWA-0001', 0.66, 'NO GOOD',  '2026-07-03 09:05:00'),
    ('CU-HZ12BWA', 'BWA-0002', 0.66, 'GOOD',  '2026-07-03 09:10:00'),
    ('CU-HZ12BWA', 'BWA-0003', 0.66, 'NO GOOD', '2026-07-03 09:15:00');

CREATE TABLE IF NOT EXISTS system_state (
               `key_name`   VARCHAR(50)  NOT NULL PRIMARY KEY,
               `value`      VARCHAR(255) NOT NULL,
               `updated_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
				ON UPDATE CURRENT_TIMESTAMP
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `system_state` (`key_name`, `value`) VALUES (	'last_autoclose_date', '2026-07-28');

-- ────────────────────────────────────────────
-- 9. Audit Logs
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `table_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `record_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `details` text COLLATE utf8mb4_unicode_ci,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────
-- 0. PLC View
-- ────────────────────────────────────────────

-- ────────────────────────────────────────────
-- 0. Worksched Today 
-- ────────────────────────────────────────────

create view worksched_today AS
SELECT
id,
lineno,
seq,
modelcode,
plan,
act,
takttime,
date
from worksched
where date = current_date();

select * from worksched_today;

-- ────────────────────────────────────────────
-- Part Reference Sort View (formerly modelref_sort)
-- ────────────────────────────────────────────

-- DROP VIEW IF EXISTS `partref_sort`;
--    select * from partref_sort where modelcode = 'CW-U921JPH';
    CREATE VIEW `partref_sort` AS
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
        WHEN `module` = 'CRS'   THEN 1
        WHEN `module` = 'gms'   THEN 2
        WHEN `module` = 'spams' THEN 3
        WHEN `module` = 'cb'    THEN 4
        ELSE 5
    END ASC,
    `id` ASC;


-- ────────────────────────────────────────────
-- 0. Configuration
-- ────────────────────────────────────────────
alter USER 'panasonic'@'192.168.0.11'
    IDENTIFIED WITH mysql_native_password
    BY 'MIndS2026';
    
FLUSH PRIVILEGES;  

-- Grant full access to the plcdata database only
GRANT ALL PRIVILEGES ON plcdata.* TO 'panasonic'@'192.168.0.11';

-- Apply changes
FLUSH PRIVILEGES;

SHOW VARIABLES LIKE '%timeout%';

SET GLOBAL max_allowed_packet = 67108864;   -- 64 MB
SET GLOBAL net_read_timeout = 120;          -- 2 minutes
SET GLOBAL net_write_timeout = 120;         -- 2 minutes

SET GLOBAL general_log = 'ON';
SET GLOBAL general_log = 'OFF';

SHOW VARIABLES LIKE 'general_log_file';

SHOW GLOBAL STATUS LIKE 'Aborted_clients';