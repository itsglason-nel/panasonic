-- Migration 019: Add plant_code column to lines table
-- Purpose: Support per-line default plant codes (e.g. L1 = 34P3) for Transfer Slip generation

ALTER TABLE `lines` ADD COLUMN plant_code VARCHAR(10) NOT NULL DEFAULT '34P3' AFTER name;
