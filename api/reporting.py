from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

try:
    from store import store
except ImportError:
    from .store import store


REPORT_SCHEDULE_HOURS = 6


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def generate_agent_periodic_report(company_id: str) -> dict[str, Any]:
    runs = [r for r in store.agent_runs.values() if r.get("company_id") == company_id]

    status_counts = {
        "queued": 0,
        "running": 0,
        "waiting_approval": 0,
        "done": 0,
        "failed": 0,
    }
    for run in runs:
        status = run.get("status", "queued")
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1

    done_runs = [r for r in runs if r.get("status") == "done"]
    failed_runs = [r for r in runs if r.get("status") == "failed"]
    approval_blocked = [r for r in runs if r.get("status") == "waiting_approval"]

    return {
        "company_id": company_id,
        "generated_at": _iso_now(),
        "window_hours": REPORT_SCHEDULE_HOURS,
        "totals": {
            "agent_runs": len(runs),
            "done": len(done_runs),
            "failed": len(failed_runs),
            "waiting_approval": len(approval_blocked),
        },
        "status_counts": status_counts,
        "failed_run_ids": [r["id"] for r in failed_runs],
        "approval_blocked_run_ids": [r["id"] for r in approval_blocked],
    }


def _weekday_name() -> str:
    """Return Arabic day name for weekday."""
    names = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    # Monday = 0, Sunday = 6
    return names[datetime.now(UTC).weekday()]


def generate_ceo_daily_report(
    company_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
) -> dict[str, Any]:
    """Generate CEO daily synthesis report covering business modules."""
    now = datetime.now(UTC)
    today_date = now.date().isoformat()

    if period_end is None:
        period_end = f"{today_date}T23:59:59"
    if period_start is None:
        period_start = f"{today_date}T00:00:00"

    # ── Agent runs summary ────────────────────────────────────────────────
    runs = [r for r in store.agent_runs.values() if r.get("company_id") == company_id]
    total_runs = len(runs)
    done_runs = [r for r in runs if r.get("status") == "done"]
    failed_runs = [r for r in runs if r.get("status") == "failed"]
    waiting_approval = [r for r in runs if r.get("status") == "waiting_approval"]
    running_runs = [r for r in runs if r.get("status") == "running"]

    # ── Orchestrator cycles summary ────────────────────────────────────────
    cycles = [
        c for c in store.orchestrator_cycles.values()
        if c.get("company_id") == company_id
    ]
    done_cycles = [c for c in cycles if c.get("status") == "done"]
    failed_cycles = [c for c in cycles if c.get("status") == "failed"]

    # ── Task summary ────────────────────────────────────────────────────────
    tasks = [t for t in store.tasks.values() if t.get("company_id") == company_id]
    todo_tasks = [t for t in tasks if t.get("status") == "todo"]
    in_progress_tasks = [t for t in tasks if t.get("status") == "in_progress"]
    done_tasks = [t for t in tasks if t.get("status") == "done"]

    # ── Approval queue ─────────────────────────────────────────────────────
    pending_approvals = [
        a for a in store.approvals.values()
        if a.get("company_id") == company_id and a.get("status") == "pending"
    ]

    # ── Memory entries recent ───────────────────────────────────────────────
    memory_count = sum(
        1 for m in store.memory_entries.values()
        if m.get("company_id") == company_id
    )

    # ── Agents summary ─────────────────────────────────────────────────────
    active_agents = [
        a for a in store.agents.values()
        if a.get("company_id") == company_id and a.get("status") == "active"
    ]

    # ── Workflow runs ───────────────────────────────────────────────────────
    wf_runs = [
        w for w in store.workflow_runs.values()
        if _workflow_company_id(w) == company_id
    ]
    wf_done = [w for w in wf_runs if w.get("status") == "done"]
    wf_failed = [w for w in wf_runs if w.get("status") == "failed"]

    # ── Compose summary ─────────────────────────────────────────────────────
    success_rate = 0.0
    if total_runs > 0:
        success_rate = round(len(done_runs) / total_runs * 100, 1)

    day_name = _weekday_name()
    report_date = today_date
    greeting = f"التقرير اليومي — {day_name} ({report_date})"

    summary = {
        "date": today_date,
        "day_name": day_name,
        "greeting": greeting,
        "agent_runs": {
            "total": total_runs,
            "done": len(done_runs),
            "failed": len(failed_runs),
            "running": len(running_runs),
            "waiting_approval": len(waiting_approval),
            "success_rate_pct": success_rate,
            "failed_run_ids": [r["id"] for r in failed_runs[:5]],
            "approval_blocked_run_ids": [r["id"] for r in waiting_approval[:5]],
        },
        "orchestrator_cycles": {
            "total": len(cycles),
            "done": len(done_cycles),
            "failed": len(failed_cycles),
        },
        "tasks": {
            "total": len(tasks),
            "todo": len(todo_tasks),
            "in_progress": len(in_progress_tasks),
            "done": len(done_tasks),
            "todo_task_ids": [t["id"] for t in todo_tasks[:5]],
        },
        "approvals": {
            "pending_count": len(pending_approvals),
            "pending_ids": [a["id"] for a in pending_approvals[:10]],
        },
        "memory": {
            "total_entries": memory_count,
        },
        "agents": {
            "active_count": len(active_agents),
            "active_names": [a.get("name", "") for a in active_agents[:10]],
        },
        "workflows": {
            "total_runs": len(wf_runs),
            "done": len(wf_done),
            "failed": len(wf_failed),
        },
        "action_items": _build_action_items(
            pending_approvals, failed_runs, todo_tasks, failed_cycles
        ),
        "insights": _build_insights(
            total_runs, len(done_runs), len(failed_runs),
            len(tasks), len(in_progress_tasks),
            success_rate, len(active_agents)
        ),
    }

    return {
        "company_id": company_id,
        "generated_at": _iso_now(),
        "period_start": period_start,
        "period_end": period_end,
        "summary": summary,
    }


