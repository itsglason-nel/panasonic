from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Because these contain DELIMITER $$, standard SQLAlchemy text() execution might fail if we don't parse it.
    # It's easier to use mysql command line if it's available, but since we are using SQLAlchemy, we need to strip DELIMITER and split on $$
    
    def execute_script(filename):
        with open(filename, 'r') as f:
            content = f.read()
        
        # Remove DELIMITER $$ and DELIMITER ;
        content = content.replace('DELIMITER $$', '').replace('DELIMITER ;', '')
        statements = [s.strip() for s in content.split('$$') if s.strip()]
        
        for stmt in statements:
            try:
                db.session.execute(text(stmt))
                db.session.commit()
                print(f"Executed a block in {filename} successfully.")
            except Exception as e:
                print(f"Error executing block in {filename}: {e}")

    execute_script('scratch_sp.sql')
    execute_script('scratch_triggers.sql')
