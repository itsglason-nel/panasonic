"""
Print Tag Quality Test — Programmatic verification of TEST-PROD-001
Validates the server-rendered unitData JSON matches expected DB values.
"""
import sys, os, json, re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask_login import login_user
from app import create_app
from app.models.user import User

app = create_app()

with app.app_context():
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['LOGIN_DISABLED'] = True
    with app.test_client() as client:
        # Login by directly logging in the user in a request context
        with client.session_transaction() as sess:
            pass  # init session
        
        # Use a request to login
        @app.route('/test-login')
        def test_login():
            user = User.query.filter_by(username='admin').first()
            if user:
                login_user(user)
                return 'ok'
            return 'fail', 400
        
        client.get('/test-login')
        print('Logged in via test route')

        # Get the print tag page
        resp = client.get('/admin/print-tag/TEST-PROD-001')
        print(f'Status Code: {resp.status_code}')

        if resp.status_code != 200:
            print(f'ERROR: Got status {resp.status_code}')
            print(resp.data.decode('utf-8')[:500])
            sys.exit(1)

        html = resp.data.decode('utf-8')

        # Extract the unit data JSON from the script tag
        match = re.search(r'<script id="unit-data" type="application/json">\s*(.*?)\s*</script>', html, re.DOTALL)
        if not match:
            print('ERROR: Could not find unit-data script tag in rendered HTML')
            sys.exit(1)

        data_str = match.group(1).strip()
        data = json.loads(data_str)

        print()
        print('=' * 60)
        print('  unitData extracted from rendered HTML')
        print('=' * 60)
        for k, v in sorted(data.items()):
            status = 'OK' if v else 'EMPTY'
            print(f'  [{status:5s}] {k}: {repr(v)}')

        print()
        print('=' * 60)
        print('  QUALITY CHECKS — TEST-PROD-001')
        print('=' * 60)
        errs = []
        passes = [0]

        def check(name, condition, detail=''):
            if condition:
                passes[0] += 1
                print(f'  [PASS] {name}{" — " + detail if detail else ""}')
            else:
                errs.append(f'{name}{" — " + detail if detail else ""}')
                print(f'  [FAIL] {name}{" — " + detail if detail else ""}')

        # Basic identity
        check('Serial', data.get('serial') == 'TEST-PROD-001', f'got {data.get("serial")}')
        check('Model code populated', bool(data.get('modelcode')), f'got {data.get("modelcode")}')
        check('Line = L1', data.get('lineno') == 'L1', f'got {data.get("lineno")}')
        check('Shift = DAY', data.get('shift') == 'DAY', f'got {data.get("shift")}')
        check('Production date populated', bool(data.get('production_date')), f'got {data.get("production_date")}')

        # Inspectors
        check('CRS inspector populated', bool(data.get('crs_inspector')), f'got {data.get("crs_inspector")}')
        check('ATT status = GOOD', data.get('att_status') == 'GOOD', f'got {data.get("att_status")}')
        check('ATT inspector populated', bool(data.get('att_inspector')), f'got {data.get("att_inspector")}')
        check('GMS status = GOOD', data.get('gms_status') == 'GOOD', f'got {data.get("gms_status")}')
        check('GMS gascharge is numeric', isinstance(data.get('gms_gascharge'), (int, float)), f'got {repr(data.get("gms_gascharge"))}')
        check('GMS inspector populated', bool(data.get('gms_inspector')), f'got {data.get("gms_inspector")}')
        check('INSP2 status = GOOD', data.get('insp2_status') == 'GOOD', f'got {data.get("insp2_status")}')
        check('INSP2 inspector populated', bool(data.get('insp2_inspector')), f'got {data.get("insp2_inspector")}')

        # INSP3 RUN
        check('INSP3_RUN status = GOOD', data.get('insp3_run_status') == 'GOOD', f'got {data.get("insp3_run_status")}')
        check('INSP3_RUN inspector populated', bool(data.get('insp3_run_inspector')), f'got {data.get("insp3_run_inspector")}')

        # Cooling/Heating — Evap Tubes
        check('Evap Tubes Cooling = GOOD', data.get('insp3_run_evap_cool') == 'GOOD')
        check('Evap Tubes Heating = blank', data.get('insp3_run_evap_heat') in (None, '', 'None'), f'got {repr(data.get("insp3_run_evap_heat"))}')

        # Cooling/Heating — Cond Tubes
        check('Cond Tubes Cooling = GOOD', data.get('insp3_run_cond_cool') == 'GOOD')
        check('Cond Tubes Heating = blank', data.get('insp3_run_cond_heat') in (None, '', 'None'), f'got {repr(data.get("insp3_run_cond_heat"))}')

        # Operating Current — VALUE (not GOOD/NG)
        oc = data.get('insp3_run_operating_current', '')
        check('Operating Current is populated', bool(oc), f'got {repr(oc)}')
        check('Operating Current is a VALUE not GOOD/NG', oc not in ('GOOD', 'NG', None, ''), f'got {repr(oc)}')
        check('Op Current Cooling check = GOOD', data.get('insp3_run_op_cool') == 'GOOD')
        check('Op Current Heating check = blank', data.get('insp3_run_op_heat') in (None, '', 'None'), f'got {repr(data.get("insp3_run_op_heat"))}')

        # Input Power — VALUE (not GOOD/NG)
        ip = data.get('insp3_run_input_power', '')
        check('Input Power is populated', bool(ip), f'got {repr(ip)}')
        check('Input Power is a VALUE not GOOD/NG', ip not in ('GOOD', 'NG', None, ''), f'got {repr(ip)}')
        check('In Power Cooling check = GOOD', data.get('insp3_run_in_cool') == 'GOOD')
        check('In Power Heating check = blank', data.get('insp3_run_in_heat') in (None, '', 'None'), f'got {repr(data.get("insp3_run_in_heat"))}')

        # Text fields
        check('Temp Diff populated', bool(data.get('insp3_run_temp_diff')), f'got {data.get("insp3_run_temp_diff")}')
        check('Program Check H populated', bool(data.get('insp3_run_prog_check_h')), f'got {data.get("insp3_run_prog_check_h")}')
        check('Program Check F populated', bool(data.get('insp3_run_prog_check_f')), f'got {data.get("insp3_run_prog_check_f")}')
        check('Leak Location populated', bool(data.get('insp3_run_leak_location')), f'got {data.get("insp3_run_leak_location")}')

        # INSP3 VIB & INSP4
        check('INSP3_VIB status = GOOD', data.get('insp3_vib_status') == 'GOOD', f'got {data.get("insp3_vib_status")}')
        check('INSP3_VIB inspector populated', bool(data.get('insp3_vib_inspector')), f'got {data.get("insp3_vib_inspector")}')
        check('INSP4 status = GOOD', data.get('insp4_status') == 'GOOD', f'got {data.get("insp4_status")}')
        check('INSP4 inspector populated', bool(data.get('insp4_inspector')), f'got {data.get("insp4_inspector")}')

        # HTML structure checks
        check('HTML contains Brazing table', 'BRAZERS INITIAL' in html)
        check('HTML contains Remarks section', 'REMARKS' in html)
        check('HTML contains line-cell checkboxes', 'line-cell' in html)
        check('HTML contains shift-cell checkboxes', 'shift-cell' in html)
        check('HTML has op_current text input', 'id="op_current"' in html)
        check('HTML has in_power text input', 'id="in_power"' in html)
        check('HTML has temp_read text input', 'id="temp_read"' in html)
        check('HTML has prog-part inputs', 'prog-part' in html)

        print()
        print('=' * 60)
        total = passes[0] + len(errs)
        if errs:
            print(f'  RESULT: {passes[0]}/{total} PASSED, {len(errs)} FAILED')
            print()
            for e in errs:
                print(f'  * FAIL: {e}')
        else:
            print(f'  RESULT: ALL {total} QUALITY CHECKS PASSED!')
        print('=' * 60)
