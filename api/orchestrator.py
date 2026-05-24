"""
MD-OS Hermes Orchestrator Service
=================================
Plan → Delegate → Monitor → Report

Given a task description and a set of available agents, the orchestrator:
1. Plans  — decomposes into sub-tasks, assigns to agents
2. Delegates — creates agent_runs, dispatches
3. Monitors — tracks state transitions until terminal
4. Reports — aggregates results into a summary

Designed to run in a background task (FastAPI BackgroundTasks or cron).
Thread-safe for concurrent orchestrator instances.
"""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

try:
    from models import AgentRunCreate
    from services import create_agent_run, transition_agent_run, get_agent_run
    from store import store
except ImportError:
    from .models import AgentRunCreate
    from .services import create_agent_run, transition_agent_run, get_agent_run
    from .store import store


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class OrchestratorStatus:
    PLANNING = "planning"
    DELEGATING = "delegating"
    MONITORING = "monitoring"
    DONE = "done"
    FAILED = "failed"


class OrchestratorCycle:
    """An orchestration cycle — one planning → delegation → monitoring pass."""

    def __init__(
        self,
        task_description: str,
        company_id: str,
        agent_ids: list[str],
        context: dict[str, Any] | None = None,
        max_parallel: int = 4,
    ) -> None:
        self.id = str(uuid4())
        self.task_description = task_description
        self.company_id = company_id
        self.agent_ids = agent_ids
        self.context = context or {}
        self.max_parallel = max_parallel

        self.status = OrchestratorStatus.PLANNING
        self.plan: list[dict[str, Any]] = []
        self.agent_runs: list[str] = []  # run IDs
        self.result: dict[str, Any] = {}
        self.error: str | None = None
        self.created_at = time.time()
        self.finished_at: float | None = None

        # Persist in store
        store.orchestrator_cycles[self.id] = self._to_dict()

    def _to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_description": self.task_description,
            "company_id": self.company_id,
            "agent_ids": self.agent_ids,
            "context": self.context,
            "max_parallel": self.max_parallel,
            "status": self.status,
            "plan": self.plan,
            "agent_runs": self.agent_runs,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }

    def _save(self) -> None:
        store.orchestrator_cycles[self.id] = self._to_dict()


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

