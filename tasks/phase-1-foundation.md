# Foundation — DB, API, Auth, Paperclip Shell

- [x] **[p1-01]** Create PostgreSQL DB with pgvector and run migrations — `P0` ✅ (migration runner + pgvector compose/docs ready; live DB needs POSTGRES_URI)
- [x] **[p1-02]** Build auth: JWT + workspace-scoped RBAC middleware — `P0` ✅
- [x] **[p1-03]** Build approval guard middleware (destructive/financial/production/customer-data/secret) — `P0` ✅
- [x] **[p1-04]** Build audit log middleware (every mutation logged) — `P0` ✅
- [x] **[p1-05]** Seed default company: MD Platform (NewTech Kuwait) — `P0` ✅
- [x] **[p1-06]** Import 25 agent definitions into agents table — `P1` ✅
- [x] **[p1-07]** Import 6 workflow JSON files into workflows table — `P1` ✅
- [x] **[p1-08]** Build /api/agents CRUD + /api/agent-teams — `P1` ✅
- [x] **[p1-09]** Build /api/workflows/:id/run + workflow_runs table — `P1` ✅
- [ ] **[p1-10]** Build Paperclip dashboard shell (RTL Arabic, sidebar, company switcher) — `P1`
- [ ] **[p1-11]** Build Agent Studio page (create/edit/view agents) — `P1`
- [ ] **[p1-12]** Build Workflow Studio page (visual graph view + trigger config) — `P2`

## Phase 2 — Orchestration
- [x] **[p2-01]** Hermes Orchestrator service: plan → delegate → monitor → report — `P0` ✅ (orchestrator.py + 4 endpoints; plan decomposition heuristics; agent role matching; run_cycle executes full cycle; 13 integration tests)
- [x] **[p2-02]** Agent run state machine: queued/running/waiting_approval/done/failed — `P0` ✅ (partial: code + tests done; DB table ready via p1-01)
- [x] **[p2-03]** Memory write/search adapter: GBrain/PGLite + vector (768 dims) — `P0` ✅ (memory.py module; write/get/list/delete/search/upsert with cosine sim; 3 test scenarios)
- [x] **[p2-04]** Tool permission resolver per agent role — `P1` ✅
- [x] **[p2-05]** Human approval interrupt mechanism (workflow pauses, resumes on approve) — `P0` ✅ (api/agent-runs/{id}/request-approval → pause run + link approval; decide endpoint resumes or fails agent run)
- [x] **[p2-06]** Build /api/approvals CRUD + decision endpoint — `P1` ✅
- [x] **[p2-07]** Agent periodic report cycle (6h) via cron — `P1` ✅ (backend report generator + `/api/reports/agent-periodic`)
- [x] **[p2-08]** CEO daily synthesis report (9 AM Mon-Fri) — `P1` ✅
- [ ] **[p2-09]** Build Agent Teams page (org chart, run cycles, reports) — `P2`
- [ ] **[p2-10]** Build Task Engine page (Kanban, queues, SLA, automation rules) — `P2`
