# Agentic SDLC Policy — MD-OS

**Model:** `top` (9Router combo, provider=ninerouter)
**Stack:** Hermes CEO + OpenCode primary coder + Antigravity SDK reviewer + Codegraph gate + GBrain memory
**Last updated:** 2026-05-24

---

## 1. Execution Tiers

| Tier | Worker | Used for |
|------|--------|----------|
| 1 | **OpenCode** | Refactor, feature, fix, PR review, smoke tests |
| 2 | **Antigravity SDK** | Architecture review, alternative design, complex reasoning |
| 3 | **Hermes direct** | Config, cron, small patches, tests, codegraph calls |
| 4 | **Codegraph** | Quality gate BEFORE + AFTER every PR |

**Rule:** OpenCode is always first for coding. Never skip to Tier 2 without trying Tier 1.

---

## 2. Failover Chain

```
antigravity-sdk(gemini) → opencode(minimax) → opencode(openai/codex) → hermes-direct-tools
```

- Try primary first
- On error (quota/rate-limit/auth), step to next
- Document provider used in commit message

---

## 3. Development Cycle (per task)

```
1. Hermes receives task → parse scope → open branch
2. Codegraph pre-check (impact/dependencies)
3. OpenCode executes coding task
4. Antigravity SDK reviews (complex tasks only)
5. Test gate (targeted + full suite)
6. Codegraph post-check (entities/dependencies)
7. GBrain records decision + rationale
8. PR → review → merge
9. Hermes Telegram report
```

---

## 4. Quality Gates (mandatory)

### Pre-PR gate
```bash
python3 /root/.hermes/profiles/newmain/scripts/md_os_integrated.py verify
mcp_codegraph_codegraph_analyze(path="/root/md-os")
```

### Post-PR gate
- Entity count must not regress
- Dependencies must not introduce circular deps
- 100% tests pass

---

## 5. Component Roles

| Component | Role | Alive check |
|-----------|------|-------------|
| Hermes Agent | CEO orchestrator, cron, Telegram | always |
| GBrain | Long-term memory, knowledge graph | `curl http://127.0.0.1:3132/health` |
| OpenCode | Primary coding worker | `opencode --version` |
| Antigravity SDK | Google planning/review | SDK live call |
| Codegraph | Quality gate + deps | `codegraph --version` |
| Multica | Worker board | 7 agents non-idle |
| Paperclip | Approval workflow | `curl 83.171.249.32:3100/health` |

---

## 6. Module Addition Pattern

Every new business module needs ALL of these in order:

1. `models.py` — Add ApiModel Create + main class
2. `store.py` — Add bucket in `__init__` + `reset()`
3. `services.py` — CRUD + summary functions
4. `security.py` — Add `module:read/write` to `manager` ROLE_PERMISSIONS
5. `main.py` — Wire FastAPI routes
6. `tests/` — TestClient E2E test file

Rules:
- Company isolation: `_company_allowed(ctx, item.get("company_id"))` on every route
- Audit logging: `log_audit()` on create/update/delete
- Store reset: add bucket to BOTH `__init__` AND `reset()`

---

## 7. Commit Format

```
<type>(<scope>): <short description>

Types: feat | fix | refactor | test | docs | chore
Scope: api | models | services | security | tests | docs
```

Full test suite must pass before commit.

---

## 8. Current Status (2026-05-24)

| Module | Status |
|--------|--------|
| CRM | ✅ |
| Support | ✅ |
| Finance | ✅ |
| Inventory | ✅ |
| HR | ✅ |
| Logistics | ✅ |
| Integrations | ✅ |
| Connector Hub | ✅ |
| Orchestrator | ✅ |
| Reports | ✅ |
| Memory | ✅ |
| Approvals | ✅ |
| Sales | ⏳ pending |
| Marketing | ⏳ pending |