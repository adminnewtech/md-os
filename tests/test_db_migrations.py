from __future__ import annotations

from pathlib import Path

from api import db


def test_parse_migrations_keeps_unique_version_per_file(tmp_path: Path, monkeypatch):
    (tmp_path / "001_initial.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "001_core_schema.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "002_seed_data.sql").write_text("SELECT 3;", encoding="utf-8")

    monkeypatch.setattr(db, "SCHEMAS_DIR", tmp_path)

    migrations = db._parse_migrations()
    versions = [version for version, _ in migrations]

    assert versions == ["001_core_schema", "001_initial", "002_seed_data"]
    assert len(set(versions)) == 3
