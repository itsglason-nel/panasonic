import sys
sys.path.insert(0, '.')
from app import create_app
from app.models.crs import CRS

app = create_app()
with app.app_context():
    crs_record = CRS.query.filter(CRS.serial.isnot(None), CRS.serial != '').first()
    if crs_record:
        print(f"CRS: Model {crs_record.modelcode}, Serial {crs_record.serial}")
    else:
        print("No CRS records with serial")
