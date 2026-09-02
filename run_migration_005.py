"""Run migration 005: Decimal upgrade and spamso_outmodel_refs creation."""
from app import create_app, db
from sqlalchemy import text

app = create_app()

STATEMENTS = [
    "ALTER TABLE modelref MODIFY COLUMN gmstolpos DECIMAL(4,2) DEFAULT 0",
    "ALTER TABLE modelref MODIFY COLUMN gmstolneg DECIMAL(4,2) DEFAULT 0",
    "ALTER TABLE linestat MODIFY COLUMN gmstolpos DECIMAL(4,2) DEFAULT 0",
    "ALTER TABLE linestat MODIFY COLUMN gmstolneg DECIMAL(4,2) DEFAULT 0",
    """CREATE TABLE IF NOT EXISTS `spamso_outmodel_refs` (
        `id`          INT AUTO_INCREMENT PRIMARY KEY,
        `modelcode`   VARCHAR(14) NOT NULL,
        `outmodel`    VARCHAR(14) NOT NULL,
        `created_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at`  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY `uq_spamso_outmodel_ref_modelcode` (`modelcode`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
]

with app.app_context():
    for stmt in STATEMENTS:
        try:
            db.session.execute(text(stmt))
            db.session.commit()
            print(f"OK: {stmt[:60]}...")
        except Exception as e:
            db.session.rollback()
            print(f"ERR: {stmt[:60]}... => {e}")

    # Safe column add with check
    try:
        row = db.session.execute(text(
            "SELECT COUNT(*) as cnt FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='linestat' AND COLUMN_NAME='outmodel'"
        )).fetchone()
        if row.cnt == 0:
            db.session.execute(text("ALTER TABLE linestat ADD COLUMN outmodel VARCHAR(14) NULL AFTER outvar"))
            db.session.commit()
            print("OK: Added outmodel column to linestat")
        else:
            print("SKIP: outmodel column already exists in linestat")
    except Exception as e:
        db.session.rollback()
        print(f"ERR adding outmodel column: {e}")

print("Migration 005 complete.")
