# MD-OS Codegraph Baseline Report
**Generated:** 2026-05-24 | **Tool:** Codegraph v1.2.0 | **Path:** /root/md-os

---

## Project Overview

| Metric | Value |
|--------|-------|
| Python files | 31 |
| Total lines | 8,010 |
| Modules | 12 |
| Test files | 17 |

---

## File Structure

```
md-os/
├── api/                    # Core API (12 files)
│   ├── main.py             # FastAPI entry point
│   ├── models.py           # 385 lines — 57 Pydantic models
│   ├── orchestrator.py      # 297 lines — CEO agent orchestration
│   ├── reporting.py         # 194 lines — daily/periodic reports
│   ├── bootstrap.py         # Seed data + schema init
│   ├── db.py                # Postgres connection + migrations
│   ├── auth.py              # JWT auth context
│   ├── security.py          # RBAC + tool permissions
│   ├── services.py          # Business logic layer
│   ├── store.py             # InMemory store + persistence
│   ├── agent_state_machine.py
│   └── tool_permissions.py
└── tests/                   # 17 integration tests
```

---

## Hotspots (Most Referenced)

### Tier 1 — Critical (10+ inbound links)

| Entity | File | Lines | Links In |
|--------|------|-------|----------|
| `ApiModel` | models.py | 2 | **39** |
| `InMemoryStore` | store.py | 71 | **9** |
| `can_transition` | agent_state_machine.py | 4 | **10** |
| `is_valid_transition` | agent_state_machine.py | 4 | **10** |

### Tier 2 — High Usage

| Entity | File | Lines | Links In |
|--------|------|-------|----------|
| `generate_ceo_daily_report` | reporting.py | 72 | 1 |
| `InvoiceCreate` | models.py | 13 | 5 |
| `TicketCreate` | models.py | 14 | 3 |
| `DealCreate` | models.py | 14 | 1 |
| `OrchestratorCycle` | orchestrator.py | 54 | 2 |

---

## Domain Models (57 Pydantic Classes)

**Core:**
- Company, Project, Agent, AgentTeam, Workflow, WorkflowRun, Task

**CRM:**
- Contact, Lead, Deal, DealActivity, CustomerHealth

**Support:**
- Ticket, TicketUpdate, Macro, TicketNote

**Finance:**
- InvoiceCreate, Invoice, LineItemCreate, Payment

**Inventory:**
- SKU, StockMovement, ApiCredential, WebhookConfig, ApiLog

**HR/Logistics:**
- Employee, RecruitmentPipeline, Vehicle, Shipment

**System:**
- Approval, AgentRun, MemoryEntry, AuditLog, CEODailyReport

---

## Dependency Chain

```
bootstrap.py (seed data)
  ├── seed_agents     → models.Agent
  ├── seed_projects   → models.Project, models.Task
  ├── seed_workflows  → models.Workflow
  └── bootstrap_full   → 8 domain seeders

reporting.py
  ├── generate_ceo_daily_report  → orchestrator cycle
  ├── generate_agent_periodic_report
  └── _build_action_items / _build_insights

orchestrator.py
  ├── _delegate_plan   → agent dispatch
  └── _monitor_until_done → status polling

db.py
  ├── init_db         → run_pending_migrations
  └── pg_connection   → Postgres pool
```

---

## Security / Auth

- **tool_permissions.py** — resolve_tool_permissions (2 callers), normalize_role
- **auth.py** — JWT context via get_auth_context, create_access_token
- **agent_state_machine.py** — state transitions: idle → running → pending_approval → running → done/error

---

## Before Refactor — Read First

1. **models.py** — changing ApiModel breaks 39 call sites
2. **store.py** — InMemoryStore underpins all CRUD; migration to Postgres needs dual-write
3. **agent_state_machine.py** — transitions are referenced by 10 places; changing states needs audit
4. **orchestrator.py** — CEO delegation logic; any changes affect daily report generation
5. **reporting.py** — CEO report format changes affect all 7 agent reports

---

## Recommendations

1. **Next refactor target:** Extract `InMemoryStore` to a proper repository interface before Postgres migration
2. **Before touching models.py:** Run `find_usages` on any class you plan to rename
3. **Testing baseline:** 17 tests already cover core flows — run before any structural change
4. **Bootstrap isolation:** bootstrap.py has no tests — add integration tests before modifying seed data

---

*Report generated via Codegraph MCP (Hermes Agent integrated)*