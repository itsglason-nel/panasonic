from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_schema_file_contains_unique_reference_table():
    for rel in [
        'migrations/000_new_initial_schema.sql',
        'migrations/002_add_to_server.sql',
        'migrations/004_add_spamsi_unique_codes.sql',
    ]:
        text = read(rel)
        assert 'spamsi_unique_refs' in text
        assert 'UNIQUE KEY `uq_spamsi_unique_ref_modelcode`' in text
        assert 'UNIQUE KEY `uq_spamsi_unique_ref_code`' in text


def test_spamsi_procedure_sets_and_clears_inunique_code():
    for rel in ['migrations/000_new_initial_schema.sql', 'migrations/002_add_to_server.sql', 'scratch_sp.sql']:
        text = read(rel)
        assert "SELECT unique_code INTO v_spamsi_unique_code" in text
        assert 'UPDATE linestat SET' in text
        assert 'inuniqe = v_spamsi_unique_code' in text
        assert 'inuniqe = NULL' in text or 'inuniqe = NULL' in text


def test_admin_ui_has_spamsi_unique_code_fields():
    modal = read('app/templates/admin/components/modals.html')
    scripts = read('app/templates/admin/components/scripts.html')
    assert 'SPAMSI Unique Code' in modal
    assert 'mc-spamsi-unique-code' in modal
    assert 'spamsi_unique_code' in scripts
