from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from agent_state_machine import can_transition
    from models import (
        AgentRun, Approval, AuditLog, MemoryEntry, WorkflowRun,
        Contact, Lead, Deal, DealActivity,
        Ticket, TicketNote, Macro, CustomerHealth,
        Invoice, Payment,
        SKU, StockMovement,
        ApiCredential, WebhookConfig, ApiLog,
        Employee, RecruitmentPipeline,
        Vehicle, Shipment,
        Quote, Proposal, DealDesk,
    )
    from store import store
except ImportError:
    from .agent_state_machine import can_transition
    from .models import (
        AgentRun, Approval, AuditLog, MemoryEntry, WorkflowRun,
        Contact, Lead, Deal, DealActivity,
        Ticket, TicketNote, Macro, CustomerHealth,
        Invoice, Payment,
        SKU, StockMovement,
        ApiCredential, WebhookConfig, ApiLog,
        Employee, RecruitmentPipeline,
        Vehicle, Shipment,
        Quote, Proposal, DealDesk,
    )
    from .store import store


def create_item(bucket_name: str, item: dict[str, Any]) -> dict[str, Any]:
    bucket = store.bucket(bucket_name)
    bucket[item["id"]] = item
    return item


def list_items(bucket_name: str) -> list[dict[str, Any]]:
    return list(store.bucket(bucket_name).values())


def get_item(bucket_name: str, item_id: str) -> dict[str, Any] | None:
    return store.bucket(bucket_name).get(item_id)


def update_item(bucket_name: str, item_id: str, values: dict[str, Any]) -> dict[str, Any] | None:
    item = get_item(bucket_name, item_id)
    if item is None:
        return None
    item.update(values)
    return item


def log_audit(
    company_id: str | None,
    actor_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any]:
    entry = AuditLog(
        company_id=company_id,
        actor_type="user",
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
    ).model_dump()
    store.audit_logs.append(entry)
    return entry


def create_workflow_run(workflow_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    run = WorkflowRun(workflow_id=workflow_id, input=input_payload)
    store.workflow_runs[run.id] = run.model_dump()
    return store.workflow_runs[run.id]


def decide_approval(
    approval_id: str, decision: str, decided_by: str
) -> dict[str, Any] | None:
    approval = store.approvals.get(approval_id)
    if approval is None:
        return None
    approval["status"] = decision
    approval["decided_by"] = decided_by

    # If this approval was linked to an agent run, resume or fail it
    agent_run = None
    for run_id, run in store.agent_runs.items():
        if run.get("waiting_approval_id") == approval_id:
            agent_run = run
            break
    if agent_run:
        if decision == "approved":
            agent_run["status"] = "running"
            agent_run["waiting_approval_id"] = None
        else:
            agent_run["status"] = "failed"
            agent_run["error"] = "approval rejected"
            agent_run["waiting_approval_id"] = None

    return {"approval": approval, "agent_run": agent_run}


def create_approval(payload: dict[str, Any]) -> dict[str, Any]:
    approval = Approval(**payload).model_dump()
    store.approvals[approval["id"]] = approval
    return approval


def create_agent_run(payload: dict[str, Any]) -> dict[str, Any]:
    run = AgentRun(**payload).model_dump()
    store.agent_runs[run["id"]] = run
    return run


def transition_agent_run(
    run_id: str,
    to_status: str,
    output: dict[str, Any] | None = None,
    error: str | None = None,
    waiting_approval_id: str | None = None,
) -> dict[str, Any] | None:
    run = store.agent_runs.get(run_id)
    if run is None:
        return None
    if not can_transition(run, to_status):
        return None

    run["status"] = to_status
    if output is not None:
        run["output"] = output
    if error is not None:
        run["error"] = error
    if waiting_approval_id is not None:
        run["waiting_approval_id"] = waiting_approval_id
    return run


def get_agent_run(run_id: str) -> dict[str, Any] | None:
    return store.agent_runs.get(run_id)


def list_agent_runs() -> list[dict[str, Any]]:
    return list(store.agent_runs.values())


def create_memory_entry(payload: dict[str, Any]) -> dict[str, Any]:
    entry = MemoryEntry(**payload).model_dump()
    store.memory_entries[entry["id"]] = entry
    return entry


def get_memory_entry(entry_id: str) -> dict[str, Any] | None:
    return store.memory_entries.get(entry_id)


def list_memory_entries(company_id: str | None = None, agent_id: str | None = None) -> list[dict[str, Any]]:
    items = list(store.memory_entries.values())
    if company_id is not None:
        items = [item for item in items if item.get("company_id") == company_id]
    if agent_id is not None:
        items = [item for item in items if item.get("agent_id") == agent_id]
    return items


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def search_memory_entries(
    company_id: str,
    embedding: list[float],
    limit: int = 5,
    agent_id: str | None = None,
    key_prefix: str | None = None,
) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for item in list_memory_entries(company_id=company_id, agent_id=agent_id):
        if key_prefix is not None and not item.get("key", "").startswith(key_prefix):
            continue
        score = _cosine_similarity(embedding, item.get("embedding", []))
        scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {**item, "score": round(score, 6)}
        for score, item in scored[:limit]
    ]


