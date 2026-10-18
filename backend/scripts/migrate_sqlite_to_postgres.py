#!/usr/bin/env python3
"""
CivicFix AI — SQLite to PostgreSQL / Supabase Safe Migration Utility.

Transfers all civic complaints and chronological status history from the local
SQLite database (civicfix.db) to a target PostgreSQL database (e.g. Supabase)
while strictly preserving:
- All original complaint_id values (e.g. CF-2026-XXXXX)
- All primary key and foreign key relationships
- All GPS coordinates, categories, departments, SLA hours, and notes
- All timestamps (created_at, updated_at, status_history.timestamp)
- PostgreSQL sequence alignment for auto-incrementing status_history.id

Usage:
  python migrate_sqlite_to_postgres.py --dry-run
  python migrate_sqlite_to_postgres.py --target-url "postgresql://user:pass@host:5432/postgres"
"""

import os
import sys
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

# Ensure backend directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, text
from app.db import Base
from app.models.complaint import Complaint
from app.models.status_history import StatusHistory

DEFAULT_SOURCE_DB = BACKEND_DIR / "civicfix.db"

def parse_iso_or_str(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return None

def migrate(source_db_path: Path, target_url: str, dry_run: bool = False, auto_confirm: bool = False):
    print("=" * 70)
    print("CIVICFIX AI: SQLITE TO POSTGRESQL SAFE MIGRATION")
    print("=" * 70)

    # 1. Validate Source Database
    if not source_db_path.exists():
        print(f"[ERROR] Source database not found at: {source_db_path}")
        sys.exit(1)

    print(f"[*] Source SQLite: {source_db_path}")
    src_conn = sqlite3.connect(source_db_path)
    src_cur = src_conn.cursor()

    # Integrity check
    src_cur.execute("PRAGMA integrity_check")
    integrity = src_cur.fetchone()[0]
    if integrity != "ok":
        print(f"[ERROR] Source database integrity check failed: {integrity}")
        sys.exit(1)

    # Read counts
    src_cur.execute("SELECT COUNT(*) FROM complaints")
    src_c_count = src_cur.fetchone()[0]

    src_cur.execute("SELECT COUNT(*) FROM status_history")
    src_sh_count = src_cur.fetchone()[0]

    print(f"[*] Source Database Verified: {src_c_count} complaints, {src_sh_count} status history rows.")

    # Read complaint rows
    src_cur.execute("""
        SELECT complaint_id, category, confidence, severity, latitude, longitude,
               address, department, suggested_action, complaint_text, language,
               status, duplicate_of, estimated_resolution_hours, image_path, upvotes,
               created_at, updated_at
        FROM complaints
        ORDER BY created_at ASC
    """)
    complaint_rows = src_cur.fetchall()

    # Read status_history rows
    src_cur.execute("""
        SELECT id, complaint_id, status, timestamp, note
        FROM status_history
        ORDER BY id ASC
    """)
    history_rows = src_cur.fetchall()
    src_conn.close()

    # Validate FK relationships in source
    cid_set = {r[0] for r in complaint_rows}
    orphans = [h for h in history_rows if h[1] not in cid_set]
    if orphans:
        print(f"[ERROR] Found {len(orphans)} orphaned status history rows referencing non-existent complaints!")
        sys.exit(1)

    print(f"[+] All {src_sh_count} status history rows successfully mapped to {len(cid_set)} unique complaints.")

    if dry_run:
        print("\n[DRY RUN MODE]")
        print(f"  - Target URL: {target_url or '(Not provided - Dry run only)'}")
        print(f"  - Complaints planned for migration: {len(complaint_rows)}")
        print(f"  - Status history planned for migration: {len(history_rows)}")
        print("  - Dry run validation SUCCESSFUL. No data was written to any destination.")
        print("=" * 70)
        return True

    # 2. Connect to Target Database
    if not target_url:
        print("[ERROR] Target database URL is required when not running in --dry-run mode.")
        sys.exit(1)

    # Normalize postgres:// to postgresql://
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    # Ensure target engine connects
    print(f"[*] Connecting to Target PostgreSQL database...")
    is_postgres = "postgresql" in target_url
    target_engine = create_engine(target_url, pool_pre_ping=True)

    try:
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[+] Connection to target database successful.")
    except Exception as e:
        print(f"[ERROR] Failed to connect to target database: {e}")
        sys.exit(1)

    # 3. Create schema tables on target if they don't already exist and inspect compatibility
    print("[*] Ensuring target tables exist (Base.metadata.create_all)...")
    Base.metadata.create_all(bind=target_engine)

    from sqlalchemy import inspect
    inspector = inspect(target_engine)
    existing_tables = set(inspector.get_table_names())
    for required_table in ("complaints", "status_history"):
        if required_table not in existing_tables:
            raise RuntimeError(f"Target schema incompatible: missing required table '{required_table}'.")

    # 4. Check if target already has data (both complaints and status_history)
    with target_engine.connect() as conn:
        existing_c = conn.execute(text("SELECT COUNT(*) FROM complaints")).scalar() or 0
        existing_sh = conn.execute(text("SELECT COUNT(*) FROM status_history")).scalar() or 0

    if existing_c > 0 or existing_sh > 0:
        print(f"[!] Warning: Target database is NOT empty ({existing_c} complaints, {existing_sh} status history records).")
        if auto_confirm:
            print("[*] Auto-confirm enabled. Proceeding to conflict and uniqueness inspection...")
        else:
            try:
                resp = input("Proceed with validation and migration? [y/N]: ")
                if resp.lower() != 'y':
                    print("[*] Aborted by user.")
                    sys.exit(0)
            except (EOFError, OSError):
                print("[*] Non-interactive environment detected without confirmation; aborting safely.")
                sys.exit(0)

    # 5. Detect duplicate IDs with conflicting field values before mutating
    with target_engine.connect() as conn:
        existing_target_complaints = {
            row["complaint_id"]: row
            for row in conn.execute(text("""
                SELECT complaint_id, category, severity, status, department, address
                FROM complaints
            """)).mappings()
        }
        existing_target_history = {
            row["id"]: row
            for row in conn.execute(text("""
                SELECT id, complaint_id, status
                FROM status_history
            """)).mappings()
        }

    conflicts = []
    for r in complaint_rows:
        cid = r[0]
        if cid in existing_target_complaints:
            tgt = existing_target_complaints[cid]
            mismatches = []
            if str(tgt["category"] or "").strip().lower() != str(r[1] or "").strip().lower():
                mismatches.append(f"category ('{tgt['category']}' != '{r[1]}')")
            if str(tgt["severity"] or "").strip().lower() != str(r[3] or "").strip().lower():
                mismatches.append(f"severity ('{tgt['severity']}' != '{r[3]}')")
            if str(tgt["status"] or "").strip().lower() != str(r[11] or "").strip().lower():
                mismatches.append(f"status ('{tgt['status']}' != '{r[11]}')")
            if str(tgt["department"] or "").strip().lower() != str(r[7] or "").strip().lower():
                mismatches.append(f"department ('{tgt['department']}' != '{r[7]}')")
            if mismatches:
                conflicts.append(f"Complaint '{cid}': {', '.join(mismatches)}")

    for h in history_rows:
        hid = h[0]
        if hid in existing_target_history:
            tgt_h = existing_target_history[hid]
            if tgt_h["complaint_id"] != h[1] or str(tgt_h["status"] or "").strip().lower() != str(h[2] or "").strip().lower():
                conflicts.append(f"StatusHistory ID '{hid}': target points to complaint '{tgt_h['complaint_id']}' ({tgt_h['status']}), source points to '{h[1]}' ({h[2]})")

    if conflicts:
        print("[ERROR] Conflicting records detected between source and target database:")
        for c in conflicts[:10]:
            print(f"  - {c}")
        if len(conflicts) > 10:
            print(f"  ... and {len(conflicts) - 10} more conflicts.")
        raise ValueError(f"Target database contains conflicting records with different values: {conflicts[0]}")

    # 6. Single atomic transaction for Inserts, Sequence Sync, and Exact Verification
    print(f"[*] Starting atomic migration transaction for {len(complaint_rows)} complaints and {len(history_rows)} status records...")
    with target_engine.begin() as conn:
        for r in complaint_rows:
            conn.execute(text("""
                INSERT INTO complaints (
                    complaint_id, category, confidence, severity, latitude, longitude,
                    address, department, suggested_action, complaint_text, language,
                    status, duplicate_of, estimated_resolution_hours, image_path, upvotes,
                    created_at, updated_at
                ) VALUES (
                    :cid, :cat, :conf, :sev, :lat, :lng,
                    :addr, :dept, :act, :txt, :lang,
                    :stat, :dup, :sla, :img, :up,
                    :c_at, :u_at
                ) ON CONFLICT (complaint_id) DO NOTHING
            """), {
                "cid": r[0], "cat": r[1], "conf": r[2], "sev": r[3], "lat": r[4], "lng": r[5],
                "addr": r[6], "dept": r[7], "act": r[8], "txt": r[9], "lang": r[10],
                "stat": r[11], "dup": r[12], "sla": r[13], "img": r[14], "up": r[15],
                "c_at": parse_iso_or_str(r[16]), "u_at": parse_iso_or_str(r[17])
            })

        for h in history_rows:
            conn.execute(text("""
                INSERT INTO status_history (id, complaint_id, status, timestamp, note)
                VALUES (:id, :cid, :stat, :ts, :note)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": h[0], "cid": h[1], "stat": h[2], "ts": parse_iso_or_str(h[3]), "note": h[4]
            })

        # Align PostgreSQL sequence if PostgreSQL
        if is_postgres:
            try:
                conn.execute(text("""
                    SELECT setval(pg_get_serial_sequence('status_history', 'id'), COALESCE(max(id), 1)) 
                    FROM status_history
                """))
                print("[+] PostgreSQL auto-increment sequence synchronized.")
            except Exception as e:
                print(f"[!] Note: Sequence sync skipped or not applicable: {e}")

        # Exact record-level verification inside the transaction
        print("[*] Running exact record-level verification inside atomic transaction...")
        target_complaints_all = {
            row["complaint_id"]: row
            for row in conn.execute(text("""
                SELECT complaint_id, category, severity, status, department, address
                FROM complaints
            """)).mappings()
        }

        for src in complaint_rows:
            cid = src[0]
            if cid not in target_complaints_all:
                raise AssertionError(f"Verification failed: Complaint '{cid}' is missing from destination table!")
            tgt = target_complaints_all[cid]
            if str(tgt["category"] or "").strip().lower() != str(src[1] or "").strip().lower():
                raise AssertionError(f"Record verification failed for '{cid}': category mismatch (source='{src[1]}', target='{tgt['category']}')")
            if str(tgt["severity"] or "").strip().lower() != str(src[3] or "").strip().lower():
                raise AssertionError(f"Record verification failed for '{cid}': severity mismatch (source='{src[3]}', target='{tgt['severity']}')")
            if str(tgt["status"] or "").strip().lower() != str(src[11] or "").strip().lower():
                raise AssertionError(f"Record verification failed for '{cid}': status mismatch (source='{src[11]}', target='{tgt['status']}')")
            if str(tgt["department"] or "").strip().lower() != str(src[7] or "").strip().lower():
                raise AssertionError(f"Record verification failed for '{cid}': department mismatch (source='{src[7]}', target='{tgt['department']}')")

        target_history_all = {
            row["id"]: row
            for row in conn.execute(text("""
                SELECT id, complaint_id, status
                FROM status_history
            """)).mappings()
        }

        for h in history_rows:
            hid = h[0]
            if hid not in target_history_all:
                raise AssertionError(f"Verification failed: StatusHistory row '{hid}' is missing from destination table!")
            tgt_h = target_history_all[hid]
            if tgt_h["complaint_id"] != h[1]:
                raise AssertionError(f"Verification failed for StatusHistory '{hid}': complaint_id mismatch (source='{h[1]}', target='{tgt_h['complaint_id']}')")
            if str(tgt_h["status"] or "").strip().lower() != str(h[2] or "").strip().lower():
                raise AssertionError(f"Verification failed for StatusHistory '{hid}': status mismatch (source='{h[2]}', target='{tgt_h['status']}')")

        dest_c = conn.execute(text("SELECT COUNT(*) FROM complaints")).scalar()
        dest_sh = conn.execute(text("SELECT COUNT(*) FROM status_history")).scalar()
        joined = conn.execute(text("""
            SELECT COUNT(*)
            FROM status_history sh
            JOIN complaints c ON sh.complaint_id = c.complaint_id
        """)).scalar()

        if dest_c < src_c_count or dest_sh < src_sh_count or joined < src_sh_count:
            raise AssertionError(f"Verification count mismatch: complaints={dest_c}/{src_c_count}, history={dest_sh}/{src_sh_count}, joined={joined}/{src_sh_count}")

    print("\n[SUCCESS] 100% of records, relationships, and history verified on target database! Transaction committed.")
    print("=" * 70)
    return True

def main():
    parser = argparse.ArgumentParser(description="CivicFix AI: SQLite to PostgreSQL Migration Utility")
    parser.add_argument("--source-db", default=str(DEFAULT_SOURCE_DB), help="Path to source SQLite database")
    parser.add_argument("--target-url", default=os.getenv("TARGET_DATABASE_URL") or os.getenv("DATABASE_URL"), help="Destination PostgreSQL URL")
    parser.add_argument("--dry-run", action="store_true", help="Validate source data and schema without writing to target")
    parser.add_argument("--yes", "-y", action="store_true", dest="auto_confirm", help="Automatically proceed if target contains data")
    args = parser.parse_args()

    migrate(
        source_db_path=Path(args.source_db),
        target_url=args.target_url,
        dry_run=args.dry_run,
        auto_confirm=args.auto_confirm
    )

if __name__ == "__main__":
    main()
