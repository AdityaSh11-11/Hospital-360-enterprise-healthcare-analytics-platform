from ai.sql_guard import validate_and_limit

def test_select_allowed():
    r = validate_and_limit(
        "SELECT department_name, admissions "
        "FROM analytics.vw_department_performance"
    )
    assert r.safe
    assert "LIMIT" in r.sql.upper()

def test_with_allowed():
    r = validate_and_limit(
        "WITH x AS (SELECT * FROM warehouse.fact_admission LIMIT 5) "
        "SELECT * FROM x"
    )
    assert r.safe

def test_delete_blocked():
    assert not validate_and_limit(
        "DELETE FROM warehouse.fact_admission"
    ).safe

def test_update_blocked():
    assert not validate_and_limit(
        "UPDATE warehouse.fact_billing SET net_amount = 0"
    ).safe

def test_system_schema_blocked():
    assert not validate_and_limit(
        "SELECT * FROM pg_catalog.pg_roles"
    ).safe

def test_information_schema_blocked():
    assert not validate_and_limit(
        "SELECT * FROM information_schema.tables"
    ).safe

def test_multiple_statements_blocked():
    assert not validate_and_limit(
        "SELECT * FROM warehouse.dim_patient; "
        "SELECT * FROM warehouse.dim_doctor"
    ).safe

def test_unqualified_relation_blocked():
    assert not validate_and_limit(
        "SELECT * FROM dim_patient"
    ).safe