# ── CRM Services ──────────────────────────────────────────────────────────────

def create_contact(payload: dict[str, Any]) -> dict[str, Any]:
    item = Contact(**payload).model_dump()
    store.contacts[item["id"]] = item
    return item


def create_lead(payload: dict[str, Any]) -> dict[str, Any]:
    item = Lead(**payload).model_dump()
    store.leads[item["id"]] = item
    return item


def convert_lead_to_deal(lead_id: str) -> dict[str, Any] | None:
    lead = store.leads.get(lead_id)
    if lead is None or lead.get("status") == "converted":
        return None

    from datetime import datetime, timezone

    deal = Deal(
        title=lead.get("title", ""),
        contact_id=lead.get("contact_id"),
        lead_id=lead_id,
        stage="prospecting",
        probability=10,
        company_id=lead["company_id"],
        workspace_id=lead.get("workspace_id", "default"),
        custom_fields=lead.get("custom_fields", {}),
    ).model_dump()

    store.deals[deal["id"]] = deal

    lead["status"] = "converted"
    lead["converted_at"] = datetime.now(timezone.utc).isoformat()
    lead["converted_to_deal_id"] = deal["id"]

    return {"lead": lead, "deal": deal}


def create_deal(payload: dict[str, Any]) -> dict[str, Any]:
    item = Deal(**payload).model_dump()
    store.deals[item["id"]] = item
    return item


def update_deal_stage(
    deal_id: str, new_stage: str, closed_at: str | None = None
) -> dict[str, Any] | None:
    deal = store.deals.get(deal_id)
    if deal is None:
        return None
    deal["stage"] = new_stage
    if new_stage in ("closed_won", "closed_lost"):
        deal["closed_at"] = closed_at
    return deal


def create_deal_activity(payload: dict[str, Any]) -> dict[str, Any]:
    item = DealActivity(**payload).model_dump()
    store.deal_activities[item["id"]] = item
    return item


def get_crm_pipeline(company_id: str) -> dict[str, Any]:
    """Aggregate deal counts and values by stage for a company."""
    stages = [
        "prospecting", "qualification", "proposal",
        "negotiation", "closed_won", "closed_lost",
    ]
    pipeline = {}
    total_value = 0.0

    for stage in stages:
        stage_deals = [
            d for d in store.deals.values()
            if d.get("company_id") == company_id and d.get("stage") == stage
        ]
        count = len(stage_deals)
        value = sum(d.get("value", 0) for d in stage_deals)
        pipeline[stage] = {"count": count, "value": value}
        if stage not in ("closed_lost",):
            total_value += value

    active_deals = [
        d for d in store.deals.values()
        if d.get("company_id") == company_id and d.get("stage") not in ("closed_won", "closed_lost")
    ]
    won_deals = [
        d for d in store.deals.values()
        if d.get("company_id") == company_id and d.get("stage") == "closed_won"
    ]

    return {
        "company_id": company_id,
        "pipeline": pipeline,
        "total_active_value": round(total_value, 2),
        "active_deals_count": len(active_deals),
        "closed_won_count": len(won_deals),
        "closed_won_value": round(sum(d.get("value", 0) for d in won_deals), 2),
    }


