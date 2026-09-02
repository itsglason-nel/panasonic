from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with open('scratch_alter_linestat.sql', 'r') as f:
        sql = f.read()
    
    try:
        db.session.execute(text(sql))
        db.session.commit()
        print("Successfully updated linestat table.")
    except Exception as e:
        print(f"Error updating linestat: {e}")
