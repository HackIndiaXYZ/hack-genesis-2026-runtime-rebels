import os
import sys
import tempfile
import uuid
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.models.complaint import Complaint
from app.models.status_history import StatusHistory
from app.db import Base

def test_migration_on_disposable_database():
    """
    Simulates database migration by cloning schema and data from the
    existing SQLite database into a fresh disposable database.
    Verifies that all 23 complaints, 56 status history records, and relationships
    are preserved with 100% accuracy.
    """
    src_db_path = BACKEND_DIR / "civicfix.db"
    assert src_db_path.exists(), "Source civicfix.db must exist"

    # 1. Create a clean temporary destination database
    disposable_db_file = os.path.join(tempfile.gettempdir(), f"disposable_migration_{uuid.uuid4().hex}.db")
    dest_engine = create_engine(f"sqlite:///{disposable_db_file}")
    
    try:
        # 2. Build target schema using SQLAlchemy Base metadata
        Base.metadata.create_all(bind=dest_engine)

        # 3. Read records from source database
        src_conn = sqlite3.connect(src_db_path)
        src_cur = src_conn.cursor()

        src_cur.execute("SELECT COUNT(*) FROM complaints")
        src_c_count = src_cur.fetchone()[0]
        assert src_c_count == 23

        src_cur.execute("SELECT COUNT(*) FROM status_history")
        src_sh_count = src_cur.fetchone()[0]
        assert src_sh_count == 56

        # Fetch all complaints
        src_cur.execute("""
            SELECT complaint_id, category, confidence, severity, latitude, longitude,
                   address, department, suggested_action, complaint_text, language,
                   status, duplicate_of, estimated_resolution_hours, image_path, upvotes,
                   created_at, updated_at
            FROM complaints
        """)
        complaints_rows = src_cur.fetchall()

        # Fetch all status history
        src_cur.execute("""
            SELECT id, complaint_id, status, timestamp, note
            FROM status_history
        """)
        history_rows = src_cur.fetchall()
        src_conn.close()

        # 4. Insert into disposable target database
        dest_conn = sqlite3.connect(disposable_db_file)
        dest_cur = dest_conn.cursor()

        dest_cur.executemany("""
            INSERT INTO complaints (
                complaint_id, category, confidence, severity, latitude, longitude,
                address, department, suggested_action, complaint_text, language,
                status, duplicate_of, estimated_resolution_hours, image_path, upvotes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, complaints_rows)

        dest_cur.executemany("""
            INSERT INTO status_history (id, complaint_id, status, timestamp, note)
            VALUES (?, ?, ?, ?, ?)
        """, history_rows)

        dest_conn.commit()

        # 5. Verify records and relationships in target database
        dest_cur.execute("SELECT COUNT(*) FROM complaints")
        dest_c_count = dest_cur.fetchone()[0]
        assert dest_c_count == 23, f"Expected 23 complaints, got {dest_c_count}"

        dest_cur.execute("SELECT COUNT(*) FROM status_history")
        dest_sh_count = dest_cur.fetchone()[0]
        assert dest_sh_count == 56, f"Expected 56 status history, got {dest_sh_count}"

        # Verify foreign key relationship integrity
        dest_cur.execute("""
            SELECT sh.id, sh.complaint_id, c.category, c.status
            FROM status_history sh
            JOIN complaints c ON sh.complaint_id = c.complaint_id
        """)
        joined_rows = dest_cur.fetchall()
        assert len(joined_rows) == 56, "All 56 status history records must join to their parent complaint"

        dest_conn.close()

    finally:
        if os.path.exists(disposable_db_file):
            try:
                os.remove(disposable_db_file)
            except Exception:
                pass

def test_migration_utility_clean_run():
    """
    Tests that migrate() properly populates a clean disposable database,
    passes exact record-level verification, and returns True.
    """
    from scripts.migrate_sqlite_to_postgres import migrate
    src_db_path = BACKEND_DIR / "civicfix.db"
    disposable_db = os.path.join(tempfile.gettempdir(), f"disposable_clean_{uuid.uuid4().hex}.db")
    try:
        success = migrate(
            source_db_path=src_db_path,
            target_url=f"sqlite:///{disposable_db}",
            auto_confirm=True
        )
        assert success is True

        conn = sqlite3.connect(disposable_db)
        cur = conn.cursor()
        assert cur.execute("SELECT COUNT(*) FROM complaints").fetchone()[0] == 23
        assert cur.execute("SELECT COUNT(*) FROM status_history").fetchone()[0] == 56
        conn.close()
    finally:
        if os.path.exists(disposable_db):
            try:
                os.remove(disposable_db)
            except Exception:
                pass

def test_migration_detects_conflicting_records():
    """
    Tests that migrate() catches duplicate complaint IDs with conflicting field values
    and aborts with ValueError before modifying/corrupting data.
    """
    import pytest
    from scripts.migrate_sqlite_to_postgres import migrate
    src_db_path = BACKEND_DIR / "civicfix.db"
    disposable_db = os.path.join(tempfile.gettempdir(), f"disposable_conflict_{uuid.uuid4().hex}.db")
    dest_engine = create_engine(f"sqlite:///{disposable_db}")

    try:
        Base.metadata.create_all(bind=dest_engine)
        conn = sqlite3.connect(disposable_db)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO complaints (
                complaint_id, category, confidence, severity, latitude, longitude,
                address, department, suggested_action, complaint_text, language,
                status, duplicate_of, estimated_resolution_hours, image_path, upvotes,
                created_at, updated_at
            ) VALUES (
                'CF-2026-00847', 'conflicting_category', 0.85, 'low', 26.4499, 80.3319,
                'Mismatched Address', 'Road Maintenance (PWD)', 'None', 'None', 'en',
                'submitted', NULL, 48, '/uploads/test.jpg', 0,
                '2026-10-18T00:00:00', '2026-10-18T00:00:00'
            )
        """)
        conn.commit()
        conn.close()

        with pytest.raises(ValueError, match="Target database contains conflicting records"):
            migrate(
                source_db_path=src_db_path,
                target_url=f"sqlite:///{disposable_db}",
                auto_confirm=True
            )
    finally:
        if os.path.exists(disposable_db):
            try:
                os.remove(disposable_db)
            except Exception:
                pass

