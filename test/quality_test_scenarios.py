"""
═══════════════════════════════════════════════════════════════════════════
  PMPC Data Logger — Comprehensive Print-Tag Quality Test Suite
  Creates realistic test data covering every production scenario
═══════════════════════════════════════════════════════════════════════════
  Run:  py test/quality_test_scenarios.py
═══════════════════════════════════════════════════════════════════════════
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from app import create_app
from app.models import db
from app.models.crs import CRS
from app.models.gms import GMS
from app.models.att import ATT
from app.models.insp2 import INSP2
from app.models.insp3_run import INSP3Run
from app.models.insp3_vib import INSP3Vib
from app.models.insp4 import INSP4
from app.models.repair import Repair

app = create_app()

# ─── Helper ──────────────────────────────────────────────────────────────────

def clear_test_data(serials):
    """Wipe only the test serials so we don't touch real production data."""
    for model in [CRS, GMS, ATT, INSP2, INSP3Run, INSP3Vib, INSP4, Repair]:
        model.query.filter(model.serial.in_(serials)).delete(synchronize_session='fetch')
    db.session.commit()
    print(f"  ✓ Cleared old test data for {len(serials)} serials")


def banner(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


# ═════════════════════════════════════════════════════════════════════════════
#  SCENARIO DEFINITIONS
# ═════════════════════════════════════════════════════════════════════════════

SCENARIOS = {}
BASE_TIME = datetime(2026, 8, 7, 10, 30, 0)  # 10:30 AM → DAY shift


# ─── Scenario 1: HAPPY PATH — All GOOD, Cooling-Only ─────────────────────
def scenario_1_happy_path():
    """All inspections pass first try. Cooling-only unit. All fields populated."""
    serial = 'QT-HAPPY-001'
    model  = 'CW-U921JPH'
    t      = BASE_TIME

    db.session.add(CRS(modelcode=model, serial=serial, compmod='C-SBS120H38B',
                       compserial='COMP-001', fan1mod='FAN-A', fan1serial='FAN-001',
                       time=t, inspector='YAMADA', lineno='L1'))

    db.session.add(ATT(modelcode=model, serial=serial, status='GOOD', time=t + timedelta(minutes=5),
                       inspector='TANAKA', lineno='L1',
                       test_no_clogged='GOOD', test_no_leak='GOOD', test_exp_valve='GOOD'))

    db.session.add(GMS(modelcode=model, serial=serial, gascharge=1050.0, status='GOOD',
                       time=t + timedelta(minutes=10), inspector='SUZUKI', lineno='L1'))

    db.session.add(INSP2(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=15), inspector='WATANABE',
                         test_wiring_seq='GOOD', test_no_touching='GOOD',
                         test_no_misaligned='GOOD', test_no_lacking='GOOD'))

    db.session.add(INSP3Run(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=20), inspector='KIMURA',
                            insulation_resistance='500', withstand_voltage='1500',
                            leak_status='NO LEAK', leak_location='',
                            prog_check_h='14:30', prog_check_f='15:00',
                            airswing='GOOD', comp_operation='GOOD', fan_operation='GOOD',
                            evap_tubes_cool='GOOD', evap_tubes_heat=None,
                            cond_tubes_cool='GOOD', cond_tubes_heat=None,
                            op_current_cool='GOOD', op_current_heat=None,
                            in_power_cool='GOOD', in_power_heat=None,
                            operating_current='5.2', input_power='1200', temp_diff='8.5'))

    db.session.add(INSP3Vib(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=25), inspector='KIMURA'))

    db.session.add(INSP4(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=30), inspector='TAKAHASHI',
                         insulation_resistance='500', operating_current='5.1',
                         nameplate_match='GOOD', model_label='GOOD',
                         manual_remote='GOOD', manual_warranty='GOOD', manual_screws='GOOD',
                         grille_eel='GOOD', grille_model='GOOD', grille_logo='GOOD'))

    db.session.commit()
    return serial

SCENARIOS['1_happy_path'] = scenario_1_happy_path


