#!/usr/bin/env python3
"""MD-OS Unified Stack Orchestrator

One command to run full stack cycle:
Hermes + GBrain + Codegraph + Antigravity + Multica + Paperclip + GitHub
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/root/md-os")
REPORT = ROOT / "reports" / "stack-unified-report.json"


def run(cmd: str, check: bool = False) -> tuple[int, str]:
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    out = (p.stdout or "") + (p.stderr or "")
    if check and p.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{out}")
    return p.returncode, out.strip()


def health() -> dict:
    checks = {}
    targets = {
        "hermes": "curl -fsS http://127.0.0.1:8061/health",
        "gbrain": "curl -fsS http://127.0.0.1:3132/health",
        "paperclip": "curl -fsS http://127.0.0.1:3100/api/health",
        "multica": "curl -fsS http://127.0.0.1:8080/health",
        "codegraph": "codegraph --version",
        "antigravity": "agy --version",
    }
    for k, cmd in targets.items():
        rc, out = run(cmd)
        checks[k] = {"ok": rc == 0, "output": out[:300]}
    return checks


def codegraph_gate() -> dict:
    rc, out = run("python3 /root/.hermes/profiles/newmain/scripts/md_os_integrated.py verify")
    return {"ok": rc == 0, "output": out[:1200]}


def test_gate() -> dict:
    rc, out = run("cd /root/md-os && python3 -m pytest tests/ -q")
    return {"ok": rc == 0, "output": out[-1500:]}


def multica_snapshot() -> dict:
    rc, out = run("docker exec multica-postgres-1 psql -U multica -d multica -t -c \"SELECT status, count(*) FROM agent GROUP BY status ORDER BY status;\"")
    return {"ok": rc == 0, "agents_by_status": out}


def gbrain_snapshot() -> dict:
    # keep thin: health only + known engine
    rc, out = run("curl -fsS http://127.0.0.1:3132/health")
    return {"ok": rc == 0, "health": out}


def main() -> int:
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": "adminnewtech/md-os",
        "branch": "feat/may26-full-data-bootstrap",
        "health": health(),
        "codegraph_gate": codegraph_gate(),
        "tests": test_gate(),
        "multica": multica_snapshot(),
        "gbrain": gbrain_snapshot(),
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # summary line for cron/ops
    ok = all(v.get("ok", False) for v in data["health"].values()) and data["tests"]["ok"] and data["codegraph_gate"]["ok"]
    print("STACK_UNIFIED_OK" if ok else "STACK_UNIFIED_DEGRADED")
    print(str(REPORT))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