def _decompose_task(description: str, context: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Decompose a task description into ordered sub-tasks.
    Uses a simple heuristic-based planner:
    - If description contains keywords, generate structured plan
    - Otherwise use generic "process and report" plan

    In production this would call a model for planning.
    Here we produce a deterministic fallback plan.
    """
    desc_lower = description.lower()

    # Heuristic: CRM-style task
    if any(k in desc_lower for k in ["crm", "lead", "contact", "deal", "pipeline"]):
        return [
            {"step": 1, "action": "fetch", "target": "contacts", "agent_role": "crm-agent"},
            {"step": 2, "action": "analyze", "target": "leads", "agent_role": "analyst-agent"},
            {"step": 3, "action": "prioritize", "target": "pipeline", "agent_role": "crm-agent"},
        ]

    # Heuristic: finance task
    if any(k in desc_lower for k in ["finance", "invoice", "budget", "expense", "cashflow"]):
        return [
            {"step": 1, "action": "fetch", "target": "transactions", "agent_role": "finance-agent"},
            {"step": 2, "action": "calculate", "target": "budget", "agent_role": "finance-agent"},
            {"step": 3, "action": "report", "target": "cashflow", "agent_role": "analyst-agent"},
        ]

    # Heuristic: support task
    if any(k in desc_lower for k in ["support", "ticket", "sla", "escalation"]):
        return [
            {"step": 1, "action": "fetch", "target": "open_tickets", "agent_role": "support-agent"},
            {"step": 2, "action": "categorize", "target": "priority", "agent_role": "support-agent"},
            {"step": 3, "action": "escalate", "target": "sla_breach", "agent_role": "manager-agent"},
        ]

    # Heuristic: inventory task
    if any(k in desc_lower for k in ["inventory", "stock", "sku", "supplier", "reorder"]):
        return [
            {"step": 1, "action": "scan", "target": "stock_levels", "agent_role": "inventory-agent"},
            {"step": 2, "action": "detect", "target": "low_stock", "agent_role": "inventory-agent"},
            {"step": 3, "action": "order", "target": "reorder", "agent_role": "manager-agent"},
        ]

    # Heuristic: HR task
    if any(k in desc_lower for k in ["hr", "employee", "recruit", "onboard"]):
        return [
            {"step": 1, "action": "review", "target": "pipeline", "agent_role": "hr-agent"},
            {"step": 2, "action": "screen", "target": "candidates", "agent_role": "hr-agent"},
            {"step": 3, "action": "offer", "target": "selected", "agent_role": "manager-agent"},
        ]

    # Heuristic: sales task
    if any(k in desc_lower for k in ["sales", "quote", "proposal", "deal", "conversion"]):
        return [
            {"step": 1, "action": "identify", "target": "prospects", "agent_role": "sales-agent"},
            {"step": 2, "action": "prepare", "target": "quote", "agent_role": "sales-agent"},
            {"step": 3, "action": "follow_up", "target": "deals", "agent_role": "sales-agent"},
        ]

    # Heuristic: general multi-agent task
    if any(k in desc_lower for k in ["research", "analyze", "report", "audit"]):
        return [
            {"step": 1, "action": "gather", "target": "data", "agent_role": "researcher-agent"},
            {"step": 2, "action": "analyze", "target": "findings", "agent_role": "analyst-agent"},
            {"step": 3, "action": "summarize", "target": "report", "agent_role": "writer-agent"},
        ]

    # Fallback: generic single-pass
    return [
        {"step": 1, "action": "process", "target": "task", "agent_role": "general-agent"},
    ]


def _assign_agents(plan: list[dict[str, Any]], available_agent_ids: list[str]) -> list[dict[str, Any]]:
    """
    Match plan steps to available agents by role.
    Assigns the first matching agent from the available list.
    """
    # Build role -> agent_id mapping from store
    role_to_agent: dict[str, str] = {}
    for agent_id in available_agent_ids:
        agent = store.agents.get(agent_id)
        if agent:
            role = agent.get("role", "")
            if role and role not in role_to_agent:
                role_to_agent[role] = agent_id

    # Also build a pool of all agents for fallback
    all_agent_ids = list(available_agent_ids)
    if not all_agent_ids:
        all_agent_ids = list(store.agents.keys())

    assigned = []
    for step in plan:
        role = step.get("agent_role", "general-agent")
        agent_id = role_to_agent.get(role, all_agent_ids[0] if all_agent_ids else "")
        assigned.append({**step, "agent_id": agent_id})

    return assigned


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------

def _delegate_plan(cycle: OrchestratorCycle) -> list[str]:
    """
    Create agent_runs for each plan step.
    Returns list of run IDs.
    """
    run_ids: list[str] = []
    for step in cycle.plan:
        agent_id = step.get("agent_id", "")
        if not agent_id:
            continue

        payload = AgentRunCreate(
            agent_id=agent_id,
            company_id=cycle.company_id,
            input={
                "task_description": cycle.task_description,
                "step": step,
                "context": cycle.context,
            },
        )
        run = create_agent_run(payload.model_dump())
        run_ids.append(run["id"])

        # Transition to running immediately (orchestrator dispatches)
        transition_agent_run(run["id"], "running")
        # Simulate worker completion in same cycle (MVP orchestrator)
        transition_agent_run(
            run["id"],
            "done",
            output={
                "summary": f"completed {step.get('action')} {step.get('target')}",
                "step": step,
            },
        )

    return run_ids


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------

def _monitor_until_done(run_ids: list[str], timeout: float = 30.0) -> dict[str, Any]:
    """
    Poll agent_runs until all reach terminal state (done/failed).
    Returns aggregated output from all runs.
    Returns quickly if all already terminal.
    """
    start = time.time()
    results: list[dict[str, Any]] = []
    pending = set(run_ids)

    while pending and (time.time() - start) < timeout:
        for run_id in list(pending):
            run = get_agent_run(run_id)
            if run is None:
                pending.discard(run_id)
                continue
            status = run.get("status", "queued")
            if status in ("done", "failed"):
                results.append(run)
                pending.discard(run_id)
            elif status == "waiting_approval":
                # Don't block on approval — include as-is with warning
                results.append({**run, "_blocked": "waiting_approval"})
                pending.discard(run_id)
        if pending:
            time.sleep(0.1)

    # Include any still-pending runs
    for run_id in pending:
        run = get_agent_run(run_id)
        if run:
            results.append({**run, "_incomplete": True})

    return {"runs": results, "total": len(run_ids), "completed": len(results) - len(pending)}


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _generate_report(cycle: OrchestratorCycle, monitor_result: dict[str, Any]) -> dict[str, Any]:
    """Aggregate results into a structured report."""
    runs = monitor_result.get("runs", [])

    succeeded = [r for r in runs if r.get("status") == "done"]
    failed = [r for r in runs if r.get("status") == "failed"]
    blocked = [r for r in runs if r.get("_blocked") == "waiting_approval"]
    incomplete = [r for r in runs if r.get("_incomplete")]

    report = {
        "cycle_id": cycle.id,
        "task_description": cycle.task_description,
        "plan_summary": [
            f"Step {s['step']}: {s['action']} {s['target']} ({s.get('agent_id', '?')[:8]})"
            for s in cycle.plan
        ],
        "agent_runs": len(runs),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "blocked_on_approval": len(blocked),
        "incomplete": len(incomplete),
        "total_duration_s": round(time.time() - cycle.created_at, 2),
        "details": [
            {
                "run_id": r["id"],
                "agent_id": r.get("agent_id"),
                "status": r.get("status"),
                "output": r.get("output", {}),
                "error": r.get("error"),
            }
            for r in runs
        ],
        "status": "success" if not failed and not incomplete else ("partial" if blocked else ("failed" if failed else "incomplete")),
    }

    return report


# ---------------------------------------------------------------------------
# Main Orchestrator API
# ---------------------------------------------------------------------------

def create_cycle(
    task_description: str,
    company_id: str,
    agent_ids: list[str],
    context: dict[str, Any] | None = None,
    max_parallel: int = 4,
) -> dict[str, Any]:
    """Create a new orchestration cycle and return its initial state."""
    cycle = OrchestratorCycle(
        task_description=task_description,
        company_id=company_id,
        agent_ids=agent_ids,
        context=context,
        max_parallel=max_parallel,
    )
    return cycle._to_dict()


def run_cycle(cycle_id: str) -> dict[str, Any]:
    """
    Execute a full orchestration cycle: plan → delegate → monitor → report.
    Returns the cycle with final result.
    """
    cycle_dict = store.orchestrator_cycles.get(cycle_id)
    if cycle_dict is None:
        raise ValueError(f"Cycle not found: {cycle_id}")

    cycle = OrchestratorCycle.__new__(OrchestratorCycle)
    for k, v in cycle_dict.items():
        setattr(cycle, k, v)

    try:
        # ── 1. PLAN ──────────────────────────────────────────────
        cycle.status = OrchestratorStatus.PLANNING
        cycle._save()

        raw_plan = _decompose_task(cycle.task_description, cycle.context)
        cycle.plan = _assign_agents(raw_plan, cycle.agent_ids)
        cycle.status = OrchestratorStatus.DELEGATING
        cycle._save()

        # ── 2. DELEGATE ─────────────────────────────────────────
        cycle.agent_runs = _delegate_plan(cycle)
        cycle.status = OrchestratorStatus.MONITORING
        cycle._save()

        # ── 3. MONITOR ─────────────────────────────────────────
        monitor_result = _monitor_until_done(cycle.agent_runs, timeout=20.0)

        # ── 4. REPORT ──────────────────────────────────────────
        cycle.result = _generate_report(cycle, monitor_result)
        cycle.status = OrchestratorStatus.DONE
        cycle.finished_at = time.time()
        cycle._save()

    except Exception as exc:
        cycle.status = OrchestratorStatus.FAILED
        cycle.error = str(exc)
        cycle.finished_at = time.time()
        cycle._save()
        raise

    return cycle._to_dict()


def get_cycle(cycle_id: str) -> dict[str, Any] | None:
    return store.orchestrator_cycles.get(cycle_id)


def list_cycles(company_id: str | None = None) -> list[dict[str, Any]]:
    cycles = list(store.orchestrator_cycles.values())
    if company_id:
        cycles = [c for c in cycles if c.get("company_id") == company_id]
    return cycles


def get_cycle_report(cycle_id: str) -> dict[str, Any] | None:
    """Get just the report portion of a cycle."""
    cycle = store.orchestrator_cycles.get(cycle_id)
    if cycle is None:
        return None
    return cycle.get("result", {})