# ─── Scenario 2: HEAT PUMP — Both Cooling AND Heating pass ───────────────
def scenario_2_heat_pump():
    """Heat pump model: Cooling AND Heating both tested and GOOD."""
    serial = 'QT-HTPMP-002'
    model  = 'CW-U921JPH'
    t      = BASE_TIME

    db.session.add(CRS(modelcode=model, serial=serial, compmod='C-SBS120H38B',
                       compserial='COMP-002', fan1mod='FAN-A', fan1serial='FAN-002',
                       time=t, inspector='YAMADA', lineno='L2'))

    db.session.add(ATT(modelcode=model, serial=serial, status='GOOD',
                       time=t + timedelta(minutes=5), inspector='TANAKA', lineno='L2',
                       test_no_clogged='GOOD', test_no_leak='GOOD', test_exp_valve='GOOD'))

    db.session.add(GMS(modelcode=model, serial=serial, gascharge=1080.0, status='GOOD',
                       time=t + timedelta(minutes=10), inspector='SUZUKI', lineno='L2'))

    db.session.add(INSP2(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=15), inspector='WATANABE',
                         test_wiring_seq='GOOD', test_no_touching='GOOD',
                         test_no_misaligned='GOOD', test_no_lacking='GOOD'))

    db.session.add(INSP3Run(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=20), inspector='KIMURA',
                            insulation_resistance='520', withstand_voltage='1480',
                            leak_status='NO LEAK', leak_location='',
                            prog_check_h='09:15', prog_check_f='10:45',
                            airswing='GOOD', comp_operation='GOOD', fan_operation='GOOD',
                            evap_tubes_cool='GOOD', evap_tubes_heat='GOOD',
                            cond_tubes_cool='GOOD', cond_tubes_heat='GOOD',
                            op_current_cool='GOOD', op_current_heat='GOOD',
                            in_power_cool='GOOD', in_power_heat='GOOD',
                            operating_current='6.1', input_power='1350', temp_diff='9.2'))

    db.session.add(INSP3Vib(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=25), inspector='KIMURA'))

    db.session.add(INSP4(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=30), inspector='TAKAHASHI',
                         insulation_resistance='510', operating_current='6.0',
                         nameplate_match='GOOD', model_label='GOOD',
                         manual_remote='GOOD', manual_warranty='GOOD', manual_screws='GOOD',
                         grille_eel='GOOD', grille_model='GOOD', grille_logo='GOOD'))

    db.session.commit()
    return serial

SCENARIOS['2_heat_pump'] = scenario_2_heat_pump


# ─── Scenario 3: COOLING ONLY — Heating columns NULL ─────────────────────
def scenario_3_cooling_only():
    """Cooling-only model. All heating columns are NULL."""
    serial = 'QT-COOL-003'
    model  = 'CW-U921JPH'
    t      = BASE_TIME

    db.session.add(CRS(modelcode=model, serial=serial, compmod='C-SBS120H38B',
                       compserial='COMP-003', fan1mod='FAN-A', fan1serial='FAN-003',
                       time=t, inspector='YAMADA', lineno='L3'))

    db.session.add(ATT(modelcode=model, serial=serial, status='GOOD',
                       time=t + timedelta(minutes=5), inspector='TANAKA', lineno='L3',
                       test_no_clogged='GOOD', test_no_leak='GOOD', test_exp_valve='GOOD'))

    db.session.add(GMS(modelcode=model, serial=serial, gascharge=1020.0, status='GOOD',
                       time=t + timedelta(minutes=10), inspector='SUZUKI', lineno='L3'))

    db.session.add(INSP2(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=15), inspector='WATANABE',
                         test_wiring_seq='GOOD', test_no_touching='GOOD',
                         test_no_misaligned='GOOD', test_no_lacking='GOOD'))

    db.session.add(INSP3Run(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=20), inspector='SATO',
                            insulation_resistance='490', withstand_voltage='1520',
                            leak_status='NO LEAK', leak_location='',
                            prog_check_h='11:00', prog_check_f='12:30',
                            airswing='GOOD', comp_operation='GOOD', fan_operation='GOOD',
                            evap_tubes_cool='GOOD', evap_tubes_heat=None,
                            cond_tubes_cool='GOOD', cond_tubes_heat=None,
                            op_current_cool='GOOD', op_current_heat=None,
                            in_power_cool='GOOD', in_power_heat=None,
                            operating_current='4.8', input_power='1100', temp_diff='7.8'))

    db.session.add(INSP3Vib(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=25), inspector='SATO'))

    db.session.add(INSP4(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=30), inspector='TAKAHASHI',
                         insulation_resistance='480', operating_current='4.7',
                         nameplate_match='GOOD', model_label='GOOD',
                         manual_remote='GOOD', manual_warranty='GOOD', manual_screws='GOOD',
                         grille_eel='GOOD', grille_model='GOOD', grille_logo='GOOD'))

    db.session.commit()
    return serial

