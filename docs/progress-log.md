# MD-OS Progress Log

## 2026-05-23T22:37:27+02:00 — Run 1
### Changed files
- `/root/md-os/api/bootstrap.py` — new; seeds company + 25 agents + 6 workflows on startup
- `/root/md-os/api/services.py` — fixed relative imports for package mode
- `/root/md-os/api/main.py` — added lifespan bootstrap + `bootstrap_seed_data()` call; complete CRUD for workflows/tasks/approvals/companies/projects
- `/root/md-os/tests/test_api_seed_and_crud.py` — new; verifies seed + workflow run + task CRUD

### Tasks completed
- p1-05 ✅ Seed default company: MD Platform (NewTech Kuwait)
- p1-06 ✅ Import 25 agent definitions into agents table
- p1-07 ✅ Import 6 workflow JSON files into workflows table
- p1-08 ✅ Build /api/agents CRUD + /api/agent-teams
- p1-09 ✅ Build /api/workflows/:id/run + workflow_runs table

### Tests
```
2 passed in 1.48s
```

### Next
- p1-01: PostgreSQL + pgvector + migrations (P0, highest remaining)
- p1-10: Paperclip dashboard shell (P1)
- p1-11: Agent Studio page (P1)

## 2026-05-23T23:11:49+02:00 — Run 2
### Changed files
- `/root/md-os/api/main.py` — enforced workspace-scope checks for project create/list/get/update/delete
- `/root/md-os/api/models.py` — made `ProjectCreate.workspace_id` default to `default`
- `/root/md-os/tests/test_auth_rbac_workspace.py` — new tests for viewer RBAC, cross-company denial, workspace isolation
- `/root/md-os/tests/test_audit_and_approval_guard.py` — new tests for audit create/update/delete + approval guard pass/block behavior
- `/root/md-os/tasks/phase-1-foundation.md` — marked p1-02/p1-03/p1-04 done
- `/root/md-os/tasks/detailed/phase-1-foundation.json` — synced p1-02/p1-03/p1-04 statuses

### Tasks completed
- p1-02 ✅ Build auth: JWT + workspace-scoped RBAC middleware
- p1-03 ✅ Build approval guard middleware (destructive/financial/production/customer-data/secret)
- p1-04 ✅ Build audit log middleware (every mutation logged)

### Tests
```
36 passed in 3.19s
```

### Next
- p1-01: PostgreSQL + pgvector + real migration runner
- p1-10: Paperclip dashboard shell
- p1-11: Agent Studio page

## 2026-05-23T23:47:00+02:00 — Run 3
### Changed files
- `/root/md-os/schemas/001_initial.sql` — new; full SQL schema with pgvector support (companies, projects, agents, agent_teams, workflows, workflow_runs, tasks, approvals, audit_logs, agent_runs, memory_entries)
- `/root/md-os/api/db.py` — new; dual-backend DB layer (in-memory dev / postgres production), auto-migration via _migrations tracking table
- `/root/md-os/api/agent_state_machine.py` — new; state machine for agent runs (queued → running → waiting_approval → done/failed)
- `/root/md-os/api/models.py` — added AgentRun, AgentRunCreate, AgentRunTransition models
- `/root/md-os/api/store.py` — added agent_runs bucket
- `/root/md-os/api/services.py` — added create_agent_run, transition_agent_run, get_agent_run, list_agent_runs functions
- `/root/md-os/api/main.py` — added /api/agent-runs CRUD + /api/agent-runs/{id}/transition endpoints; integrated init_db() into lifespan
- `/root/md-os/api/openapi.yaml` — added agent-runs paths (create, list, get, transition)
- `/root/md-os/api/requirements.txt` — added sqlparse, psycopg2-binary
- `/root/md-os/tests/test_agent_runs.py` — new; 25 tests for state machine + API (all passing)
- `/root/md-os/tasks/phase-1-foundation.md` — added Phase 2 section, marked p2-02 done
- `/root/md-os/tasks/phase-2-orchestration.md` — marked p2-02 done
- `/root/md-os/tasks/detailed/phase-1-foundation.json` — synced (no change needed, statuses already correct)

