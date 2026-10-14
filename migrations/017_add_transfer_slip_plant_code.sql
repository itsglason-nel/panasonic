-- Migration 017: Add plant_code column to transfer_slips table
-- Purpose: Persist the active plant code (snapshot of PLANT_CODE env) at creation time
-- so historical transfer slips permanently retain their original plant code even if .env changes.

ALTER TABLE transfer_slips ADD COLUMN plant_code VARCHAR(10) NOT NULL DEFAULT '34P3' AFTER ref_number;