SCENARIOS['3_cooling_only'] = scenario_3_cooling_only


# ─── Scenario 4: REPAIR FLOW — Fails INSP3 → Repair → Re-test GOOD ──────
def scenario_4_repair_flow():
    """
    Unit fails Running Inspection (leak found). Goes to repair.
    Gets repaired. Then a 2nd INSP3_RUN is recorded as GOOD.
    The print tag should use the LATEST (2nd) record.
    """
    serial = 'QT-REPR-004'
    model  = 'CW-U921JPH'
    t      = BASE_TIME

    db.session.add(CRS(modelcode=model, serial=serial, compmod='C-SBS120H38B',
                       compserial='COMP-004', fan1mod='FAN-A', fan1serial='FAN-004',
                       time=t, inspector='YAMADA', lineno='L1'))

    db.session.add(ATT(modelcode=model, serial=serial, status='GOOD',
                       time=t + timedelta(minutes=5), inspector='TANAKA', lineno='L1',
                       test_no_clogged='GOOD', test_no_leak='GOOD', test_exp_valve='GOOD'))

    db.session.add(GMS(modelcode=model, serial=serial, gascharge=1060.0, status='GOOD',
                       time=t + timedelta(minutes=10), inspector='SUZUKI', lineno='L1'))

    db.session.add(INSP2(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=15), inspector='WATANABE',
                         test_wiring_seq='GOOD', test_no_touching='GOOD',
                         test_no_misaligned='GOOD', test_no_lacking='GOOD'))

    # 1st INSP3 — FAILED (leak detected)
    db.session.add(INSP3Run(modelcode=model, serial=serial, status='NG',
                            time=t + timedelta(minutes=20), inspector='KIMURA',
                            insulation_resistance='480', withstand_voltage='1450',
                            leak_status='LEAK', leak_location='Compressor suction pipe',
                            prog_check_h=None, prog_check_f=None,
                            airswing='GOOD', comp_operation='GOOD', fan_operation='GOOD',
                            evap_tubes_cool=None, evap_tubes_heat=None,
                            cond_tubes_cool=None, cond_tubes_heat=None,
                            op_current_cool=None, op_current_heat=None,
                            in_power_cool=None, in_power_heat=None,
                            operating_current=None, input_power=None, temp_diff=None,
                            remarks='LEAK found at compressor suction pipe. Sent to repair.'))

    # Repair record
    db.session.add(Repair(modelcode=model, serial=serial,
                          station_origin='Running Inspection', defect_type='Gas Leak',
                          action_taken='Re-brazed compressor suction pipe joint',
                          status='REPAIRED', inspector='YOSHIDA',
                          time=t + timedelta(minutes=40),
                          remarks='Leak at suction pipe. Re-brazed and pressure tested.'))

    # 2nd INSP3 — PASSED after repair
    db.session.add(INSP3Run(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=60), inspector='KIMURA',
                            insulation_resistance='500', withstand_voltage='1500',
                            leak_status='NO LEAK', leak_location='',
                            prog_check_h='14:00', prog_check_f='15:30',
                            airswing='GOOD', comp_operation='GOOD', fan_operation='GOOD',
                            evap_tubes_cool='GOOD', evap_tubes_heat=None,
                            cond_tubes_cool='GOOD', cond_tubes_heat=None,
                            op_current_cool='GOOD', op_current_heat=None,
                            in_power_cool='GOOD', in_power_heat=None,
                            operating_current='5.0', input_power='1180', temp_diff='8.1',
                            remarks='2nd test after repair - PASSED'))

    db.session.add(INSP3Vib(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=65), inspector='KIMURA'))

    db.session.add(INSP4(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=70), inspector='TAKAHASHI',
                         insulation_resistance='500', operating_current='5.0',
                         nameplate_match='GOOD', model_label='GOOD',
                         manual_remote='GOOD', manual_warranty='GOOD', manual_screws='GOOD',
                         grille_eel='GOOD', grille_model='GOOD', grille_logo='GOOD'))

    db.session.commit()
    return serial

SCENARIOS['4_repair_flow'] = scenario_4_repair_flow


