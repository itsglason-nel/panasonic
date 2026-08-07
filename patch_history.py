import re

with open('app/routes/admin.py', 'r') as f:
    code = f.read()

# 1. Add _check_ng_history above _get_paginated_data
helper_func = '''
def _check_ng_history(records):
    if not records:
        return {}
    serials = list(set([r.serial for r in records if getattr(r, 'serial', None)]))
    if not serials:
        return {}
    repaired = db.session.query(Repair.serial).filter(Repair.serial.in_(serials)).all()
    ng_serials = {r[0] for r in repaired}
    return {s: (s in ng_serials) for s in serials}

def _get_paginated_data'''
code = code.replace('def _get_paginated_data', helper_func, 1)

# 2. Patch GMS and ATT
code = re.sub(r'(records = query.order_by\([A-Z]+\.time\.desc\(\)\)\.offset[^\n]+)', r'\1\n    ng = _check_ng_history(records)', code)

# 3. Patch SPAMS, CBPCB, INSP2, INSP3Run, INSP3Vib, INSP4
code = re.sub(r'(total, records = _get_paginated_data\([^)]+\))', r'\1\n    ng = _check_ng_history(records)', code)

# 4. Patch remarks in JSON responses
code = re.sub(r'\'remarks\': r\.remarks or \'\'', r'\'remarks\': (r.remarks or \'\') + (\' [Past NG History]\' if ng.get(r.serial) else \'\')', code)

with open('app/routes/admin.py', 'w') as f:
    f.write(code)