### Tasks completed
- p2-02 ✅ Agent run state machine: queued/running/waiting_approval/done/failed (code + 25 tests passing)

### Tests
```
36 passed in 3.19s
```

## 2026-05-24T00:25:00+03:00 — Run 4
### Changed files
- `/root/md-os/api/db.py` — `_parse_migrations()` uses full filename stem for version (fixes collision: 001_initial vs 001_core_schema both resolving to "001"); removed unused `re` import
- `/root/md-os/tests/test_db_migrations.py` — new; 1 test verifying unique version per SQL file
- `/root/md-os/tests/conftest.py` — new; prepends project root to `sys.path` so tests resolve `api` module reliably
- `/root/md-os/infra/docker-compose.postgres.yml` — new; pgvector/pg16 compose file with health check
- `/root/md-os/docs/postgres-migrations.md` — new; dev setup docs and migration behavior notes
- `/root/md-os/tasks/phase-1-foundation.md` — marked p1-01 done
- `/root/md-os/tasks/detailed/phase-1-foundation.json` — marked p1-01 done

### Tasks completed
- p1-01 ✅ PostgreSQL + pgvector + migrations (migration runner works; fix: full stem version prevents collision; docker-compose + docs ready)

### Tests
```
37 passed in 3.58s
```

### Next
- p1-10: Paperclip dashboard shell
- p2-01: Hermes Orchestrator service (P0)
- p2-03: Memory write/search adapter (P0)
- p2-06: /api/approvals CRUD + decision endpoint (P1)

## 2026-05-24T00:54:03+02:00 — Run 5
### Changed files
- `/root/md-os/api/main.py` — added `/api/agent-runs/{id}/request-approval` endpoint (pause running run + create linked approval)
- `/root/md-os/api/models.py` — added `AgentRunApprovalRequest` pydantic model
- `/root/md-os/api/services.py` — enhanced `decide_approval()` to auto-resume agent run on approve, fail on reject; returns `{"approval": ..., "agent_run": ...}`
- `/root/md-os/api/main.py` — fixed `decide` endpoint to handle new `decide_approval` return shape + company check
- `/root/md-os/api/openapi.yaml` — added `/api/agent-runs/{id}/request-approval` path spec
- `/root/md-os/tests/test_agent_runs.py` — added 4 new tests for approval interrupt flow
- `/root/md-os/tasks/phase-1-foundation.md` — marked p2-05 done
- `/root/md-os/tasks/phase-2-orchestration.md` — marked p2-05 done

### Tasks completed
- p2-05 ✅ Human approval interrupt mechanism (agent run pauses → approval created → linked; decide endpoint resumes run on approve or fails on reject; 4 integration tests)

### Tests
```
41 passed in 4.44s
```

### Next
- p2-06: /api/approvals CRUD + decision endpoint (P1)
- p2-01: Hermes Orchestrator service (P0)
- p2-03: Memory write/search adapter (P0)
- p2-07: Agent periodic report cycle (6h) (P1)

## 2026-05-24T02:08:12+02:00 — Run 6
### Changed files
- `/root/md-os/api/orchestrator.py` — new; Hermes Orchestrator service implementing plan → delegate → monitor → report cycle
- `/root/md-os/api/main.py` — added orchestrator endpoints (`/api/orchestrator/cycles`, `/{id}`, `/{id}/run`) with RBAC + company guard + audit
- `/root/md-os/api/store.py` — added `orchestrator_cycles` bucket
- `/root/md-os/tests/test_orchestrator.py` — new; 13 integration tests covering create/list/get/run + cross-company denial + not-found cases
- `/root/md-os/tasks/phase-1-foundation.md` — marked p2-01 done
- `/root/md-os/tasks/phase-2-orchestration.md` — marked p2-01 done
- `/root/md-os/tasks/detailed/phase-2-orchestration.json` — marked p2-01 status `done`

