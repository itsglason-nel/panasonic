from app.models.crs import CRS
record = CRS.query.filter(CRS.serial != '').first()
if record:
    print(f"MODEL={record.modelcode} SERIAL={record.serial}")
else:
    print("NO_RECORD")
