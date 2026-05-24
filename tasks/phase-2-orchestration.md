# Orchestration — Agent Run Lifecycle, Memory, Approval Interrupt

- [x] **[p2-01]** Hermes Orchestrator service: plan → delegate → monitor → report — `P0` ✅
- [x] **[p2-02]** Agent run state machine: queued/running/waiting_approval/done/failed — `P0` ✅
- [x] **[p2-03]** Memory write/search adapter: GBrain/PGLite + vector (768 dims) — `P0` ✅
- [x] **[p2-04]** Tool permission resolver per agent role — `P1` ✅ (tool_permissions.py: 24 roles mapped to tool sets; /api/agents/{id}/tool-permissions + /check endpoints; company isolation; 4 tests)
- [x] **[p2-05]** Human approval interrupt mechanism (workflow pauses, resumes on approve) — `P0` ✅
- [x] **[p2-06]** Build /api/approvals CRUD + decision endpoint — `P1` ✅
- [x] **[p2-07]** Agent periodic report cycle (6h) via cron — `P1` ✅
- [x] **[p2-08]** CEO daily synthesis report (9 AM Mon-Fri) — `P1` ✅
- [ ] **[p2-09]** Build Agent Teams page (org chart, run cycles, reports) — `P2`
- [ ] **[p2-10]** Build Task Engine page (Kanban, queues, SLA, automation rules) — `P2`
