-- Migration 018: Add UNIQUE constraint on modelref.serialstart and ensure 3-character zero padding for spamsi_unique
-- Schema: plcdata
-- Target: modelref

-- Normalize any unpadded or duplicate test rows before applying constraint
UPDATE `modelref` SET `serialstart` = '10278', `spamsi_unique` = '002' WHERE `modelcode` = 'CW-U923JPH-H' AND `serialstart` = '10277';
UPDATE `modelref` SET `spamsi_unique` = '0A1' WHERE `modelcode` = 'CW-U923JPH-W';
UPDATE `modelref` SET `spamsi_unique` = '0B2' WHERE `modelcode` = 'CW-XU925JPH';

-- Add unique constraint on serialstart
ALTER TABLE `modelref` ADD UNIQUE KEY `uq_modelref_serialstart` (`serialstart`);
