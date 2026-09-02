from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    # Execute raw SQL to widen the columns
    db.session.execute(db.text("ALTER TABLE crs MODIFY fan1serial VARCHAR(60);"))
    db.session.execute(db.text("ALTER TABLE crs MODIFY fan2serial VARCHAR(60);"))
    db.session.execute(db.text("ALTER TABLE crs MODIFY compserial VARCHAR(60);"))
    db.session.execute(db.text("ALTER TABLE crs MODIFY part1serial VARCHAR(60);"))
    db.session.execute(db.text("ALTER TABLE crs MODIFY part2serial VARCHAR(60);"))
    db.session.execute(db.text("ALTER TABLE crs MODIFY part3serial VARCHAR(60);"))
    db.session.execute(db.text("ALTER TABLE crs MODIFY part4serial VARCHAR(60);"))
    db.session.commit()
    print("Database columns successfully widened to VARCHAR(60)!")
