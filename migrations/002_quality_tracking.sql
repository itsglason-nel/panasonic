-- ================================================================
-- Panasonic Data Logger — Quality Tracking Schema Extension
-- MySQL 8.x | InnoDB | utf8mb4_unicode_ci
-- Schema: plcdata
-- ================================================================

USE plcdata;

-- ────────────────────────────────────────────
-- 1. Modify ATT — add test detail columns
-- ────────────────────────────────────────────
ALTER TABLE `att`
  ADD COLUMN `test_no_clogged` ENUM('GOOD','NG') NULL AFTER `inspector`,
  ADD COLUMN `test_no_leak`    ENUM('GOOD','NG') NULL AFTER `test_no_clogged`,
  ADD COLUMN `test_exp_valve`  ENUM('GOOD','NG') NULL AFTER `test_no_leak`,
  ADD COLUMN `remarks`         TEXT NULL AFTER `test_exp_valve`;

-- ────────────────────────────────────────────
-- 2. Modify GMS — add remarks
-- ────────────────────────────────────────────
ALTER TABLE `gms`
  ADD COLUMN `remarks` TEXT NULL AFTER `inspector`;

-- ────────────────────────────────────────────
-- 3. Safety Parts Monitoring System (SPAMS)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `spams` (
    `id`        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode` VARCHAR(14) NOT NULL,
    `serial`    VARCHAR(14) NOT NULL,
    `status`    VARCHAR(12) NOT NULL,
    `inspector` VARCHAR(20) NULL,
    `time`      TIMESTAMP NOT NULL,
    `remarks`   TEXT NULL,
    INDEX idx_spams_serial (serial),
    INDEX idx_spams_time (time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────
-- 4. Control Board & Power Control Board (CB/PCB)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `cb_pcb` (
    `id`        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode` VARCHAR(14) NOT NULL,
    `serial`    VARCHAR(14) NOT NULL,
    `status`    VARCHAR(12) NOT NULL,
    `inspector` VARCHAR(20) NULL,
    `time`      TIMESTAMP NOT NULL,
    `remarks`   TEXT NULL,
    INDEX idx_cbpcb_serial (serial),
    INDEX idx_cbpcb_time (time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────
-- 5. Inner Line & Construction (INSP2)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `insp2` (
    `id`                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`         VARCHAR(14) NOT NULL,
    `serial`            VARCHAR(14) NOT NULL,
    `status`            VARCHAR(12) NOT NULL,
    `inspector`         VARCHAR(20) NULL,
    `time`              TIMESTAMP NOT NULL,
    `test_wiring_seq`   ENUM('GOOD','NG') NULL COMMENT 'Correct sequence of wirings',
    `test_no_touching`  ENUM('GOOD','NG') NULL COMMENT 'No touching materials (tubes, rings, spm)',
    `test_no_misaligned` ENUM('GOOD','NG') NULL COMMENT 'No misaligned tubes',
    `test_no_lacking`   ENUM('GOOD','NG') NULL COMMENT 'No lacking parts',
    `remarks`           TEXT NULL,
    INDEX idx_insp2_serial (serial),
    INDEX idx_insp2_time (time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────
-- 6. Running Inspection (INSP3 — Running)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `insp3_run` (
    `id`                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`             VARCHAR(14) NOT NULL,
    `serial`                VARCHAR(14) NOT NULL,
    `status`                VARCHAR(12) NOT NULL,
    `inspector`             VARCHAR(20) NULL,
    `time`                  TIMESTAMP NOT NULL,
    `insulation_resistance` VARCHAR(20) NULL COMMENT 'Insulation Resistance reading',
    `withstand_voltage`     VARCHAR(20) NULL COMMENT 'Withstand Voltage reading',
    `leak_status`           ENUM('NO LEAK','LEAK') NULL,
    `leak_location`         VARCHAR(60) NULL COMMENT 'Location if leak found',
    `prog_check_h`          VARCHAR(20) NULL COMMENT 'Program Check H value',
    `prog_check_f`          VARCHAR(20) NULL COMMENT 'Program Check F value',
    `airswing`              ENUM('GOOD','NG') NULL COMMENT 'Airswing working & not noisy',
    `comp_operation`        ENUM('GOOD','NG') NULL COMMENT 'No noisy/abnormal compressor op',
    `fan_operation`         ENUM('GOOD','NG') NULL COMMENT 'No noisy/abnormal fan motor op',
    `evap_tubes_cool`       ENUM('GOOD','NG') NULL,
    `evap_tubes_heat`       ENUM('GOOD','NG') NULL,
    `cond_tubes_cool`       ENUM('GOOD','NG') NULL,
    `cond_tubes_heat`       ENUM('GOOD','NG') NULL,
    `op_current_cool`       ENUM('GOOD','NG') NULL,
    `op_current_heat`       ENUM('GOOD','NG') NULL,
    `in_power_cool`         ENUM('GOOD','NG') NULL,
    `in_power_heat`         ENUM('GOOD','NG') NULL,
    `operating_current`     VARCHAR(20) NULL COMMENT 'Current reading',
    `input_power`           VARCHAR(20) NULL COMMENT 'Wattage reading',
    `temp_diff`             VARCHAR(20) NULL COMMENT 'Temp reading',
    `remarks`               TEXT NULL,
    INDEX idx_insp3run_serial (serial),
    INDEX idx_insp3run_time (time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────
-- 7. Vibration Test (INSP3 — Vibration)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `insp3_vib` (
    `id`        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode` VARCHAR(14) NOT NULL,
    `serial`    VARCHAR(14) NOT NULL,
    `status`    VARCHAR(12) NOT NULL,
    `inspector` VARCHAR(20) NULL,
    `time`      TIMESTAMP NOT NULL,
    `remarks`   TEXT NULL,
    INDEX idx_insp3vib_serial (serial),
    INDEX idx_insp3vib_time (time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────
-- 8. Final Inspection (INSP4)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `insp4` (
    `id`                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`             VARCHAR(14) NOT NULL,
    `serial`                VARCHAR(14) NOT NULL,
    `status`                VARCHAR(12) NOT NULL,
    `inspector`             VARCHAR(20) NULL,
    `time`                  TIMESTAMP NOT NULL,
    `insulation_resistance` VARCHAR(20) NULL COMMENT 'Insulation Resistance / Withstand Voltage',
    `operating_current`     VARCHAR(20) NULL COMMENT 'Operating Current / Input Power',
    `nameplate_match`       ENUM('GOOD','NG') NULL COMMENT 'Nameplate & barcode same model/serial',
    `model_label`           ENUM('GOOD','NG') NULL COMMENT 'Correct model label & badge',
    `manual_remote`         ENUM('GOOD','NG') NULL COMMENT 'Remote and battery complete',
    `manual_warranty`       ENUM('GOOD','NG') NULL COMMENT 'Operation instruction & warranty card',
    `manual_screws`         ENUM('GOOD','NG') NULL COMMENT 'Screw bag & drain pan complete',
    `grille_eel`            ENUM('GOOD','NG') NULL COMMENT 'EEL label present',
    `grille_model`          ENUM('GOOD','NG') NULL COMMENT 'Correct model on grille',
    `grille_logo`           ENUM('GOOD','NG') NULL COMMENT 'Flammable logo present',
    `remarks`               TEXT NULL,
    INDEX idx_insp4_serial (serial),
    INDEX idx_insp4_time (time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────
-- 9. Repair Station
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `repair` (
    `id`             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `modelcode`      VARCHAR(14) NOT NULL,
    `serial`         VARCHAR(14) NOT NULL,
    `station_origin` VARCHAR(30) NULL COMMENT 'Which station sent this unit for repair',
    `defect_type`    VARCHAR(60) NULL COMMENT 'Type of defect found',
    `action_taken`   VARCHAR(120) NULL COMMENT 'What was done to fix it',
    `status`         VARCHAR(12) NOT NULL COMMENT 'REPAIRED / SCRAPPED / PENDING',
    `inspector`      VARCHAR(20) NULL,
    `time`           TIMESTAMP NOT NULL,
    `remarks`        TEXT NULL,
    INDEX idx_repair_serial (serial),
    INDEX idx_repair_time (time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
