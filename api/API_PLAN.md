# MD-OS API Plan v0.1

## Base
- Auth: JWT + workspace scoped RBAC
- Audit: every mutation writes `audit_logs`
- Approval guard: destructive, financial, production, customer-data, secrets

## Endpoints
- `POST /api/companies` create company
- `GET /api/companies/:id/dashboard` executive dashboard
- `POST /api/projects` create project
- `POST /api/agents` create agent from definition
- `POST /api/agent-teams` create team
- `POST /api/tasks` create task
- `POST /api/tasks/:id/assign-agent` assign agent
- `POST /api/workflows` create workflow graph
- `POST /api/workflows/:id/run` run workflow
- `GET /api/workflow-runs/:id` run status
- `POST /api/skills` add skill
- `POST /api/memories/search` semantic memory search
- `POST /api/connectors` create connector
- `POST /api/approvals` request approval
- `POST /api/approvals/:id/decide` approve/reject
- `GET /api/crm/contacts`, `POST /api/crm/contacts`
- `GET /api/deals`, `POST /api/deals`
- `GET /api/support/tickets`, `POST /api/support/tickets`
- `GET /api/finance/invoices`, `POST /api/finance/invoices`
- `GET /api/inventory/items`, `POST /api/inventory/items`

## Connector Priority
1. Telegram
2. GitHub
3. Paperclip
4. Hermes Gateway
5. Zoho Books / QuickBooks
6. Shopify / WooCommerce
7. Stripe / Tap / MyFatoorah
8. WhatsApp Business
9. Google Workspace
10. n8n / webhooks
