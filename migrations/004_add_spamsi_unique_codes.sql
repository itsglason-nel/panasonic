-- Per-model SPAMSI code reference for the existing linestat.inuniqe field.
CREATE TABLE IF NOT EXISTS `spamsi_unique_refs` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `modelcode`   VARCHAR(14) NOT NULL,
    `unique_code` VARCHAR(4) NOT NULL,
    `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_spamsi_unique_ref_modelcode` (`modelcode`),
    UNIQUE KEY `uq_spamsi_unique_ref_code` (`unique_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
