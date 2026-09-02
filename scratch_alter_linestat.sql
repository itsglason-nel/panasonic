ALTER TABLE linestat
    ADD COLUMN wcmodelcode VARCHAR(14), 
    ADD COLUMN wcvar INTEGER,

    ADD COLUMN rimodelcode VARCHAR(14),
    ADD COLUMN rivar INTEGER,
    ADD COLUMN ri_progh VARCHAR(6),
    ADD COLUMN ri_progf VARCHAR(6),
    ADD COLUMN ri_opcur DECIMAL (8,2),
    ADD COLUMN ri_opcur_pos DECIMAL (2,0),
    ADD COLUMN ri_opcur_neg DECIMAL (2,0),
    ADD COLUMN ri_oppow DECIMAL (8,2),
    ADD COLUMN ri_oppow_pos DECIMAL (2,0),
    ADD COLUMN ri_oppow_neg DECIMAL (2,0),
    ADD COLUMN ri_tempdiff DECIMAL (8,2),
    ADD COLUMN ri_tempdiff_pos DECIMAL (2,0),
    ADD COLUMN ri_tempdiff_neg DECIMAL (2,0),

    ADD COLUMN fimodelcode VARCHAR(14),
    ADD COLUMN fivar INTEGER,
    ADD COLUMN fi_opcur DECIMAL (5,2),
    ADD COLUMN fi_oppow DECIMAL (5,2),

    ADD COLUMN packmodelcode VARCHAR(14),
    ADD COLUMN packvar INTEGER;