def _workflow_company_id(wf_run: dict[str, Any]) -> str | None:
    """Extract company_id from a workflow run or its linked workflow."""
    if "company_id" in wf_run:
        return wf_run.get("company_id")
    return None


def _build_action_items(
    pending_approvals: list[dict[str, Any]],
    failed_runs: list[dict[str, Any]],
    todo_tasks: list[dict[str, Any]],
    failed_cycles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build prioritized action items list."""
    items: list[dict[str, Any]] = []

    for a in pending_approvals[:5]:
        items.append({
            "type": "approval_pending",
            "priority": "high",
            "id": a["id"],
            "title": a.get("title", "طلب موافقة"),
            "category": a.get("category", ""),
            "created_at": a.get("created_at", ""),
        })

    for r in failed_runs[:5]:
        items.append({
            "type": "failed_agent_run",
            "priority": "high",
            "id": r["id"],
            "agent_id": r.get("agent_id", ""),
            "error": r.get("error", ""),
        })

    for t in todo_tasks[:5]:
        items.append({
            "type": "stale_task",
            "priority": "medium",
            "id": t["id"],
            "title": t.get("title", ""),
            "priority_level": t.get("priority", "medium"),
        })

    for c in failed_cycles[:3]:
        items.append({
            "type": "failed_cycle",
            "priority": "medium",
            "id": c["id"],
            "task_description": c.get("task_description", ""),
        })

    return items


def _build_insights(
    total_runs: int,
    done: int,
    failed: int,
    total_tasks: int,
    in_progress: int,
    success_rate: float,
    agent_count: int,
) -> list[str]:
    """Generate contextual insights from today's metrics."""
    insights: list[str] = []

    if total_runs == 0:
        insights.append("لا توجد عمليات وكلاء منفذة اليوم. النظام جاهز للعمل.")
    else:
        if failed > 0 and failed / total_runs > 0.3:
            insights.append(
                f"تحذير: {failed} من {total_runs} عمليات وكلاء فشلت. راجع السجلات."
            )
        if success_rate >= 80:
            insights.append(
                f"أداء ممتاز: نسبة النجاح {success_rate}% — الفريق يعمل بكفاءة."
            )
        elif success_rate >= 50:
            insights.append(
                f"تحتاج تحسين: نسبة النجاح {success_rate}% — راجع العمليات الفاشلة."
            )

    if in_progress > 0:
        insights.append(f"{in_progress} مهمة قيد التنفيذ. تابع التقدم.")

    if total_tasks > 10 and in_progress == 0:
        insights.append(
            "تنبيه: أكثر من 10 مهام معلقة بدون تقدم. راجع الأولويات."
        )

    if agent_count > 5:
        insights.append(
            f"{agent_count} وكلاء نشطين متاحين. استخدمهم بكفاءة."
        )

    if not insights:
        insights.append("النظام يعمل بشكل طبيعي. لا توجد مشاكل مكتشفة.")

    return insights
