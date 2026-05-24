# MD-OS — خطة التطوير الشاملة 2026
## الإصدار: MD-OS v2.0 (Million Dinar OS)
## التاريخ: 2026-05-24
## الحالة: الإنتاجي — مرحلة التوسع

---

## 📌 ملخص الوضع الحالي

### ما تم إنجازه ✅
| المكون | الحالة | ملاحظات |
|--------|--------|---------|
| FastAPI Backend | ✅ production | 40+ endpoint، uvicorn systemd |
| Seed Data كامل | ✅ done | CRM/Projects/Finance/HR/Inventory/Support/Logistics |
| SSL + nginx | ✅ done | certbot + nginx proxy |
| Dashboard HTML | ✅ v2 live | 9 modules، RTL dark |
| CRUD APIs | ✅ done | 134 tests passing |
| Agent Swarm | ✅ 25 agents | roles defined |
| Workflows | ✅ 6 workflows | automation ready |
| Orchestrator | ✅ basic | cycles/runs/approvals |
| Reporting | ✅ | CEO daily + agent periodic |

### ما يحتاج تنفيذ ⚠️
| المكون | الأولوية | الحالة |
|--------|----------|---------|
| Visual verification + screenshots | P0 | لم يكتمل |
| End-to-end CRUD audit | P0 | لم يكتمل رسميًا |
| Marketing module API | P1 | UI فقط |
| Marketing module UI | P1 | placeholder |
| Settings page API wiring | P1 | placeholder |
| Reports page real data | P1 | placeholder |
| Next.js migration | P2 | HTML SPA → real app |
| PostgreSQL migration | P2 | SQLite → PG |
| Real-time WebSocket | P2 | live updates |
| Auth hardening | P1 | bcrypt + real login |
| Multitenancy | P2 | subdomain-based |
| Mobile app | P3 | Flutter/React Native |

---

## 🏗️ الهيكل الجديد — MD-OS v2.0 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Users / Clients                           │
└──────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐   ┌──────────┐    ┌──────────┐
        │Dashboard │   │ Telegram │    │  Mobile  │
        │ (Next.js)│   │  Bridge  │    │    App   │
        └────┬─────┘   └────┬─────┘    └────┬─────┘
             │              │               │
             └──────────────┼───────────────┘
                            ▼
                   ┌────────────────┐
                   │   FastAPI      │
                   │   Backend      │
                   │   (v2.0)       │
                   └────┬───────────┘
                        │
        ┌───────────────┼───────────────────┐
        ▼               ▼                    ▼
  ┌──────────┐   ┌──────────┐       ┌──────────┐
  │ PostgreSQL│   │  PGLite  │       │  Ollama  │
  │ (primary) │   │ (memory) │       │ (embed)  │
  └──────────┘   └──────────┘       └──────────┘
