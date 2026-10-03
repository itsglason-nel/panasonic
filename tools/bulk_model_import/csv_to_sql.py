#!/usr/bin/env python3
"""
csv_to_sql.py — Convert the 2-CSV bulk import format into MySQL INSERT statements.

Usage:
    python tools/bulk_model_import/csv_to_sql.py <config.csv> <parts.csv>
    python tools/bulk_model_import/csv_to_sql.py <config.csv> <parts.csv> > output.sql
    python tools/bulk_model_import/csv_to_sql.py <config.csv> <parts.csv> --execute

SAFETY:
  - This tool ONLY performs INSERT operations into: modelref, partref.
  - It does NOT modify any existing data, triggers, stored procedures, views,
    or any other table.
  - All INSERTs use INSERT IGNORE to skip duplicates gracefully.
"""

import csv
import sys
import re
import os

# ── Validation helpers ──────────────────────────────────────────────────────────

def _validate_length(value, maxlen, field_name, row_num, file_type):
    if value and len(value) > maxlen:
        raise ValueError(
            f"{file_type} Row {row_num}: '{field_name}' value '{value}' exceeds max length {maxlen}"
        )

def _validate_decimal(value, field_name, row_num, file_type, max_val=99.99):
    if value in ('', None):
        return '0'
    try:
        f = float(value)
        if f < 0 or f > max_val:
            raise ValueError(
                f"{file_type} Row {row_num}: '{field_name}' value '{value}' out of range 0–{max_val}"
            )
        return str(f)
    except (ValueError, TypeError):
        raise ValueError(
            f"{file_type} Row {row_num}: '{field_name}' value '{value}' is not a valid decimal"
        )

def _validate_program(value, field_name, row_num, file_type):
    if value in ('', None):
        return None
    if not re.match(r'^\d{2}:\d{2}$', value):
        raise ValueError(
            f"{file_type} Row {row_num}: '{field_name}' value '{value}' must be NN:NN format (e.g. 05:30)"
        )
    return value

def _validate_on_null(value, field_name, row_num, file_type):
    if value in ('', None):
        return None
    if value.upper() == 'ON':
        return 'ON'
    raise ValueError(
        f"{file_type} Row {row_num}: '{field_name}' value '{value}' must be 'ON' or blank"
    )

def _sql_str(value):
    """Escape a string for MySQL single-quoted literal."""
    if value is None:
        return 'NULL'
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"

def _sql_num(value):
    """Format a numeric for SQL."""
    if value in ('', None):
        return '0'
    return str(value)

# ── Main converter ──────────────────────────────────────────────────────────────