# ── Support Services ──────────────────────────────────────────────────────────

SLA_HOURS = {
    "low": {"response": 24, "resolution": 168},
    "medium": {"response": 8, "resolution": 72},
    "high": {"response": 2, "resolution": 24},
    "urgent": {"response": 1, "resolution": 8},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sla_deadlines(priority: str) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    sla = SLA_HOURS.get(priority, SLA_HOURS["medium"])
    return {
        "sla_response_deadline": (now + timedelta(hours=sla["response"])).isoformat(),
        "sla_resolution_deadline": (now + timedelta(hours=sla["resolution"])).isoformat(),
    }


def get_ticket(ticket_id: str) -> dict[str, Any] | None:
    return store.tickets.get(ticket_id)


def list_tickets(
    company_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
) -> list[dict[str, Any]]:
    tickets = list(store.tickets.values())
    if company_id is not None:
        tickets = [t for t in tickets if t.get("company_id") == company_id]
    if status is not None:
        tickets = [t for t in tickets if t.get("status") == status]
    if priority is not None:
        tickets = [t for t in tickets if t.get("priority") == priority]
    return tickets


def create_ticket(payload: dict[str, Any]) -> dict[str, Any]:
    item = Ticket(**payload).model_dump()
    item.update(_sla_deadlines(item["priority"]))
    store.tickets[item["id"]] = item
    return item


def update_ticket(ticket_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    ticket = store.tickets.get(ticket_id)
    if ticket is None:
        return None
    for key, value in payload.items():
        if value is not None:
            ticket[key] = value
    if ticket.get("status") == "resolved" and ticket.get("resolved_at") is None:
        ticket["resolved_at"] = _now_iso()
    if ticket.get("status") == "closed" and ticket.get("closed_at") is None:
        ticket["closed_at"] = _now_iso()
    return ticket


def close_ticket(ticket_id: str, resolution_notes: str | None = None) -> dict[str, Any] | None:
    values: dict[str, Any] = {"status": "closed"}
    if resolution_notes is not None:
        values["resolution_notes"] = resolution_notes
    closed = update_ticket(ticket_id, values)
    if closed is not None and closed.get("resolved_at") is None:
        closed["resolved_at"] = _now_iso()
    return closed


def create_ticket_note(payload: dict[str, Any], company_id: str, actor_id: str | None) -> dict[str, Any]:
    item = TicketNote(**payload, company_id=company_id, created_by=actor_id).model_dump()
    store.ticket_notes[item["id"]] = item
    return item


def add_ticket_note(payload: dict[str, Any]) -> dict[str, Any]:
    ticket = store.tickets.get(payload["ticket_id"])
    if ticket is None:
        raise ValueError("ticket not found")
    return create_ticket_note(
        {"ticket_id": payload["ticket_id"], "content": payload["content"], "is_internal": payload.get("is_internal", False)},
        company_id=ticket["company_id"],
        actor_id=payload.get("created_by"),
    )


def list_ticket_notes(ticket_id: str) -> list[dict[str, Any]]:
    return [note for note in store.ticket_notes.values() if note.get("ticket_id") == ticket_id]


def create_macro(payload: dict[str, Any]) -> dict[str, Any]:
    item = Macro(**payload).model_dump()
    store.macros[item["id"]] = item
    return item


def get_macro(macro_id: str) -> dict[str, Any] | None:
    return store.macros.get(macro_id)


def list_macros(company_id: str | None = None, active_only: bool = False) -> list[dict[str, Any]]:
    macros = list(store.macros.values())
    if company_id is not None:
        macros = [m for m in macros if m.get("company_id") == company_id]
    if active_only:
        macros = [m for m in macros if m.get("is_active") is True]
    return macros


def update_macro(macro_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    macro = store.macros.get(macro_id)
    if macro is None:
        return None
    for key, value in payload.items():
        if value is not None:
            macro[key] = value
    return macro


def upsert_customer_health(payload: dict[str, Any]) -> dict[str, Any]:
    existing = next(
        (
            item for item in store.customer_health.values()
            if item.get("company_id") == payload["company_id"] and item.get("contact_id") == payload["contact_id"]
        ),
        None,
    )
    if existing:
        existing.update(CustomerHealth(**{**existing, **payload}).model_dump())
        existing["updated_at"] = _now_iso()
        return existing
    item = CustomerHealth(**payload).model_dump()
    item["updated_at"] = _now_iso()
    store.customer_health[item["id"]] = item
    return item


def update_customer_health(payload: dict[str, Any]) -> dict[str, Any]:
    return upsert_customer_health(payload)


def get_customer_health(contact_id: str) -> dict[str, Any] | None:
    return next(
        (item for item in store.customer_health.values() if item.get("contact_id") == contact_id),
        None,
    )


def get_support_summary(company_id: str) -> dict[str, Any]:
    tickets = [t for t in store.tickets.values() if t.get("company_id") == company_id]
    health = [h for h in store.customer_health.values() if h.get("company_id") == company_id]
    return {
        "company_id": company_id,
        "ticket_counts": {
            "total": len(tickets),
            "open": sum(1 for t in tickets if t.get("status") == "open"),
            "in_progress": sum(1 for t in tickets if t.get("status") == "in_progress"),
            "pending": sum(1 for t in tickets if t.get("status") == "pending"),
            "resolved": sum(1 for t in tickets if t.get("status") == "resolved"),
            "closed": sum(1 for t in tickets if t.get("status") == "closed"),
            "urgent": sum(1 for t in tickets if t.get("priority") == "urgent"),
        },
        "customer_health": {
            "tracked": len(health),
            "high_risk": sum(1 for h in health if h.get("risk_level") == "high"),
            "average_score": round(sum(h.get("health_score", 0) for h in health) / len(health), 2) if health else 0,
        },
        "macro_count": sum(1 for m in store.macros.values() if m.get("company_id") == company_id and m.get("is_active")),
    }


# ── Finance Services ──────────────────────────────────────────────────────────────

def create_invoice(payload: dict[str, Any]) -> dict[str, Any]:
    item = Invoice(**payload).model_dump()
    item["paid_amount"] = 0.0
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    item["updated_at"] = item["created_at"]
    store.invoices[item["id"]] = item
    return item


def get_invoice(invoice_id: str) -> dict[str, Any] | None:
    return store.invoices.get(invoice_id)


def update_invoice(invoice_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    invoice = store.invoices.get(invoice_id)
    if invoice is None:
        return None
    for key, value in payload.items():
        if value is not None:
            invoice[key] = value
    from datetime import datetime, timezone
    invoice["updated_at"] = datetime.now(timezone.utc).isoformat()
    return invoice


def list_invoices(
    company_id: str,
    status: str | None = None,
    customer_id: str | None = None,
) -> list[dict[str, Any]]:
    invoices = [inv for inv in store.invoices.values() if inv.get("company_id") == company_id]
    if status is not None:
        invoices = [inv for inv in invoices if inv.get("status") == status]
    if customer_id is not None:
        invoices = [inv for inv in invoices if inv.get("customer_id") == customer_id]
    return invoices


def get_invoices_aging_summary(company_id: str) -> dict[str, Any]:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    outstanding_invoices = [
        inv for inv in store.invoices.values()
        if inv.get("company_id") == company_id
        and inv.get("status") in ("sent", "overdue")
    ]
    total_outstanding = sum(inv.get("total_amount", 0) for inv in outstanding_invoices)
    return {
        "company_id": company_id,
        "total_outstanding": round(total_outstanding, 2),
        "count": len(outstanding_invoices),
    }


def create_payment(payload: dict[str, Any]) -> dict[str, Any]:
    item = Payment(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    store.payments[item["id"]] = item

    # Update invoice paid_amount and check if fully paid
    invoice = store.invoices.get(item["invoice_id"])
    if invoice:
        invoice["paid_amount"] = invoice.get("paid_amount", 0) + item["amount"]
        if invoice["paid_amount"] >= invoice["total_amount"]:
            invoice["status"] = "paid"
        invoice["updated_at"] = datetime.now(timezone.utc).isoformat()

    return item


def list_payments_for_invoice(invoice_id: str) -> list[dict[str, Any]]:
    return [p for p in store.payments.values() if p.get("invoice_id") == invoice_id]


# ── Inventory Services ─────────────────────────────────────────────────────────────

def create_sku(payload: dict[str, Any]) -> dict[str, Any]:
    item = SKU(**payload).model_dump()
    from datetime import datetime, timezone
    item["updated_at"] = datetime.now(timezone.utc).isoformat()
    store.skus[item["id"]] = item
    return item


def get_sku(sku_id: str) -> dict[str, Any] | None:
    return store.skus.get(sku_id)


def update_sku(sku_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    sku = store.skus.get(sku_id)
    if sku is None:
        return None
    for key, value in payload.items():
        if value is not None:
            sku[key] = value
    from datetime import datetime, timezone
    sku["updated_at"] = datetime.now(timezone.utc).isoformat()
    return sku


def list_skus(
    company_id: str,
    category: str | None = None,
    status: str | None = None,
    low_stock_only: bool = False,
) -> list[dict[str, Any]]:
    skus = [s for s in store.skus.values() if s.get("company_id") == company_id]
    if category is not None:
        skus = [s for s in skus if s.get("category") == category]
    if status is not None:
        skus = [s for s in skus if s.get("status") == status]
    if low_stock_only:
        skus = [s for s in skus if s.get("quantity_on_hand", 0) <= s.get("reorder_point", 0)]
    return skus


def create_stock_movement(payload: dict[str, Any]) -> dict[str, Any]:
    movement = StockMovement(**payload).model_dump()
    from datetime import datetime, timezone
    movement["created_at"] = datetime.now(timezone.utc).isoformat()
    store.stock_movements[movement["id"]] = movement

    sku = store.skus.get(movement["sku_id"])
    if sku is None:
        raise ValueError("SKU not found")

    qty = movement["quantity"]
    if movement["movement_type"] == "in":
        sku["quantity_on_hand"] = sku.get("quantity_on_hand", 0) + qty
    elif movement["movement_type"] == "out":
        if sku.get("quantity_on_hand", 0) < qty:
            raise ValueError("insufficient stock")
        sku["quantity_on_hand"] = sku.get("quantity_on_hand", 0) - qty
    elif movement["movement_type"] == "adjustment":
        sku["quantity_on_hand"] = qty

    sku["updated_at"] = datetime.now(timezone.utc).isoformat()
    return movement


def get_inventory_summary(company_id: str) -> dict[str, Any]:
    skus = [s for s in store.skus.values() if s.get("company_id") == company_id]
    low_stock = [s for s in skus if s.get("quantity_on_hand", 0) <= s.get("reorder_point", 0)]
    return {
        "company_id": company_id,
        "total_skus": len(skus),
        "low_stock_count": len(low_stock),
        "low_stock_skus": [{"sku_code": s["sku_code"], "name": s["name"], "quantity_on_hand": s["quantity_on_hand"]} for s in low_stock],
        "total_quantity_on_hand": sum(s.get("quantity_on_hand", 0) for s in skus),
    }


# ── API Connector Services ────────────────────────────────────────────────────

def create_api_credential(payload: dict[str, Any]) -> dict[str, Any]:
    item = ApiCredential(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    store.api_credentials[item["id"]] = item
    return item


def get_api_credential(cred_id: str) -> dict[str, Any] | None:
    return store.api_credentials.get(cred_id)


def list_api_credentials(company_id: str, provider: str | None = None) -> list[dict[str, Any]]:
    creds = [c for c in store.api_credentials.values() if c.get("company_id") == company_id]
    if provider:
        creds = [c for c in creds if c.get("provider") == provider]
    return creds


def delete_api_credential(cred_id: str) -> bool:
    if cred_id in store.api_credentials:
        del store.api_credentials[cred_id]
        return True
    return False


def create_webhook_config(payload: dict[str, Any]) -> dict[str, Any]:
    item = WebhookConfig(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    store.webhook_configs[item["id"]] = item
    return item


def get_webhook_config(webhook_id: str) -> dict[str, Any] | None:
    return store.webhook_configs.get(webhook_id)


def list_webhook_configs(company_id: str) -> list[dict[str, Any]]:
    return [w for w in store.webhook_configs.values() if w.get("company_id") == company_id]


def delete_webhook_config(webhook_id: str) -> bool:
    if webhook_id in store.webhook_configs:
        del store.webhook_configs[webhook_id]
        return True
    return False


def log_api_call(payload: dict[str, Any]) -> dict[str, Any]:
    item = ApiLog(**payload).model_dump()
    from datetime import datetime, timezone
    item["timestamp"] = datetime.now(timezone.utc).isoformat()
    store.api_logs.append(item)
    if len(store.api_logs) > 1000:
        store.api_logs = store.api_logs[-1000:]
    return item


def list_api_logs(
    company_id: str,
    connector_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    logs = [l for l in store.api_logs if l.get("company_id") == company_id]
    if connector_id:
        logs = [l for l in logs if l.get("connector_id") == connector_id]
    return logs[-limit:]


def get_connector_health(company_id: str) -> dict[str, Any]:
    credentials = list_api_credentials(company_id)
    active = [c for c in credentials if c.get("is_active")]
    logs = [l for l in store.api_logs if l.get("company_id") == company_id]
    recent_failures = [l for l in logs[-100:] if int(l.get("status_code", 0)) >= 400]
    return {
        "company_id": company_id,
        "total_connectors": len(credentials),
        "active_connectors": len(active),
        "providers": list(set(c.get("provider", "unknown") for c in active)),
        "recent_log_count": len(logs[-100:]),
        "recent_failure_count": len(recent_failures),
    }


# ── HR Services ───────────────────────────────────────────────────────────────────

def create_employee(payload: dict[str, Any]) -> dict[str, Any]:
    item = Employee(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    store.employees[item["id"]] = item
    return item


def get_employee(emp_id: str) -> dict[str, Any] | None:
    return store.employees.get(emp_id)


def list_employees(company_id: str, status: str | None = None, department: str | None = None) -> list[dict[str, Any]]:
    emps = [e for e in store.employees.values() if e.get("company_id") == company_id]
    if status:
        emps = [e for e in emps if e.get("status") == status]
    if department:
        emps = [e for e in emps if e.get("department") == department]
    return emps


def update_employee(emp_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    emp = store.employees.get(emp_id)
    if emp is None:
        return None
    for k, v in payload.items():
        if v is not None:
            emp[k] = v
    from datetime import datetime, timezone
    emp["updated_at"] = datetime.now(timezone.utc).isoformat()
    return emp


def create_recruitment(payload: dict[str, Any]) -> dict[str, Any]:
    item = RecruitmentPipeline(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    store.recruitment_pipeline[item["id"]] = item
    return item


def get_recruitment(rec_id: str) -> dict[str, Any] | None:
    return store.recruitment_pipeline.get(rec_id)


def list_recruitments(company_id: str, stage: str | None = None) -> list[dict[str, Any]]:
    recs = [r for r in store.recruitment_pipeline.values() if r.get("company_id") == company_id]
    if stage:
        recs = [r for r in recs if r.get("stage") == stage]
    return recs


def update_recruitment(rec_id: str, stage: str) -> dict[str, Any] | None:
    rec = store.recruitment_pipeline.get(rec_id)
    if rec is None:
        return None
    rec["stage"] = stage
    return rec


# ── Logistics Services ───────────────────────────────────────────────────────────

def create_vehicle(payload: dict[str, Any]) -> dict[str, Any]:
    item = Vehicle(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    store.vehicles[item["id"]] = item
    return item


def get_vehicle(veh_id: str) -> dict[str, Any] | None:
    return store.vehicles.get(veh_id)


def list_vehicles(company_id: str, status: str | None = None) -> list[dict[str, Any]]:
    vehs = [v for v in store.vehicles.values() if v.get("company_id") == company_id]
    if status:
        vehs = [v for v in vehs if v.get("status") == status]
    return vehs


def update_vehicle_status(veh_id: str, status: str) -> dict[str, Any] | None:
    veh = store.vehicles.get(veh_id)
    if veh is None:
        return None
    veh["status"] = status
    return veh


def create_shipment(payload: dict[str, Any]) -> dict[str, Any]:
    item = Shipment(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    store.shipments[item["id"]] = item
    return item


def get_shipment(ship_id: str) -> dict[str, Any] | None:
    return store.shipments.get(ship_id)


def list_shipments(company_id: str, status: str | None = None, vehicle_id: str | None = None) -> list[dict[str, Any]]:
    ships = [s for s in store.shipments.values() if s.get("company_id") == company_id]
    if status:
        ships = [s for s in ships if s.get("status") == status]
    if vehicle_id:
        ships = [s for s in ships if s.get("vehicle_id") == vehicle_id]
    return ships


def update_shipment_status(ship_id: str, status: str, delivered_at: str | None = None) -> dict[str, Any] | None:
    ship = store.shipments.get(ship_id)
    if ship is None:
        return None
    ship["status"] = status
    if status == "delivered" and delivered_at:
        ship["actual_delivery"] = delivered_at
    return ship


def get_logistics_summary(company_id: str) -> dict[str, Any]:
    vehicles = list_vehicles(company_id)
    available = [v for v in vehicles if v.get("status") == "available"]
    in_use = [v for v in vehicles if v.get("status") == "in_use"]
    shipments = list_shipments(company_id)
    in_transit = [s for s in shipments if s.get("status") == "in_transit"]
    return {
        "company_id": company_id,
        "total_vehicles": len(vehicles),
        "available_vehicles": len(available),
        "vehicles_in_use": len(in_use),
        "total_shipments": len(shipments),
        "shipments_in_transit": len(in_transit),
    }


def get_hr_summary(company_id: str) -> dict[str, Any]:
    employees = list_employees(company_id)
    active = [e for e in employees if e.get("status") == "active"]
    recruiting = list_recruitments(company_id)
    open_positions = [r for r in recruiting if r.get("stage") in ("applied", "screening", "interview")]
    return {
        "company_id": company_id,
        "total_employees": len(employees),
        "active_employees": len(active),
        "recruiting_candidates": len(recruiting),
        "open_positions": len(open_positions),
    }


# ── Sales Services ──────────────────────────────────────────────────────────────

def create_quote(payload: dict[str, Any]) -> dict[str, Any]:
    item = Quote(**payload).model_dump()
    # Calculate totals from line items
    subtotal = sum(itm.get("quantity", 1) * itm.get("unit_price", 0) * (1 - itm.get("discount_pct", 0) / 100) for itm in item.get("items", []))
    item["subtotal"] = subtotal
    item["total"] = subtotal * (1 - item.get("discount_pct", 0) / 100)
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    item["updated_at"] = item["created_at"]
    store.quotes[item["id"]] = item
    return item


def get_quote(quote_id: str) -> dict[str, Any] | None:
    return store.quotes.get(quote_id)


def list_quotes(company_id: str, status: str | None = None) -> list[dict[str, Any]]:
    qs = [q for q in store.quotes.values() if q.get("company_id") == company_id]
    if status:
        qs = [q for q in qs if q.get("status") == status]
    return qs


def update_quote(quote_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    quote = store.quotes.get(quote_id)
    if quote is None:
        return None
    for k, v in payload.items():
        if v is not None:
            quote[k] = v
    # Recalculate totals if items changed
    subtotal = sum(itm.get("quantity", 1) * itm.get("unit_price", 0) * (1 - itm.get("discount_pct", 0) / 100) for itm in quote.get("items", []))
    quote["subtotal"] = subtotal
    quote["total"] = subtotal * (1 - quote.get("discount_pct", 0) / 100)
    from datetime import datetime, timezone
    quote["updated_at"] = datetime.now(timezone.utc).isoformat()
    return quote


def create_proposal(payload: dict[str, Any]) -> dict[str, Any]:
    item = Proposal(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    item["updated_at"] = item["created_at"]
    store.proposals[item["id"]] = item
    # Link to quote if exists
    if item.get("quote_id"):
        quote = store.quotes.get(item["quote_id"])
        if quote:
            quote["status"] = "converted"
            quote["converted_to_proposal_id"] = item["id"]
            quote["updated_at"] = datetime.now(timezone.utc).isoformat()
    return item


def get_proposal(proposal_id: str) -> dict[str, Any] | None:
    return store.proposals.get(proposal_id)


def list_proposals(company_id: str, status: str | None = None) -> list[dict[str, Any]]:
    ps = [p for p in store.proposals.values() if p.get("company_id") == company_id]
    if status:
        ps = [p for p in ps if p.get("status") == status]
    return ps


def update_proposal(proposal_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    prop = store.proposals.get(proposal_id)
    if prop is None:
        return None
    for k, v in payload.items():
        if v is not None:
            prop[k] = v
    from datetime import datetime, timezone
    prop["updated_at"] = datetime.now(timezone.utc).isoformat()
    return prop


def create_deal_desk(payload: dict[str, Any]) -> dict[str, Any]:
    item = DealDesk(**payload).model_dump()
    from datetime import datetime, timezone
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    item["updated_at"] = item["created_at"]
    store.deal_desks[item["id"]] = item
    return item


def get_deal_desk(deal_id: str) -> dict[str, Any] | None:
    return store.deal_desks.get(deal_id)


def list_deal_desks(company_id: str, stage: str | None = None) -> list[dict[str, Any]]:
    ds = [d for d in store.deal_desks.values() if d.get("company_id") == company_id]
    if stage:
        ds = [d for d in ds if d.get("stage") == stage]
    return ds


def update_deal_desk(deal_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    deal = store.deal_desks.get(deal_id)
    if deal is None:
        return None
    for k, v in payload.items():
        if v is not None:
            deal[k] = v
    from datetime import datetime, timezone
    deal["updated_at"] = datetime.now(timezone.utc).isoformat()
    return deal


def get_sales_summary(company_id: str) -> dict[str, Any]:
    quotes = list_quotes(company_id)
    proposals = list_proposals(company_id)
    deals = list_deal_desks(company_id)
    open_quotes = [q for q in quotes if q.get("status") in ("draft", "sent")]
    converted_quotes = [q for q in quotes if q.get("status") == "converted"]
    won_deals = [d for d in deals if d.get("stage") == "closed_won"]
    lost_deals = [d for d in deals if d.get("stage") == "closed_lost"]
    pending = [d for d in deals if d.get("stage") == "pending_approval"]
    return {
        "company_id": company_id,
        "total_quotes": len(quotes),
        "open_quotes": len(open_quotes),
        "converted_quotes": len(converted_quotes),
        "total_proposals": len(proposals),
        "total_deals": len(deals),
        "won_deals": len(won_deals),
        "lost_deals": len(lost_deals),
        "pending_approval": len(pending),
        "pipeline_value": sum(d.get("total_amount", 0) for d in deals if d.get("stage") not in ("closed_won", "closed_lost")),
        "won_value": sum(d.get("total_amount", 0) for d in won_deals),
    }
