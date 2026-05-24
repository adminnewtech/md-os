from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from models import Agent, Company, Workflow
    from store import store
except ImportError:
    from .models import Agent, Company, Workflow
    from .store import store

DEFAULT_COMPANY_ID = "00000000-0000-0000-0000-000000000001"
ROOT = Path("/root/md-os")


def seed_default_company() -> dict[str, Any]:
    company = Company(
        id=DEFAULT_COMPANY_ID,
        name="MD Platform (NewTech Kuwait)",
        industry="ai-company-operating-system",
        status="active",
        settings={"country": "KW", "currency": "KWD", "locale": "ar-KW"},
    ).model_dump()
    store.companies.setdefault(DEFAULT_COMPANY_ID, company)
    return store.companies[DEFAULT_COMPANY_ID]


def _load_json_files(directory: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        payload["_source_file"] = str(path)
        rows.append(payload)
    return rows


def _stable_import_id(prefix: str, source_file: str) -> str:
    stem = Path(source_file).stem
    return f"{prefix}:{stem}"


def seed_agents(company_id: str = DEFAULT_COMPANY_ID) -> int:
    count = 0
    for definition in _load_json_files(ROOT / "agents"):
        source_file = definition.pop("_source_file")
        agent_id = _stable_import_id("agent", source_file)
        config = dict(definition)
        config["source_file"] = source_file
        agent = Agent(
            id=agent_id,
            company_id=company_id,
            name=definition["name"],
            role=definition["role"],
            mission=definition["mission"],
            config=config,
            status="active",
        ).model_dump()
        if agent_id not in store.agents:
            count += 1
        store.agents[agent_id] = agent
    return count


def seed_workflows(company_id: str = DEFAULT_COMPANY_ID) -> int:
    count = 0
    for definition in _load_json_files(ROOT / "workflows"):
        source_file = definition.pop("_source_file")
        workflow_id = definition.get("id") or _stable_import_id("workflow", source_file)
        graph = {"nodes": definition.get("nodes", []), "source_file": source_file}
        workflow = Workflow(
            id=workflow_id,
            company_id=company_id,
            name=definition["name"],
            trigger=definition["trigger"],
            graph=graph,
            status="active",
        ).model_dump()
        if workflow_id not in store.workflows:
            count += 1
        store.workflows[workflow_id] = workflow
    return count


def bootstrap_seed_data() -> dict[str, int]:
    seed_default_company()
    agents = seed_agents()
    workflows = seed_workflows()
    return {"companies": len(store.companies), "agents_imported": agents, "workflows_imported": workflows}