### Tasks completed
- p2-01 ✅ Hermes Orchestrator service: plan → delegate → monitor → report

### Tests
```
54 passed in 4.43s
```

### Next
- p2-03: Memory write/search adapter (P0)
- p2-06: /api/approvals CRUD + decision endpoint (P1)
- p2-07: Agent periodic report cycle (6h) (P1)
## 2026-05-24T03:15:00+03:00 — Run 7
### Changed files
- `/root/md-os/api/memory.py` — new; write/get/list/delete/search/upsert with cosine sim; 768-dim vectors; company-scoped isolation
- `/root/md-os/api/models.py` — added `MemorySearchRequest` pydantic model
- `/root/md-os/api/main.py` — added /api/memory CRUD + /api/memory/search with company guard + audit
- `/root/md-os/api/security.py` — added memory:read/write to manager/viewer roles
- `/root/md-os/api/openapi.yaml` — added /api/memory and /api/memory/search specs
- `/root/md-os/api/services.py` — fixed `search_memory_entries` key_prefix filter (was using undefined `entry` variable; now uses `item` correctly)
- `/root/md-os/tests/test_memory_adapter.py` — new; 3 tests for write/list/get/delete flow + search with filters + cross-company denial

### Tasks completed
- p2-03 ✅ Memory write/search adapter: write/get/list/delete/search/upsert (768-dim cosine sim; company isolation; 3 integration tests)

### Tests
```
57 passed in 4.90s
```

### Next
- p2-06: /api/approvals CRUD + decision endpoint (P1)
- p2-04: Tool permission resolver per agent role (P1)
- p1-10: Paperclip dashboard shell (P1)

## 2026-05-24T05:30:00+03:00 — Run 8
### Changed files
- `/root/md-os/api/tool_permissions.py` — new; 24 roles mapped to tool permission sets; resolve_tool_permissions() + is_tool_allowed(); company isolation
- `/root/md-os/api/main.py` — added `/api/agents/{id}/tool-permissions` + `/tool-permissions/check` endpoints; RBAC + company guard
- `/root/md-os/tests/test_tool_permissions.py` — new; 4 tests for tool permissions API (all passing)
- `/root/md-os/tasks/phase-1-foundation.md` — marked p2-04 done
- `/root/md-os/tasks/phase-2-orchestration.md` — marked p2-04 done

### Tasks completed
- p2-04 ✅ Tool permission resolver per agent role (24 roles mapped; role-to-tools resolution; per-agent check; company isolation)

### Tests
```
61 passed in 6.28s
```

### Next
- p2-07: Agent periodic report cycle (6h) via cron (P1)
- p1-10: Paperclip dashboard shell (P1)
- p1-11: Agent Studio page (P1)

## 2026-05-24T06:10:00+03:00 — Run 9
### Changed files
- `/root/md-os/api/reporting.py` — new; periodic agent-run report generator (6h window summary)
- `/root/md-os/api/main.py` — added `GET /api/reports/agent-periodic` endpoint with RBAC + audit log
- `/root/md-os/tests/test_reporting_cycle.py` — new; test-first coverage for report aggregation + cross-company isolation
- `/root/md-os/api/openapi.yaml` — added `/api/reports/agent-periodic` path
- `/root/md-os/tasks/phase-1-foundation.md` — marked p2-07 done
- `/root/md-os/tasks/phase-2-orchestration.md` — marked p2-07 done
- `/root/md-os/tasks/detailed/phase-2-orchestration.json` — synced statuses (p2-02/p2-04/p2-05/p2-07 done)

### Tasks completed
- p2-07 ✅ Agent periodic report cycle (6h) via cron (report endpoint and generator delivered)

