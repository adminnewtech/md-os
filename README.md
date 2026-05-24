# MD-OS — AI Company Operating System

> Kuwait SaaS platform targeting 1M KD/year. Built with Hermes Agent + Antigravity + Paperclip + Multica + Codegraph.

## Stack

| Layer | Tool | Role |
|-------|------|------|
| Orchestration | Hermes Agent | CEO layer, cron, Telegram reports |
| Coding | Google Antigravity | Heavy execution |
| App/Business | Paperclip | Workflows, UI |
| Workforce | Multica | Agent state + autopilot |
| Code Quality | Codegraph | Dependency impact gate |

## Architecture

```
/root/md-os/
├── api/          # FastAPI backend (auth, CRUD, orchestrator, reporting)
├── agents/       # 25 agent JSON definitions (CEO → support)
├── prompts/      # agent system prompts (markdown)
├── schemas/      # PostgreSQL schema + migrations
├── workflows/    # 6 automation workflow templates
├── tests/        # 91 passing tests (pytest)
├── ui/           # Paperclip UI module map
└── docs/         # blueprints, progress, operating plan
```

## Status (2026-05-24)

- ✅ 111 files committed to git (main + develop)
- ✅ 91 tests passing
- ✅ Codegraph quality gate functional
- 🔄 Next: Finance module → Inventory → API Connector

## Commands

```bash
# Stack audit
python3 /root/.hermes/profiles/newmain/scripts/md_os_integrated.py audit

# Quality gate
python3 /root/.hermes/profiles/newmain/scripts/md_os_integrated.py verify

# Run tests
cd /root/md-os && python3 -m pytest tests/ -q

# Codegraph analysis
cd /root/md-os && codegraph api/main.py --csv /tmp/cg.csv
```

## Branches

- `main` — stable, production-ready snapshot
- `develop` — active development (current)

## Quick Stats

- 25 agents defined
- 6 workflow templates
- 91 tests (auth, API, CRM, audit, orchestrator, support)
- PostgreSQL schema: core + CRM + support modules
- REST API: 7 modules (auth, db, security, services, orchestrator, reporting, tool permissions)
