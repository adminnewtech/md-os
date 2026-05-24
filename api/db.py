"""MD-OS Database Layer.

Supports two backends:
  - IN-MEMORY (default, dev): dict per table in store.py
  - POSTGRES  (production): real SQL via psycopg2 + pgvector

Migrations run automatically on startup when POSTGRES_URI is set.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import sqlparse

# Backend selection
POSTGRES_URI = os.environ.get("POSTGRES_URI", "")
USE_POSTGRES = bool(POSTGRES_URI)

# ---------------------------------------------------------------------------
# Postgres connection (lazy — only when USE_POSTGRES)
# ---------------------------------------------------------------------------

_pg_pool: Any = None


def _get_pg_pool():
    global _pg_pool
    if _pg_pool is None:
        import psycopg2
        from psycopg2 import pool

        _pg_pool = pool.ThreadedConnectionPool(minconn=1, maxconn=10, dsn=POSTGRES_URI)
    return _pg_pool


@contextmanager
def pg_connection() -> Generator[Any, None, None]:
    pool = _get_pg_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@contextmanager
def pg_cursor() -> Generator[Any, None, None]:
    with pg_connection() as conn:
        cur = conn.cursor()
        try:
            yield cur
        finally:
            cur.close()


# ---------------------------------------------------------------------------
# Schema discovery — read .sql files from /root/md-os/schemas/
# ---------------------------------------------------------------------------

SCHEMAS_DIR = Path("/root/md-os/schemas")


def _parse_migrations() -> list[tuple[str, str]]:
    """Return sorted (version, SQL) pairs for all migrations.

    Version uses full filename stem (example: 001_initial).
    Prevents collision when multiple files share same numeric prefix.
    """
    files = sorted(SCHEMAS_DIR.glob("*.sql"))
    migrations: list[tuple[str, str]] = []
    for path in files:
        version = path.stem
        sql = path.read_text(encoding="utf-8")
        migrations.append((version, sql))
    return migrations


# ---------------------------------------------------------------------------
# Migration tracking table
# ---------------------------------------------------------------------------

MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS _migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def _ensure_migrations_table():
    with pg_cursor() as cur:
        cur.execute(MIGRATIONS_TABLE)


def _get_applied_versions() -> set[str]:
    _ensure_migrations_table()
    with pg_cursor() as cur:
        cur.execute("SELECT version FROM _migrations")
        return {row[0] for row in cur.fetchall()}


# ---------------------------------------------------------------------------
# Run pending migrations (idempotent — uses _migrations tracking table)
# ---------------------------------------------------------------------------

def run_pending_migrations() -> list[str]:
    """Apply all un-applied .sql files in schema order. Returns applied versions."""
    if not USE_POSTGRES:
        return []

    applied: set[str] = _get_applied_versions()
    pending: list[str] = []

    for version, sql in _parse_migrations():
        if version not in applied:
            pending.append(version)

    applied_versions: list[str] = []

    for version, sql in _parse_migrations():
        if version in pending:
            with pg_connection() as conn:
                cur = conn.cursor()
                # Split into statements, skip empty/comment-only
                for stmt in sqlparse.split(sql):
                    stripped = stmt.strip()
                    if not stripped or stripped.startswith("--"):
                        continue
                    cur.execute(stmt)
                cur.execute(
                    "INSERT INTO _migrations (version) VALUES (%s) ON CONFLICT DO NOTHING",
                    (version,),
                )
                conn.commit()
            applied_versions.append(version)

    return applied_versions


# ---------------------------------------------------------------------------
# Sync the in-memory store from Postgres (one-shot bootstrap for dev/test)
# ---------------------------------------------------------------------------

def sync_store_from_postgres():
    """Load Postgres data into the in-memory store (used during dev)."""
    if not USE_POSTGRES:
        return

    # Import here to avoid circular deps
    from .store import store

    def _load(bucket: str, query: str) -> None:
        with pg_cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            bucket_obj = store.bucket(bucket)
            bucket_obj.clear()
            for row in rows:
                item = dict(zip(cols, row))
                # Serialize JSONB columns
                for k, v in item.items():
                    if isinstance(v, str) and v.startswith("{"):
                        import json

                        try:
                            item[k] = json.loads(v)
                        except Exception:
                            pass
                bucket_obj[item["id"]] = item

    _load("companies", "SELECT * FROM companies")
    _load("projects", "SELECT * FROM projects")
    _load("agents", "SELECT * FROM agents")
    _load("agent_teams", "SELECT * FROM agent_teams")
    _load("workflows", "SELECT * FROM workflows")
    _load("workflow_runs", "SELECT * FROM workflow_runs")
    _load("tasks", "SELECT * FROM tasks")
    _load("approvals", "SELECT * FROM approvals")
    _load("orchestrator_cycles", "SELECT * FROM orchestrator_cycles")


# ---------------------------------------------------------------------------
# Init — call once at startup
# ---------------------------------------------------------------------------

def init_db() -> dict[str, Any]:
    """Initialize DB. Returns dict with backend and applied migrations."""
    if USE_POSTGRES:
        applied = run_pending_migrations()
        sync_store_from_postgres()
        return {"backend": "postgres", "migrations_applied": applied}
    return {"backend": "inmemory", "migrations_applied": []}