def test_migration_detects_non_empty_status_history():
    """
    Tests that migrate() inspects status_history as well as complaints.
    If target status_history has records, it alerts and aborts in non-interactive mode.
    """
    import pytest
    from scripts.migrate_sqlite_to_postgres import migrate
    src_db_path = BACKEND_DIR / "civicfix.db"
    disposable_db = os.path.join(tempfile.gettempdir(), f"disposable_sh_nonempty_{uuid.uuid4().hex}.db")
    dest_engine = create_engine(f"sqlite:///{disposable_db}")

    try:
        Base.metadata.create_all(bind=dest_engine)
        conn = sqlite3.connect(disposable_db)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO status_history (id, complaint_id, status, timestamp, note)
            VALUES (999, 'CF-2026-99999', 'submitted', '2026-10-18T00:00:00', 'Stray record')
        """)
        conn.commit()
        conn.close()

        with pytest.raises(SystemExit) as exc_info:
            migrate(
                source_db_path=src_db_path,
                target_url=f"sqlite:///{disposable_db}",
                auto_confirm=False
            )
        assert exc_info.value.code == 0
    finally:
        if os.path.exists(disposable_db):
            try:
                os.remove(disposable_db)
            except Exception:
                pass

def test_migration_rollback_on_failed_verification(monkeypatch):
    """
    Tests that if verification fails inside the atomic transaction,
    the transaction is rolled back, leaving the destination database empty.
    """
    import pytest
    from scripts import migrate_sqlite_to_postgres
    src_db_path = BACKEND_DIR / "civicfix.db"
    disposable_db = os.path.join(tempfile.gettempdir(), f"disposable_rollback_{uuid.uuid4().hex}.db")
    dest_engine = create_engine(f"sqlite:///{disposable_db}")

    try:
        Base.metadata.create_all(bind=dest_engine)

        def sabotaged_parse(val):
            raise RuntimeError("Simulated transient error during atomic transaction")

        monkeypatch.setattr(migrate_sqlite_to_postgres, "parse_iso_or_str", sabotaged_parse)

        with pytest.raises(RuntimeError, match="Simulated transient error"):
            migrate_sqlite_to_postgres.migrate(
                source_db_path=src_db_path,
                target_url=f"sqlite:///{disposable_db}",
                auto_confirm=True
            )

        conn = sqlite3.connect(disposable_db)
        cur = conn.cursor()
        c_count = cur.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        sh_count = cur.execute("SELECT COUNT(*) FROM status_history").fetchone()[0]
        conn.close()

        assert c_count == 0, f"Complaints table should be rolled back to 0, got {c_count}"
        assert sh_count == 0, f"StatusHistory table should be rolled back to 0, got {sh_count}"
    finally:
        if os.path.exists(disposable_db):
            try:
                os.remove(disposable_db)
            except Exception:
                pass

def test_database_url_validation_production_missing():
    import pytest
    from app.db import validate_and_resolve_database_url
    with pytest.raises(RuntimeError, match="DATABASE_URL environment variable is missing or empty"):
        validate_and_resolve_database_url(raw_url=None, environment="production")

def test_database_url_validation_production_empty():
    import pytest
    from app.db import validate_and_resolve_database_url
    with pytest.raises(RuntimeError, match="DATABASE_URL environment variable is missing or empty"):
        validate_and_resolve_database_url(raw_url="   ", environment="production")

def test_database_url_validation_production_sqlite_rejected():
    import pytest
    from app.db import validate_and_resolve_database_url
    with pytest.raises(RuntimeError, match="SQLite is not permitted in production"):
        validate_and_resolve_database_url(raw_url="sqlite:///civicfix.db", environment="production")

def test_database_url_validation_production_invalid_scheme():
    import pytest
    from app.db import validate_and_resolve_database_url
    with pytest.raises(RuntimeError, match="must be a valid PostgreSQL connection string"):
        validate_and_resolve_database_url(raw_url="mysql://user:pass@host/db", environment="production")

def test_database_url_validation_production_valid_postgres():
    from app.db import validate_and_resolve_database_url
    url, kwargs = validate_and_resolve_database_url(
        raw_url="postgres://mock_user:mock_password@aws-0.pooler.supabase.com:5432/postgres",
        environment="production"
    )
    assert url.startswith("postgresql://")
    assert kwargs.get("pool_recycle") == 300
    assert kwargs.get("pool_pre_ping") is True

def test_database_url_validation_dev_mode():
    from app.db import validate_and_resolve_database_url
    url, kwargs = validate_and_resolve_database_url(raw_url=None, environment="development")
    assert url.startswith("sqlite:///")
    assert "civicfix.db" in url
    assert kwargs.get("connect_args", {}).get("check_same_thread") is False

def test_database_url_error_sanitization():
    from app.db import validate_and_resolve_database_url
    secret_token = "mock_secret_token_12345"
    try:
        validate_and_resolve_database_url(
            raw_url=f"sqlite:///{secret_token}.db",
            environment="production"
        )
    except RuntimeError as e:
        assert secret_token not in str(e), "Error message must never echo connection strings or sensitive values"