```

---

## 🔢 المراحل التسع — Phases

### PHASE 0 — التثبيت النهائي (هذا الأسبوع)
**الهدف:** قفل النظام كمكتمل 100% رسميًا

- [ ] **0.1** Visual verification لكل 9 صفحات dashboard
  - login → dashboard → CRM → Projects → Finance → HR → Support → Reports → Docs → Settings
  - لقطة شاشة لكل صفحة موثقة
  - التحقق من: data display + navigation + tabs + forms

- [ ] **0.2** End-to-end CRUD audit
  - POST contact → GET contacts → PATCH → DELETE
  - POST ticket → update status → close
  - POST invoice → record payment → check aging
  - POST employee → update department → deactivate

- [ ] **0.3** Final health report
  - All 40+ endpoints verified
  - SSL certs expiry check
  - systemd service status
  - nginx routing verification

**Deliverable:** تقرير إغلاق Phase 0 — "MD-OS Production Ready"

---

### PHASE 1 — Auth & Security Hardening
**الهدف:** من prototype auth إلى production auth

- [ ] **1.1** Real auth flow
  - `/api/auth/login` with email/password (bcrypt)
  - `/api/auth/refresh-token`
  - `/api/auth/logout`
  - JWT expiry enforcement

- [ ] **1.2** Role-based permissions (RBAC)
  - Roles: admin / manager / employee / viewer
  - Permission matrix per module
  - `tool_permissions.py` → fully wired

- [ ] **1.3** Security headers + rate limiting
  - nginx: X-Frame-Options, CSP, HSTS
  - rate_limit_zone: 100 req/min per IP
  - brute-force protection on login

- [ ] **1.4** Audit logging enhancement
  - Log ALL write operations (not just approvals)
  - Immutable audit trail
  - `/api/audit-logs` with pagination + filter

**Files to change:** `api/auth.py`, `api/security.py`, `api/main.py`, `/etc/nginx/sites-enabled/hermes`

---

### PHASE 2 — Next.js Migration
**الهدف:** من HTML SPA إلى real Next.js app

- [ ] **2.1** Next.js project setup
  ```bash
  npx create-next-app@latest md-os-ui --typescript --tailwind --app-router
  cd md-os-ui
  npm install @tanstack/react-query zod react-hook-form
  ```

- [ ] **2.2** Authentication pages
  - `/app/(auth)/login/page.tsx`
  - `/app/(auth)/logout/page.tsx`

- [ ] **2.3** Dashboard layout
  - `/app/(dashboard)/layout.tsx` — sidebar + header
  - RTL via `dir="rtl"` on html
  - Dark theme via Tailwind CSS vars

- [ ] **2.4** Module pages
  - `/app/(dashboard)/crm/page.tsx` — pipeline + contacts + leads
  - `/app/(dashboard)/projects/page.tsx`
  - `/app/(dashboard)/finance/page.tsx`
  - `/app/(dashboard)/hr/page.tsx`
  - `/app/(dashboard)/support/page.tsx`
  - `/app/(dashboard)/reports/page.tsx`
  - `/app/(dashboard)/settings/page.tsx`

- [ ] **2.5** API client layer
  - `/lib/api.ts` — typed fetch wrapper
  - `/lib/auth.ts` — token management
  - React Query for server state

- [ ] **2.6** Deployment
  - Build: `next build && next start`
  - Port 3000, nginx proxy
  - Cutover gate (see skill:md-platform-fullstack-developer)

**Deliverable:** https://mdos.83-171-249-32.nip.io/ → Next.js app

---

### PHASE 3 — PostgreSQL Migration
**الهدف:** من SQLite في-memory store إلى PostgreSQL + pgvector

- [ ] **3.1** Prisma schema design
  - `prisma/schema.prisma` ← full data model
  - Companies, Contacts, Leads, Deals, Employees, etc.
  - Multi-tenancy via `companyId` field

- [ ] **3.2** Migration scripts
  - Export current seed data to JSON
  - Load into PostgreSQL via Prisma
  - Verify row counts match

- [ ] **3.3** Vector search setup
  - `pgvector` extension
  - `MemoryEntry` with `embedding` column
  - KNN similarity search

- [ ] **3.4** Store refactor
  - Replace `store.py` dict-bucket with Prisma client
  - Keep interface identical (no route changes)
  - Run full test suite

- [ ] **3.5** Performance optimization
  - Indexes on `company_id`, `status`, `stage`
  - Connection pooling (PgBouncer)

**Deliverable:** PostgreSQL as primary DB, pglite removed from hot path

---

### PHASE 4 — Agent Orchestration v2
**الهدف:** من orchestrator basic إلى full autonomous swarm

- [ ] **4.1** CEO Agent → autonomous daily synthesis
  - Cron: 9 AM Mon-Fri
  - Reads agent reports from `/tmp/agent_*.txt`
  - Generates CEO daily report
  - Delivers via Telegram

- [ ] **4.2** Sub-agent cron jobs (7 agents)
  - B2B, CFO, CTO, COO, HR, CMO, CSM
  - Schedule: every 6h, `no_agent=true`
  - Write reports to `/tmp/agent_<role>_report.txt`

- [ ] **4.3** Agent-to-Agent messaging
  - `create_agent_run()` with task assignment
  - Status transitions: queued→running→done/failed
  - Approval-gated stops

- [ ] **4.4** Workflow automation
  - wf-lead-to-order: auto-create deal from qualified lead
  - wf-recruitment: auto-create employee from hired stage
  - wf-daily-standup: auto-collect status from agents

- [ ] **4.5** Human-in-the-loop
  - `/api/approvals` — pending approvals queue
  - SMS/Email notification on pending
  - Auto-escalation after 24h

**Deliverable:** 7-agent autonomous operation + CEO reporting

---

### PHASE 5 — Real-time & Integrations
**الهدف:** Live updates + third-party integrations

- [ ] **5.1** WebSocket notifications
  - `FastAPI WebSocket` for live updates
  - Client subscribes to entity channels
  - Push: new ticket, deal stage change, payment received

- [ ] **5.2** Telegram Bot integration
  - `/start` → menu with module access
  - Inline query: search contacts/deals/tickets
  - Push notifications for approvals

- [ ] **5.3** Stripe integration
  - `/api/integrations/stripe/payment-link`
  - Auto-generate payment links for invoices
  - Webhook: payment confirmation → update invoice status

- [ ] **5.4** HubSpot integration
  - Bi-directional sync contacts/leads
  - Webhook from HubSpot on deal stage change

- [ ] **5.5** WhatsApp Business API
  - Customer notifications
  - Support ticket creation from WhatsApp

**Deliverable:** Multi-channel platform, Stripe payments live

---

### PHASE 6 — Marketing Module (Full Build)
**الهدف:** إكمال Marketing كـ real module

- [ ] **6.1** Campaign management
  - POST/GET/PATCH/DELETE `/api/marketing/campaigns`
  - Types: email / SMS / social / ad
  - Status: draft / scheduled / running / completed

- [ ] **6.2** Email sequences
  - `/api/marketing/sequences`
  - Multi-step drip campaigns
  - Template variables: {{name}}, {{company}}, {{deal_value}}

- [ ] **6.3** Analytics dashboard
  - Open rate, click rate, conversion rate
  - Campaign ROI per channel
  - Lead source attribution

- [ ] **6.4** Marketing UI page
  - Campaign list with status badges
  - Sequence builder with drag-drop
  - Analytics charts (recharts)

**Deliverable:** Full marketing automation module

---

### PHASE 7 — Mobile App (Flutter)
**الهدف:** Native iOS/Android app

- [ ] **7.1** Flutter project setup
  ```bash
  flutter create md_os_app --org com.newtechkw
  cd md_os_app
  flutter pub add dio provider go_router
  ```

- [ ] **7.2** Auth + onboarding
  - Login with email/password
  - Biometric auth (Face ID / fingerprint)
  - Company selection for multi-tenant

- [ ] **7.3** Core module screens
  - Dashboard with KPI cards
  - CRM: contacts + deals list
  - HR: employee directory
  - Support: ticket list + create

- [ ] **7.4** Push notifications
  - FCM for Android
  - APNs for iOS
  - Deep links to specific records

- [ ] **7.5** Offline mode
  - Cache recent data locally
  - Sync on reconnect
  - Conflict resolution

**Deliverable:** App Store + Play Store submission

---

### PHASE 8 — Scale & Enterprise
**الهدف:** Enterprise-ready multi-tenant SaaS

- [ ] **8.1** Multitenancy
  - Subdomain-based tenant isolation
  - `company subdomain` → `company_id` mapping
  - Shared infrastructure, isolated data

- [ ] **8.2** White-label
  - Custom branding per tenant
  - Logo, colors, email templates
  - Custom domain support

- [ ] **8.3** Usage-based billing
  - Stripe subscription per tenant
  - Plans: Free / SMB / Enterprise
  - Usage meters: users, records, API calls

- [ ] **8.4** SLA monitoring
  - Uptime checks per tenant
  - Alert thresholds
  - Status page: `status.newtechkw.com`

- [ ] **8.5** Backup & DR
  - Daily PostgreSQL backup to S3
  - Point-in-time recovery
  - DR runbook documented

**Deliverable:** Multi-tenant SaaS platform, billing live

---

## 🔄 ترتيب التنفيذ — Execution Order

```
NOW ── Phase 0 (completion lock)
  │