def convert_csv_to_sql(config_path, parts_path):
    statements = []
    errors = []
    seen_modelcodes = set()
    seen_spamsi_codes = set()
    seen_areas = set()
    part_counts = {}

    statements.append("-- ================================================================")
    statements.append(f"-- Auto-generated from: {os.path.basename(config_path)} and {os.path.basename(parts_path)}")
    statements.append("-- TABLES AFFECTED: areas, modelref, partref")
    statements.append("-- ================================================================")
    statements.append("")
    statements.append("START TRANSACTION;")
    statements.append("")

    # ── Parse Config CSV ────────────────────────────────────────────────────────
    try:
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Skip row 1 (Table|Column names)
            _ = next(reader, None)       # Skip row 2 (Constraints)
            
            for i, row in enumerate(reader, start=3):
                if not row or all(not cell.strip() for cell in row):
                    continue
                
                if len(row) < 21:
                    errors.append(f"Config Row {i}: Missing columns (found {len(row)}, expected 21)")
                    continue

                modelcode = row[0].strip()
                if not modelcode:
                    errors.append(f"Config Row {i}: modelcode is required")
                    continue
                
                _validate_length(modelcode, 14, 'modelcode', i, 'Config')
                if modelcode in seen_modelcodes:
                    errors.append(f"Config Row {i}: duplicate modelcode '{modelcode}'")
                    continue
                seen_modelcodes.add(modelcode)

                area = row[1].strip() or None
                serialstart = row[2].strip() or None
                program_h = _validate_program(row[3].strip(), 'program_h', i, 'Config')
                program_f = _validate_program(row[4].strip(), 'program_f', i, 'Config')

                _validate_length(area, 14, 'area', i, 'Config')
                if area:
                    seen_areas.add(area)
                _validate_length(serialstart, 6, 'serialstart', i, 'Config')

                gmstolpos = _validate_decimal(row[5].strip(), 'gmstolpos', i, 'Config')
                gmstolneg = _validate_decimal(row[6].strip(), 'gmstolneg', i, 'Config')
                op_current_base = _validate_decimal(row[7].strip(), 'op_current_base', i, 'Config')
                op_current_tolpos = _validate_decimal(row[8].strip(), 'op_current_tolpos', i, 'Config')
                op_current_tolneg = _validate_decimal(row[9].strip(), 'op_current_tolneg', i, 'Config')
                in_power_base = _validate_decimal(row[10].strip(), 'in_power_base', i, 'Config')
                in_power_tolpos = _validate_decimal(row[11].strip(), 'in_power_tolpos', i, 'Config')
                in_power_tolneg = _validate_decimal(row[12].strip(), 'in_power_tolneg', i, 'Config')
                temp_diff_base = _validate_decimal(row[13].strip(), 'temp_diff_base', i, 'Config')
                temp_diff_tolpos = _validate_decimal(row[14].strip(), 'temp_diff_tolpos', i, 'Config')
                temp_diff_tolneg = _validate_decimal(row[15].strip(), 'temp_diff_tolneg', i, 'Config')

                ritheat1 = _validate_on_null(row[16].strip(), 'ritheat1', i, 'Config')
                ritheat2 = _validate_on_null(row[17].strip(), 'ritheat2', i, 'Config')
                pittws = _validate_on_null(row[18].strip(), 'pittws', i, 'Config')

                spamsi_code = row[19].strip() or None
                spamso_out = row[20].strip() or None

                if spamsi_code:
                    _validate_length(spamsi_code, 4, 'spamsi_unique_code', i, 'Config')
                    if spamsi_code in seen_spamsi_codes:
                        errors.append(f"Config Row {i}: duplicate spamsi_unique_code '{spamsi_code}'")
                    seen_spamsi_codes.add(spamsi_code)

                if spamso_out:
                    _validate_length(spamso_out, 14, 'spamso_outmodel', i, 'Config')

        # ── Write Areas ─────────────────────────────────────────────────────────────
        if seen_areas:
            statements.append("-- Ensure all areas exist")
            area_values = ", ".join([f"({_sql_str(a)})" for a in sorted(seen_areas)])
            statements.append(f"INSERT IGNORE INTO `areas` (`name`) VALUES {area_values};")
            statements.append("")

        # ── Process Config Data Again for Model Inserts ─────────────────────────────
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Skip row 1
            _ = next(reader, None)       # Skip row 2
            
            for i, row in enumerate(reader, start=3):
                if not row or all(not cell.strip() for cell in row):
                    continue
                
                modelcode = row[0].strip()
                area = row[1].strip() or None
                serialstart = row[2].strip() or None
                program_h = _validate_program(row[3].strip(), 'program_h', i, 'Config')
                program_f = _validate_program(row[4].strip(), 'program_f', i, 'Config')
                gmstolpos = _validate_decimal(row[5].strip(), 'gmstolpos', i, 'Config')
                gmstolneg = _validate_decimal(row[6].strip(), 'gmstolneg', i, 'Config')
                op_current_base = _validate_decimal(row[7].strip(), 'op_current_base', i, 'Config')
                op_current_tolpos = _validate_decimal(row[8].strip(), 'op_current_tolpos', i, 'Config')
                op_current_tolneg = _validate_decimal(row[9].strip(), 'op_current_tolneg', i, 'Config')
                in_power_base = _validate_decimal(row[10].strip(), 'in_power_base', i, 'Config')
                in_power_tolpos = _validate_decimal(row[11].strip(), 'in_power_tolpos', i, 'Config')
                in_power_tolneg = _validate_decimal(row[12].strip(), 'in_power_tolneg', i, 'Config')
                temp_diff_base = _validate_decimal(row[13].strip(), 'temp_diff_base', i, 'Config')
                temp_diff_tolpos = _validate_decimal(row[14].strip(), 'temp_diff_tolpos', i, 'Config')
                temp_diff_tolneg = _validate_decimal(row[15].strip(), 'temp_diff_tolneg', i, 'Config')
                ritheat1 = _validate_on_null(row[16].strip(), 'ritheat1', i, 'Config')
                ritheat2 = _validate_on_null(row[17].strip(), 'ritheat2', i, 'Config')
                pittws = _validate_on_null(row[18].strip(), 'pittws', i, 'Config')
                spamsi_code = row[19].strip() or None
                spamso_out = row[20].strip() or None

                statements.append("-- Model: " + modelcode)
                statements.append(
                    f"INSERT IGNORE INTO `modelref` "
                    f"(`modelcode`, `area`, `serialstart`, `program_h`, `program_f`, "
                    f"`gmstolpos`, `gmstolneg`, "
                    f"`op_current_base`, `op_current_tolpos`, `op_current_tolneg`, "
                    f"`in_power_base`, `in_power_tolpos`, `in_power_tolneg`, "
                    f"`temp_diff_base`, `temp_diff_tolpos`, `temp_diff_tolneg`, "
                    f"`ritheat1`, `ritheat2`, `pittws`, `spamsi_unique`) VALUES ("
                    f"{_sql_str(modelcode)}, {_sql_str(area)}, {_sql_str(serialstart)}, "
                    f"{_sql_str(program_h)}, {_sql_str(program_f)}, "
                    f"{_sql_num(gmstolpos)}, {_sql_num(gmstolneg)}, "
                    f"{_sql_num(op_current_base)}, {_sql_num(op_current_tolpos)}, {_sql_num(op_current_tolneg)}, "
                    f"{_sql_num(in_power_base)}, {_sql_num(in_power_tolpos)}, {_sql_num(in_power_tolneg)}, "
                    f"{_sql_num(temp_diff_base)}, {_sql_num(temp_diff_tolpos)}, {_sql_num(temp_diff_tolneg)}, "
                    f"{_sql_str(ritheat1)}, {_sql_str(ritheat2)}, {_sql_str(pittws)}, {_sql_str(spamsi_code)});"
                )


                if spamso_out:
                    statements.append(
                        f"INSERT IGNORE INTO `partref` "
                        f"(`modelcode`, `module`, `partno`, `partdesc`, `usage`, `tag`) VALUES ("
                        f"{_sql_str(modelcode)}, 'SPAMSO', {_sql_str(spamso_out)}, 'Outdoor Control Board', 1, 'Outdoor Control Board');"
                    )
                statements.append("")

    except Exception as e:
        errors.append(f"Failed parsing Config CSV: {e}")


    # ── Parse Parts CSV ────────────────────────────────────────────────────────
    try:
        with open(parts_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Skip row 1
            _ = next(reader, None)       # Skip row 2
            
            for i, row in enumerate(reader, start=3):
                if not row or all(not cell.strip() for cell in row):
                    continue
                
                if len(row) < 6:
                    errors.append(f"Parts Row {i}: Missing columns (found {len(row)}, expected 6)")
                    continue

                modelcode = row[0].strip()
                module = row[1].strip()
                partno = row[2].strip()
                partdesc = row[3].strip()
                usage_val = _validate_decimal(row[4].strip() or '1', 'usage', i, 'Parts')
                tag = row[5].strip()

                if not modelcode:
                    errors.append(f"Parts Row {i}: modelcode missing")
                    continue
                if modelcode not in seen_modelcodes:
                    errors.append(f"Parts Row {i}: modelcode '{modelcode}' not found in config CSV")
                    continue
                
                if not module:
                    errors.append(f"Parts Row {i}: module missing")
                    continue
                if not partno:
                    errors.append(f"Parts Row {i}: partno missing")
                    continue

                _validate_length(modelcode, 14, 'modelcode', i, 'Parts')
                _validate_length(module, 8, 'module', i, 'Parts')
                _validate_length(partno, 14, 'partno', i, 'Parts')
                _validate_length(partdesc, 60, 'partdesc', i, 'Parts')
                _validate_length(tag, 14, 'tag', i, 'Parts')

                part_counts[modelcode] = part_counts.get(modelcode, 0) + 1
                if part_counts[modelcode] > 20:
                    errors.append(f"Parts Row {i}: model '{modelcode}' exceeds 20-part limit")
                    continue

                statements.append(
                    f"INSERT INTO `partref` "
                    f"(`modelcode`, `module`, `partno`, `partdesc`, `usage`, `tag`) VALUES ("
                    f"{_sql_str(modelcode)}, {_sql_str(module)}, {_sql_str(partno)}, "
                    f"{_sql_str(partdesc)}, {_sql_num(usage_val)}, {_sql_str(tag)});"
                )
    except Exception as e:
        errors.append(f"Failed parsing Parts CSV: {e}")

    statements.append("")
    statements.append("COMMIT;")
    statements.append("")
    statements.append(f"-- Summary: {len(seen_modelcodes)} model(s), {sum(part_counts.values())} part(s)")

    if errors:
        print("VALIDATION ERRORS -- SQL not generated:", file=sys.stderr)
        for err in errors:
            print(f"  x {err}", file=sys.stderr)
        sys.exit(1)

    return statements

# ── Entry point ─────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/bulk_model_import/csv_to_sql.py <config.csv> <parts.csv> [--execute]", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    parts_path = sys.argv[2]
    execute_flag = '--execute' in sys.argv

    if not os.path.isfile(config_path):
        print(f"File not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(parts_path):
        print(f"File not found: {parts_path}", file=sys.stderr)
        sys.exit(1)

    sql_lines = convert_csv_to_sql(config_path, parts_path)
    sql_text = '\n'.join(sql_lines)

    if execute_flag:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
            from app import create_app
            from app.models import db as _db

            app = create_app()
            with app.app_context():
                for stmt in sql_lines:
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith('--'):
                        _db.session.execute(_db.text(stmt))
                _db.session.commit()
                print("[OK] All statements executed successfully.")
                print(sql_text)
        except Exception as e:
            print(f"[FAIL] Execution failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(sql_text)

if __name__ == '__main__':
    main()
