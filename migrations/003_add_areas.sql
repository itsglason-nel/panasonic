-- Dynamic Area configuration. Safe to run after modelref exists.
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
SELECT DISTINCT TRIM(`area`)
FROM `modelref`
WHERE `area` IS NOT NULL AND TRIM(`area`) <> '';