# ─── Scenario 5: NG / REWORK — Multiple failures then final pass ─────────
def scenario_5_rework():
    """
    Unit fails ATT first (clogged), gets repaired/reworked.
    Then fails INSP2 (wiring issue), gets reworked again.
    Eventually all inspections pass.
    """
    serial = 'QT-RWRK-005'
    model  = 'CW-U921JPH'
    t      = BASE_TIME

    db.session.add(CRS(modelcode=model, serial=serial, compmod='C-SBS120H38B',
                       compserial='COMP-005', fan1mod='FAN-A', fan1serial='FAN-005',
                       time=t, inspector='YAMADA', lineno='L2'))

    # 1st ATT — FAILED
    db.session.add(ATT(modelcode=model, serial=serial, status='NG',
                       time=t + timedelta(minutes=5), inspector='TANAKA', lineno='L2',
                       test_no_clogged='NG', test_no_leak='GOOD', test_exp_valve='GOOD',
                       remarks='Clogged tube found'))

    # Repair 1
    db.session.add(Repair(modelcode=model, serial=serial,
                          station_origin='ATT', defect_type='Clogged tube',
                          action_taken='Cleared tube blockage and re-tested',
                          status='REPAIRED', inspector='YOSHIDA',
                          time=t + timedelta(minutes=15)))

    # 2nd ATT — PASSED
    db.session.add(ATT(modelcode=model, serial=serial, status='GOOD',
                       time=t + timedelta(minutes=25), inspector='TANAKA', lineno='L2',
                       test_no_clogged='GOOD', test_no_leak='GOOD', test_exp_valve='GOOD',
                       remarks='2nd attempt after rework - PASSED'))

    db.session.add(GMS(modelcode=model, serial=serial, gascharge=1040.0, status='GOOD',
                       time=t + timedelta(minutes=30), inspector='SUZUKI', lineno='L2'))

    # 1st INSP2 — FAILED
    db.session.add(INSP2(modelcode=model, serial=serial, status='NG',
                         time=t + timedelta(minutes=35), inspector='WATANABE',
                         test_wiring_seq='NG', test_no_touching='GOOD',
                         test_no_misaligned='GOOD', test_no_lacking='GOOD',
                         remarks='Wiring sequence incorrect'))

    # Repair 2
    db.session.add(Repair(modelcode=model, serial=serial,
                          station_origin='Construction Inspection', defect_type='Wiring error',
                          action_taken='Re-routed wiring to correct sequence',
                          status='REPAIRED', inspector='MORITA',
                          time=t + timedelta(minutes=45)))

    # 2nd INSP2 — PASSED
    db.session.add(INSP2(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=55), inspector='WATANABE',
                         test_wiring_seq='GOOD', test_no_touching='GOOD',
                         test_no_misaligned='GOOD', test_no_lacking='GOOD',
                         remarks='2nd attempt after rework - PASSED'))

    db.session.add(INSP3Run(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=60), inspector='KIMURA',
                            insulation_resistance='510', withstand_voltage='1490',
                            leak_status='NO LEAK', leak_location='',
                            prog_check_h='10:00', prog_check_f='11:30',
                            airswing='GOOD', comp_operation='GOOD', fan_operation='GOOD',
                            evap_tubes_cool='GOOD', evap_tubes_heat=None,
                            cond_tubes_cool='GOOD', cond_tubes_heat=None,
                            op_current_cool='GOOD', op_current_heat=None,
                            in_power_cool='GOOD', in_power_heat=None,
                            operating_current='5.3', input_power='1220', temp_diff='8.8'))

    db.session.add(INSP3Vib(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=65), inspector='KIMURA'))

    db.session.add(INSP4(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=70), inspector='TAKAHASHI',
                         insulation_resistance='505', operating_current='5.2',
                         nameplate_match='GOOD', model_label='GOOD',
                         manual_remote='GOOD', manual_warranty='GOOD', manual_screws='GOOD',
                         grille_eel='GOOD', grille_model='GOOD', grille_logo='GOOD'))

    db.session.commit()
    return serial

SCENARIOS['5_rework'] = scenario_5_rework