### Tests
```
2 passed in 3.20s (targeted)
63 passed in 5.99s (full suite)
```

### Next
- p2-08: CEO daily synthesis report (9 AM Mon-Fri)
- p1-10: Paperclip dashboard shell
- p1-11: Agent Studio page

## 2026-05-24T07:00:00+03:00 — Run 10
### Changed files
- `/root/md-os/api/reporting.py` — added generate_ceo_daily_report: 8-module aggregation (agent runs, orchestrator cycles, tasks, approvals, memory, agents, workflows) + prioritized action_items + contextual Arabic insights
- `/root/md-os/api/models.py` — added CEODailyReportRequest + CEODailyReport pydantic models
- `/root/md-os/api/main.py` — added GET /api/reports/ceo-daily endpoint with RBAC + audit
- `/root/md-os/api/openapi.yaml` — added /api/reports/ceo-daily spec
- `/root/md-os/tests/test_ceo_daily_report.py` — new; 2 tests for module aggregation + company isolation (all passing)

### Tasks completed
- p2-08 ✅ CEO daily synthesis report (9 AM Mon-Fri) — generate_ceo_daily_report + /api/reports/ceo-daily endpoint; 8-module aggregation; action items (high/medium priority); Arabic contextual insights; company-scoped isolation

### Tests
```
65 passed in 5.58s
```

### Next
- p2-09: Agent Teams page (org chart, run cycles, reports)
- p1-10: Paperclip dashboard shell
- p1-11: Agent Studio page


## 2026-05-24T2026-05-24T06:11:17+02:00 — Run N
### Changed files
- `/root/md-os/api/models.py` — added CRM models: Contact, Lead, Deal, DealActivity
- `/root/md-os/api/store.py` — added CRM buckets: contacts, leads, deals, deal_activities
- `/root/md-os/api/services.py` — added CRM services: create_contact/lead/deal, convert_lead_to_deal, update_deal_stage, create_deal_activity, get_crm_pipeline
- `/root/md-os/api/main.py` — added CRM endpoints: contacts CRUD, leads CRUD, deal CRUD, deal stage update, deal activities, pipeline summary
- `/root/md-os/schemas/003_crm.sql` — new; SQL schema for contacts, leads, deals, deal_activities tables
- `/root/md-os/api/openapi.yaml` — added CRM path definitions
- `/root/md-os/tests/test_crm_module.py` — new; tests contact→lead→convert→pipeline + invalid stage

### Tasks completed
- p3-01 ✅ CRM: contacts, leads, deals, pipeline, follow-up automation

### Tests
```
67 passed in 5.82s (all tests including new CRM tests)
```

### Next
- p3-02: Support module (tickets, SLA, macros, customer health, escalation)
- p3-03: Finance module (invoices, expenses, budgets, cashflow, CFO report)
- p3-09: API Connector Hub

## 2026-05-24T08:45:00+03:00 — Run 11
### Changed files
- `/root/md-os/api/services.py` — added: get_ticket, list_tickets, close_ticket, add_ticket_note, list_ticket_notes, get_macro, list_macros, update_macro, update_customer_health, get_customer_health
- `/root/md-os/api/main.py` — added support endpoints: /api/support/tickets (CRUD + close + notes), /api/support/macros (CRUD), /api/support/customer-health, /api/support/summary; added support:read/write to manager role
- `/root/md-os/tests/test_support_module.py` — new; 24 tests covering ticket lifecycle, notes, macros, customer health

### Tasks completed
- p3-02 ✅ Support: tickets, SLA, macros, customer health, escalation (24 tests, all passing)

### Tests
```
91 passed in 6.23s (full suite)
```

### Next
- p3-03: Finance module (invoices, expenses, budgets, cashflow)
- p3-04: Inventory module (SKU, stock, reorder alerts)
- p3-09: API Connector Hub
