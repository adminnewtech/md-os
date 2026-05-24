"""
MD-OS Stack Orchestrator — Unified control plane for all 6 tools.

Routes:
  GET  /api/stack/status          → full health + metrics
  POST /api/stack/analyze         → Codegraph deep scan → hotspots
  POST /api/stack/run-cycle      → run full dev cycle
  GET  /api/stack/agents         → Multica agent snapshot
  GET  /api/stack/gbrain-query   → search GBrain memory
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from typing import Any

# ── HTTP helpers ────────────────────────────────────────────────────────────────

def http_get(url: str, timeout: int = 8) -> tuple[int, str]:
    p = subprocess.run(
        ["curl", "-fsS", "--max-time", str(timeout), url],
        capture_output=True, text=True,
    )
    return p.returncode, (p.stdout or "").strip()


def http_post_json(url: str, data: dict, timeout: int = 15) -> tuple[int, str]:
    p = subprocess.run(
        ["curl", "-fsS", "--max-time", str(timeout), "-X", "POST",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(data), url],
        capture_output=True, text=True,
    )
    return p.returncode, (p.stdout or "").strip()


def run_cmd(cmd: str, timeout: int = 30) -> tuple[int, str]:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or p.stderr or "").strip()


# ── Tool checks ────────────────────────────────────────────────────────────────

def check_hermes() -> dict[str, Any]:
    rc, out = http_get("http://127.0.0.1:8061/health")
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw": out[:200]}
    return {"ok": rc == 0, "data": data}


def check_gbrain() -> dict[str, Any]:
    rc, out = http_get("http://127.0.0.1:3132/health")
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw": out[:200]}
    return {"ok": rc == 0, "data": data}


def check_paperclip() -> dict[str, Any]:
    rc, out = http_get("http://127.0.0.1:3100/api/health")
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw": out[:200]}
    return {"ok": rc == 0, "data": data}


def check_multica() -> dict[str, Any]:
    rc, out = http_get("http://127.0.0.1:8080/health")
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw": out[:200]}
    # Also get agent count from postgres
    rc2, agents = run_cmd(
        "docker exec multica-postgres-1 psql -U multica -d multica -t -c "
        "\"SELECT status, count(*) FROM agent GROUP BY status ORDER BY status;\" 2>/dev/null"
    )
    return {
        "ok": rc == 0,
        "data": data,
        "agents_by_status": agents if rc2 == 0 else "",
    }


def check_codegraph() -> dict[str, Any]:
    rc, out = run_cmd("codegraph --version")
    return {"ok": rc == 0, "version": out}


def check_antigravity() -> dict[str, Any]:
    rc, out = run_cmd("agy --version")
    return {"ok": rc == 0, "version": out}


def check_md_api() -> dict[str, Any]:
    rc, out = http_get("http://127.0.0.1:3999/api/health")
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw": out[:200]}
    return {"ok": rc == 0, "data": data}


# ── Codegraph analysis ─────────────────────────────────────────────────────────

def codegraph_analyze(repo_path: str = "/root/md-os", limit: int = 50) -> dict[str, Any]:
    """Run Codegraph entity analysis and return hotspots."""
    import csv
    import io
    from pathlib import Path

    try:
        out_path = f"/tmp/cg_{datetime.now(timezone.utc).strftime('%s')}.csv"
        proc = subprocess.run(
            ["codegraph", repo_path, "--csv", out_path],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            return {"ok": False, "error": proc.stderr[:300]}

        # Parse CSV
        entities = []
        with open(out_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entities.append({
                    "name": row.get("name", ""),
                    "type": row.get("type", ""),
                    "full_path": row.get("full_path", ""),
                    "lines": int(row.get("lines", 0) or 0),
                    "links_in": int(row.get("links_in", 0) or 0),
                })

        # Top-linked files (high connectivity = core files)
        hotspots = sorted(
            [e for e in entities if e.get("links_in", 0) > 0 and e.get("type") == "module"],
            key=lambda e: e["links_in"],
            reverse=True,
        )[:15]

        return {
            "ok": True,
            "total_entities": len(entities),
            "hotspots": hotspots,
        }
    except Exception as ex:
        return {"ok": False, "error": str(ex)}


# ── Multica agent snapshot ─────────────────────────────────────────────────────

def multica_agent_snapshot() -> dict[str, Any]:
    """Query Multica DB for full agent + runtime state."""
    rc, out = run_cmd(
        "docker exec multica-postgres-1 psql -U multica -d multica -t -c \"\"\n        SELECT a.id, a.name, a.status, ar.name as runtime, ar.provider, a.updated_at\n        FROM agent a LEFT JOIN agent_runtime ar ON ar.id = a.runtime_id\n        ORDER BY a.updated_at DESC LIMIT 30;\" 2>/dev/null"
    )
    return {"ok": rc == 0, "agents": out}


# ── Full stack status ──────────────────────────────────────────────────────────

def get_full_status() -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "generated_at": now,
        "hermes": check_hermes(),
        "gbrain": check_gbrain(),
        "paperclip": check_paperclip(),
        "multica": check_multica(),
        "codegraph": check_codegraph(),
        "antigravity": check_antigravity(),
        "md_api": check_md_api(),
    }


def is_stack_healthy() -> bool:
    status = get_full_status()
    required = ["hermes", "gbrain", "paperclip", "multica", "codegraph", "md_api"]
    return all(status.get(k, {}).get("ok", False) for k in required)