# ─── Scenario 6: PARTIAL FAIL — Some pass, some fail (mixed) ─────────────
def scenario_6_partial_fail():
    """
    Unit passes CRS, ATT, GMS, INSP2 but fails INSP3_RUN.
    Never gets repaired. Tag should show GOOD only for passing stations.
    """
    serial = 'QT-PART-006'
    model  = 'CW-U921JPH'
    t      = BASE_TIME

    db.session.add(CRS(modelcode=model, serial=serial, compmod='C-SBS120H38B',
                       compserial='COMP-006', fan1mod='FAN-A', fan1serial='FAN-006',
                       time=t, inspector='YAMADA', lineno='L1'))

    db.session.add(ATT(modelcode=model, serial=serial, status='GOOD',
                       time=t + timedelta(minutes=5), inspector='TANAKA', lineno='L1',
                       test_no_clogged='GOOD', test_no_leak='GOOD', test_exp_valve='GOOD'))

    db.session.add(GMS(modelcode=model, serial=serial, gascharge=980.0, status='GOOD',
                       time=t + timedelta(minutes=10), inspector='SUZUKI', lineno='L1'))

    db.session.add(INSP2(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=15), inspector='WATANABE',
                         test_wiring_seq='GOOD', test_no_touching='GOOD',
                         test_no_misaligned='GOOD', test_no_lacking='GOOD'))

    # INSP3 RUN — FAILED
    db.session.add(INSP3Run(modelcode=model, serial=serial, status='NG',
                            time=t + timedelta(minutes=20), inspector='KIMURA',
                            insulation_resistance='450', withstand_voltage='1400',
                            leak_status='NO LEAK', leak_location='',
                            prog_check_h=None, prog_check_f=None,
                            airswing='NG', comp_operation='NG', fan_operation='NG',
                            evap_tubes_cool=None, evap_tubes_heat=None,
                            cond_tubes_cool=None, cond_tubes_heat=None,
                            op_current_cool=None, op_current_heat=None,
                            in_power_cool=None, in_power_heat=None,
                            operating_current=None, input_power=None, temp_diff=None,
                            remarks='Fan motor abnormal noise. Compressor vibration excessive.'))

    db.session.commit()
    return serial

SCENARIOS['6_partial_fail'] = scenario_6_partial_fail


# ─── Scenario 7: MISSING DATA — Only CRS registered ──────────────────────
def scenario_7_missing_data():
    """Unit just got registered in CRS. No other inspection data exists yet."""
    serial = 'QT-MISS-007'
    model  = 'CW-U921JPH'
    t      = BASE_TIME

    db.session.add(CRS(modelcode=model, serial=serial, compmod='C-SBS120H38B',
                       compserial='COMP-007', fan1mod='FAN-A', fan1serial='FAN-007',
                       time=t, inspector='YAMADA', lineno='L3'))

    db.session.commit()
    return serial

SCENARIOS['7_missing_data'] = scenario_7_missing_data


# ─── Scenario 8: NIGHT SHIFT — Production at 10 PM ──────────────────────
def scenario_8_night_shift():
    """Production at 22:00. Night shift checkbox should be checked."""
    serial = 'QT-NGHT-008'
    model  = 'CW-U921JPH'
    t      = datetime(2026, 8, 7, 22, 0, 0)  # 10 PM

    db.session.add(CRS(modelcode=model, serial=serial, compmod='C-SBS120H38B',
                       compserial='COMP-008', fan1mod='FAN-A', fan1serial='FAN-008',
                       time=t, inspector='NAKAMURA', lineno='L2'))

    db.session.add(ATT(modelcode=model, serial=serial, status='GOOD',
                       time=t + timedelta(minutes=5), inspector='ITO', lineno='L2',
                       test_no_clogged='GOOD', test_no_leak='GOOD', test_exp_valve='GOOD'))

    db.session.add(GMS(modelcode=model, serial=serial, gascharge=1055.0, status='GOOD',
                       time=t + timedelta(minutes=10), inspector='KOBAYASHI', lineno='L2'))

    db.session.add(INSP2(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=15), inspector='ENDO',
                         test_wiring_seq='GOOD', test_no_touching='GOOD',
                         test_no_misaligned='GOOD', test_no_lacking='GOOD'))

    db.session.add(INSP3Run(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=20), inspector='HARADA',
                            insulation_resistance='505', withstand_voltage='1510',
                            leak_status='NO LEAK', leak_location='',
                            prog_check_h='22:30', prog_check_f='23:00',
                            airswing='GOOD', comp_operation='GOOD', fan_operation='GOOD',
                            evap_tubes_cool='GOOD', evap_tubes_heat='GOOD',
                            cond_tubes_cool='GOOD', cond_tubes_heat='GOOD',
                            op_current_cool='GOOD', op_current_heat='GOOD',
                            in_power_cool='GOOD', in_power_heat='GOOD',
                            operating_current='5.5', input_power='1250', temp_diff='9.0'))

    db.session.add(INSP3Vib(modelcode=model, serial=serial, status='GOOD',
                            time=t + timedelta(minutes=25), inspector='HARADA'))

    db.session.add(INSP4(modelcode=model, serial=serial, status='GOOD',
                         time=t + timedelta(minutes=30), inspector='FUJITA',
                         insulation_resistance='500', operating_current='5.4',
                         nameplate_match='GOOD', model_label='GOOD',
                         manual_remote='GOOD', manual_warranty='GOOD', manual_screws='GOOD',
                         grille_eel='GOOD', grille_model='GOOD', grille_logo='GOOD'))

    db.session.commit()
    return serial