W1 ─── Phase 1 (auth + security)
  │
W2-3 ── Phase 2 (Next.js)  ← هذا أهم من حيث UX
  │
W4-6 ── Phase 3 (PostgreSQL) ← بعد ما Next.js يشتغل
  │
W7-8 ── Phase 4 (Agent Swarm v2)
  │
W9-10 ─ Phase 5 (RT + Integrations)
  │
W11-12 ─ Phase 6 (Marketing)
  │
W13-16 ─ Phase 7 (Mobile)
  │
W17-20 ─ Phase 8 (Enterprise Scale)
```

---

## 📊 KPIs للتتبع

| Phase | KPI | Target |
|-------|-----|--------|
| P0 | Endpoints verified | 40/40 ✅ |
| P1 | Auth test pass rate | 100% |
| P2 | Dashboard LCP | < 2s |
| P2 | Lighthouse score | > 90 |
| P3 | DB query time p95 | < 50ms |
| P4 | Agent report delivery | 100% |
| P5 | WebSocket latency | < 200ms |
| P6 | Campaign send rate | 10k/hr |
| P7 | App store rating | 4.5+ |
| P8 | Tenant uptime | 99.9% |

---

## 🔴 المخاطر + mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Next.js migration breaks dashboard | High | High | Cutover gate + revert script |
| PostgreSQL migration data loss | Medium | Critical | Full backup before + verify counts |
| Agent swarm creates infinite loops | Medium | High | `no_agent=true` + approval gates |
| SSL cert expiry causes downtime | Low | High | Auto-renew via certbot |
| Mobile app rejection | Low | Medium | Pre-submission review checklist |

---

## 📁 الملفات الرئيسية المتأثرة

| Phase | الملفات |
|-------|---------|
| P0 | `api/bootstrap.py`, `api/main.py` |
| P1 | `api/auth.py`, `api/security.py`, `nginx conf` |
| P2 | `md-os-ui/` (new dir), `package.json` |
| P3 | `prisma/schema.prisma`, `api/store.py` |
| P4 | `api/orchestrator.py`, `workflows/*.json`, cron jobs |
| P5 | `api/websocket.py`, `api/integrations/` |
| P6 | `api/main.py` (marketing routes), `services.py` |
| P7 | `md-os-app/` (new dir) |
| P8 | `api/auth.py` (tenant middleware), billing |

---

## ✅ تقرير التسليم النهائي

عند إكمال كل phase، يتم تسليم:
1. التقرير التشغيلي (operational report)
2. الروابط الشغالة
3. التغييرات في الكود (git diff)
4. اختبارات النجاح
5. الوثائق المحدثة

**الآن:** تنفيذ Phase 0 — التثبيت النهائي → ثم Phase 1 → Phase 2

---
*MD-OS v2.0 — Building the AI-Native Business OS for Kuwait*
*© NewTech Kuwait — 2026*