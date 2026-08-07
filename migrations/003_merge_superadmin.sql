-- ================================================================
-- Panasonic Data Logger — Merge Superadmin into Admin
-- ================================================================

USE plcdata;

-- Change all 'super_admin' roles to 'admin'
UPDATE `users` SET `role` = 'admin' WHERE `role` = 'super_admin';
