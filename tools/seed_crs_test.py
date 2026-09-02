from app import create_app
from app.models import db
from app.models.crs import CRS
from datetime import datetime

app = create_app()

with app.app_context():
    # Insert new record
    new_crs = CRS(
        modelcode='CW-U921JPH',
        serial='0000000001',
        compmod='9SS064XHA21',
        compserial='9SS064XHA21~ABCDE00001',
        fan1mod='ACXA98-02590',
        fan1serial='20260402 | ACXA98-02590 | ZWA228S17A | 000522 | 103',
        fan2mod='ACXA98-02600',
        fan2serial='20260410 | ACXA98-02600 | ZWA328S17A | 010522 | 113',
        part1mod='G0C702K00002',
        part1desc='REACTOR',
        part1serial='12/29/2502/04/26G0C702K0000202',
        part2mod='ACXA43C07110',
        part2desc='EXP VALVE COIL',
        part2serial='12/29/2502/04/26ACXB05-0001002',
        part3mod='ACXB05-00010',
        part3desc='EXP VALVE (SOLINOID VALVE)',
        part3serial='12/29/2502/04/26ACXB05-0001002',
        # No part 4 provided in request, leaving blank
        time=datetime.now(),
        inspector='SYSTEM_TEST',
        lineno='L1'
    )

    db.session.add(new_crs)
    db.session.commit()
    print("Successfully inserted test CRS record!")