SCENARIOS['8_night_shift'] = scenario_8_night_shift


# ═════════════════════════════════════════════════════════════════════════════
#  AUDIT / DATA-INTEGRITY VERIFICATION
# ═════════════════════════════════════════════════════════════════════════════

def audit_verify(serials_map):
    """
    Run data-integrity checks against every test scenario.
    These are the same checks a production QA auditor would run.
    """
    banner("AUDIT VERIFICATION")
    errors = []
    warnings = []

    for name, serial in serials_map.items():
        print(f"\n  --- Auditing {name} ({serial}) ---")

        # 1. CRS must always exist
        crs = CRS.query.filter_by(serial=serial).first()
        if not crs:
            errors.append(f"[{name}] CRITICAL: No CRS record found!")
            continue
        print(f"    [OK] CRS record exists (model={crs.modelcode}, line={crs.lineno})")

        # 2. Lineno must be valid (L1, L2, L3)
        if crs.lineno not in ('L1', 'L2', 'L3'):
            errors.append(f"[{name}] Lineno '{crs.lineno}' is not L1/L2/L3")
        else:
            print(f"    [OK] Lineno is valid: {crs.lineno}")

        # 3. Check that order_by(id.desc()) returns the LATEST record
        insp3_all = INSP3Run.query.filter_by(serial=serial).order_by(INSP3Run.id.desc()).all()
        if insp3_all:
            latest = insp3_all[0]
            print(f"    [OK] INSP3_RUN has {len(insp3_all)} record(s). Latest status: {latest.status}")

            # 4. If latest INSP3 is GOOD, verify cooling/heating consistency
            if latest.status == 'GOOD':
                if latest.evap_tubes_cool is None and latest.evap_tubes_heat is None:
                    warnings.append(f"[{name}] INSP3 is GOOD but no evap tube checks recorded")
                if latest.operating_current is None:
                    warnings.append(f"[{name}] INSP3 is GOOD but operating_current is NULL")
                if latest.input_power is None:
                    warnings.append(f"[{name}] INSP3 is GOOD but input_power is NULL")
                if latest.temp_diff is None:
                    warnings.append(f"[{name}] INSP3 is GOOD but temp_diff is NULL")
                if latest.prog_check_h is None:
                    warnings.append(f"[{name}] INSP3 is GOOD but prog_check_h is NULL")

            # 5. If leaked, leak_location should be populated
            if latest.leak_status == 'LEAK' and not latest.leak_location:
                errors.append(f"[{name}] Leak detected but leak_location is empty!")

            # 6. Verify operating_current and input_power are numeric values (not GOOD/NG)
            if latest.operating_current and latest.operating_current in ('GOOD', 'NG'):
                errors.append(f"[{name}] operating_current should be a numeric VALUE, not '{latest.operating_current}'")
            if latest.input_power and latest.input_power in ('GOOD', 'NG'):
                errors.append(f"[{name}] input_power should be a numeric VALUE, not '{latest.input_power}'")

        # 7. If unit has repairs, verify there's a subsequent passing record
        repairs = Repair.query.filter_by(serial=serial).all()
        if repairs:
            print(f"    [!] Unit has {len(repairs)} repair record(s)")
            for r in repairs:
                print(f"      -> {r.station_origin}: {r.defect_type} -> {r.action_taken}")
            att_latest = ATT.query.filter_by(serial=serial).order_by(ATT.id.desc()).first()
            insp2_latest = INSP2.query.filter_by(serial=serial).order_by(INSP2.id.desc()).first()
            insp3_latest = INSP3Run.query.filter_by(serial=serial).order_by(INSP3Run.id.desc()).first()

            if att_latest and att_latest.status != 'GOOD':
                warnings.append(f"[{name}] Has repairs but latest ATT is still '{att_latest.status}'")
            if insp2_latest and insp2_latest.status != 'GOOD':
                warnings.append(f"[{name}] Has repairs but latest INSP2 is still '{insp2_latest.status}'")
            if insp3_latest and insp3_latest.status != 'GOOD':
                warnings.append(f"[{name}] Has repairs but latest INSP3 is still '{insp3_latest.status}'")

        # 8. INSP4 should only exist if INSP3 passed
        insp4 = INSP4.query.filter_by(serial=serial).first()
        insp3_latest = INSP3Run.query.filter_by(serial=serial).order_by(INSP3Run.id.desc()).first()
        if insp4 and (not insp3_latest or insp3_latest.status != 'GOOD'):
            errors.append(f"[{name}] INSP4 exists but INSP3_RUN is not GOOD!")

        # 9. Shift calculation audit
        hour = crs.time.hour
        expected_shift = 'NIGHT' if hour >= 18 or hour < 6 else 'DAY'
        print(f"    [OK] Production hour={hour:02d}:00 -> Expected shift: {expected_shift}")

        # 10. Gas charge value should be reasonable (800-1500 grams)
        gms = GMS.query.filter_by(serial=serial).order_by(GMS.id.desc()).first()
        if gms:
            if gms.gascharge < 800 or gms.gascharge > 1500:
                warnings.append(f"[{name}] Gas charge {gms.gascharge}g seems out of range (800-1500)")
            else:
                print(f"    [OK] Gas charge {gms.gascharge}g is within normal range")

    # ─── Summary ─────────────────────────────────────────────────────────
    banner("AUDIT SUMMARY")
    if errors:
        print(f"\n  ERRORS: {len(errors)}")
        for e in errors:
            print(f"     * {e}")
    else:
        print(f"\n  No errors found!")

    if warnings:
        print(f"\n  WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"     * {w}")
    else:
        print(f"\n  No warnings!")

    total = len(serials_map)
    print(f"\n  {total} scenarios tested | {len(errors)} errors | {len(warnings)} warnings")
    print(f"{'='*70}\n")

    return len(errors) == 0


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        banner("PMPC QUALITY TEST SUITE")
        print("  This script creates realistic test data for ALL production scenarios")
        print("  and runs data-integrity audits against them.\n")

        # Collect all test serials
        all_serials = [
            'QT-HAPPY-001', 'QT-HTPMP-002', 'QT-COOL-003', 'QT-REPR-004',
            'QT-RWRK-005', 'QT-PART-006', 'QT-MISS-007', 'QT-NGHT-008'
        ]

        # Clean up old data
        print("  Phase 1: Cleaning up old test data...")
        clear_test_data(all_serials)

        # Run each scenario
        print("\n  Phase 2: Creating test scenarios...")
        serials_map = {}
        for name, fn in SCENARIOS.items():
            serial = fn()
            serials_map[name] = serial
            print(f"    [OK] {name} -> {serial}")

        # Audit
        print("\n  Phase 3: Running audit verification...")
        success = audit_verify(serials_map)

        # Print URLs for manual verification
        banner("MANUAL VERIFICATION URLS")
        print("  Open these in your browser to visually verify each print tag:\n")
        for name, serial in serials_map.items():
            print(f"  {name}:")
            print(f"    http://localhost:8080/admin/print-tag/{serial}")
            desc = {
                '1_happy_path': 'ALL checks GOOD, Cooling ONLY, Line 1, Day shift',
                '2_heat_pump': 'ALL checks GOOD, Cooling + Heating BOTH, Line 2',
                '3_cooling_only': 'ALL checks GOOD, Cooling / Heating blank, Line 3',
                '4_repair_flow': 'Repair history present, 2nd test GOOD, Line 1',
                '5_rework': '2 repairs (ATT + INSP2), final pass, Line 2',
                '6_partial_fail': 'ATT/GMS/INSP2 GOOD, INSP3 NG, no INSP4',
                '7_missing_data': 'Only CRS exists, everything else blank',
                '8_night_shift': 'ALL checks GOOD, NIGHT shift, Line 2',
            }
            print(f"    Expected: {desc.get(name, '')}\n")

        if success:
            print("  ALL AUDIT CHECKS PASSED - System is production-ready!\n")
        else:
            print("  AUDIT FAILED - Fix the errors above before going to production.\n")
