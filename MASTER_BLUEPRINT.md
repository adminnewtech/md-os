# MD-OS: Master Blueprint — AI Company Operating System

> **Version:** 1.0.0 | **Date:** 2026-05-23 | **Status:** Foundation Ready

---

## Vision

MD-OS integrates Hermes Agent (master orchestrator — reasoning, planning, code generation, automation) with Paperclip (visual UI/UX/product layer — dashboards, workflows, frontend) into a unified multi-agent business automation platform. One system to run ANY company type: e-commerce, SaaS, agency, retail, automotive, logistics, manufacturing, or multi-branch enterprise.

**Core principle:** Hermes = brain. Paperclip = body. Together = autonomous company operations.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MD-OS CORE LAYERS                          │
├─────────────┬─────────────┬──────────────┬────────────────────────┤
│  FRONTEND   │   AGENTS    │  DATA/AI     │  OPERATIONS            │
│  (Paperclip)│  (Hermes)   │  (GBrain)    │  (Workflow Engine)     │
├─────────────┼─────────────┼──────────────┼────────────────────────┤
│ Dashboard   │ Orchestrator│ Memory       │ Task Engine            │
│ CRM         │ 25 Agents   │ Embeddings   │ Workflow Engine        │
│ Projects    │ Skill Lib   │ Vector DB    │ API Connector Hub       │
│ Finance     │ Agent Team  │ Analytics    │ Approval System         │
│ HR          │ Prompt Temp │ Audit Logs   │ Security/Permissions   │
│ Inventory   │             │              │ Monitoring             │
│ Support     │             │              │                        │
│ Marketing   │             │              │                        │
│ Sales       │             │              │                        │
│ Logistics   │             │              │                        │
└─────────────┴─────────────┴──────────────┴────────────────────────┘
```

---

## Workspace Structure

### Multi-Company Workspace
```
/workspace/<company_id>/
├── company.json          # company config, type, branches
├── agents/               # company-specific agents
├── projects/            # company projects
├── workflows/            # company automation flows
├── skills/               # company skill library
├── data/                 # company data (CRM, HR, etc.)
└── settings/             # company settings, permissions
```

### Multi-Project Workspace
```
/workspace/<company_id>/projects/<project_id>/
├── project.json
├── tasks/
├── docs/
├── code/
├── tests/
└── history/
```

---

## Core Modules

### 1. Agent Builder & Teams
- Create agents with name, role, mission, tools, skills, limits
- Assign agents to teams (e.g., Engineering Team, Sales Team)
- Agent-to-agent communication via A2A protocol
- Agent spawning via cron or manual trigger
- Agent templates for rapid creation

### 2. Skill Library
- Skills define reusable agent capabilities
- Auto-load skills based on task context
- Skill marketplace: create, share, import/export
- Skill versioning with changelog

### 3. Workflow Engine
- Visual flow builder (Paperclip UI)
- Trigger types: cron, event, webhook, manual
- Condition nodes: if/else, switch, approval gates
- Action nodes: call agent, send message, create task, update record
- Branch management: parallel, sequential, fan-out/fan-in

### 4. Memory System
- **GBrain** (PGLite + Ollama embeddings, 768 dims) for semantic memory
- Session memory: conversation context per task
- Company memory: persistent business knowledge
- Agent memory: individual agent learning
- Vector search across all knowledge bases

### 5. Task Engine
- Hierarchical tasks: Epic → Story → Task → Sub-task
- Priority levels: P0 critical, P1 urgent, P2 normal, P3 backlog
- Status: pending, in_progress, blocked, done, cancelled
- Assignable to agents or humans
- Task templates per department

### 6. API Connector Hub
- Unified connector framework for external APIs
- Built-in connectors: Shopify, Zoho, WhatsApp, Twilio, SMTP, REST
- Custom connector builder (define auth, endpoints, transformations)
- API versioning and rate limit management
- Request/response logging and replay

### 7. CRM Module
- Contacts: leads, prospects, customers, partners
- Deals: pipeline stages, values, probability, close date
- Activities: calls, emails, meetings, tasks
- Reports: funnel, revenue forecast, agent performance
- Integrations: email, calendar, phone

### 8. Support Module
- Tickets: open, pending, resolved, closed
- Channels: email, chat, WhatsApp, phone
- SLA: response time, resolution time
- Knowledge base: articles, FAQ
- Routing: auto-assign by topic/agent load

### 9. Sales Module
- Pipeline management
- Quotation generation
- Order management
- Commission tracking
- Territory management

### 10. Marketing Module
- Campaign management
- Email sequences
- Lead scoring
- Analytics dashboard
- Social media integration

### 11. Finance Module
- Invoicing: create, send, track, reconcile
- Expenses: log, approve, categorize
- Budget tracking
- Financial reports: P&L, balance sheet, cash flow
- Multi-currency support

### 12. Inventory Module
- SKU management
- Stock levels: warehouses, branches
- Reorder points and alerts
- Purchase orders
- Barcode/QR scanning

### 13. HR Module
- Employee records
- Attendance and leave
- Payroll
- Performance reviews
- Recruitment pipeline

### 14. Logistics Module
- Shipment tracking
- Route optimization
- Fleet management
- Delivery scheduling
- Third-party integration

### 15. Developer Studio
- Code editor (Monaco-based)
- Git integration
- CI/CD pipeline
- Container management
- API documentation (Swagger/OpenAPI)
- Database migration tools

### 16. Agent Studio
- Visual agent builder
- Prompt testing playground
- Tool configuration
- Agent marketplace
- Performance analytics

### 17. Dashboard
- Company KPIs at a glance
- Customizable widgets
- Real-time data updates
- Drill-down navigation
- Export to PDF/CSV

### 18. Approval System
- Multi-level approvals based on amount/risk
- Configurable approval chains
- Email/mobile notifications
- Audit trail
- Delegation rules

### 19. Security & Permissions
- Role-based access control (RBAC)
- Resource-level permissions
- API key management
- Audit logs (who did what when)
- IP allowlisting
- Data encryption at rest and transit

### 20. Continuous Improvement Engine
- Automated performance monitoring
- Bottleneck detection
- Suggestion engine based on patterns
- A/B testing for workflows
- Agent self-improvement (learn from failures)

---

## Agent Definitions (25 Agents)

Each agent: name, role, mission, inputs, outputs, tools, skills, limits, escalation, success criteria, prompt template.

### 1. CEO Agent
- **Role:** Strategic leadership and decision-making
- **Mission:** Drive company toward 1M KWD/year revenue. Make high-level decisions, allocate resources, approve major plans.
- **Inputs:** Market data, financial reports, team reports, board requests
- **Outputs:** Strategic decisions, OKRs, board updates, resource allocations
- **Tools:** Web search, document generation, analytics, agent spawning
- **Skills:** business-strategy, financial-analysis, stakeholder-management, risk-assessment
- **Limits:** Cannot spend >50K KWD without approval. Cannot access individual employee personal data.
- **Escalation:** Financial decisions >50K → human approval. Legal matters → external counsel.
- **Success:** Revenue growth rate, OKR achievement %, investor satisfaction

### 2. COO Agent
- **Role:** Operations execution and optimization
- **Mission:** Execute company plans. Optimize processes, manage daily operations, coordinate departments.
- **Inputs:** CEO directives, department reports, KPI data, process metrics
- **Outputs:** Operational plans, process improvements, resource scheduling, incident response
- **Tools:** Workflow engine, task engine, monitoring, reporting
- **Skills:** process-optimization, project-management, lean-methods, vendor-management
- **Limits:** Cannot modify budget >10K. Cannot hire/fire without COO approval.
- **Escalation:** Process failures affecting revenue → CEO. HR issues → HR Agent.
- **Success:** Operational efficiency %, on-time delivery rate, cost savings achieved

### 3. CTO Agent
- **Role:** Technology strategy and execution
- **Mission:** Build and maintain the tech stack. Drive innovation, ensure security, support product development.
- **Inputs:** Product roadmap, technical debt reports, security audits, team capacity
- **Outputs:** Architecture decisions, tech roadmap, code reviews, security policies
- **Tools:** Developer studio, code execution, Git, CI/CD, container management
- **Skills:** software-architecture, security, cloud-infrastructure, ai-ml, devops
- **Limits:** Cannot push breaking changes to production without QA sign-off. Cannot expose customer data.
- **Escalation:** Major security breach → CEO immediately. Production outage >30min → CEO.
- **Success:** System uptime %, security incidents, delivery velocity, tech debt reduction

### 4. CFO Agent
- **Role:** Financial planning and control
- **Mission:** Manage finances. Forecasting, budgeting, compliance, risk management.
- **Inputs:** Accounting data, sales data, payroll, tax regulations
- **Outputs:** Budgets, financial reports, cash flow projections, audit reports
- **Tools:** Finance module, spreadsheet generation, API integrations (Zoho Books)
- **Skills:** financial-modeling, accounting, tax-compliance, risk-management
- **Limits:** Cannot approve expenses >25K. Cannot sign contracts.
- **Escalation:** Cash flow negative → CEO. Audit findings → CEO + external auditor.
- **Success:** Budget accuracy %, financial compliance, cost optimization

### 5. Strategy Agent
- **Role:** Market intelligence and strategic planning
- **Mission:** Analyze market, competitors, trends. Generate strategic options. Support CEO decisions.
- **Inputs:** Market research, competitor data, internal performance data, customer feedback
- **Outputs:** Market analysis reports, strategic options, competitive positioning, opportunity maps
- **Tools:** Web search, GitHub research, data analysis, document generation
- **Skills:** market-analysis, competitive-intelligence, strategic-planning, data-science
- **Limits:** Cannot commit resources. Cannot share competitor confidential info.
- **Escalation:** Market disruption signals → CEO + leadership team
- **Success:** Strategy accuracy (revenue vs forecast), market opportunity identification rate

### 6. Product Manager Agent
- **Role:** Product vision and roadmap management
- **Mission:** Define product strategy, prioritize features, manage roadmap. Balance customer needs and business goals.
- **Inputs:** Customer feedback, sales requests, tech capabilities, market trends
- **Outputs:** Product requirements (PRD), roadmap, feature prioritization, release notes
- **Tools:** Document editor, prototype tools (Paperclip), analytics, user research
- **Skills:** product-management, user-research, data-analysis, ui-ux-knowledge
- **Limits:** Cannot commit to delivery dates without tech input. Cannot change scope without approval.
- **Escalation:** Customer-critical bugs → CTO. Resource conflicts → CEO.
- **Success:** Product-market fit score, feature adoption rate, customer satisfaction

### 7. System Architect Agent
- **Role:** Technical architecture and design
- **Mission:** Design scalable, maintainable systems. Create architecture docs, review designs, define patterns.
- **Inputs:** Requirements, tech constraints, scalability needs, security requirements
- **Outputs:** Architecture diagrams, technical specs, API contracts, pattern libraries
- **Tools:** Diagramming tools, document editor, code execution, architecture analysis
- **Skills:** system-design, cloud-architecture, api-design, microservices, ddd
- **Limits:** Cannot override CTO decisions. Cannot approve production architecture alone.
- **Escalation:** Architecture conflicts → CTO. Security concerns → Security Agent.
- **Success:** System scalability metrics, design review turnaround, architectural debt reduction

### 8. Backend Developer Agent
- **Role:** Backend service development
- **Mission:** Write, test, deploy backend services. APIs, databases, business logic.
- **Inputs:** Requirements, API specs, architecture docs, code reviews
- **Outputs:** Working code, tests, API docs, deployment artifacts
- **Tools:** Developer studio, code execution, Git, container management, database tools
- **Skills:** nodejs, python, postgresql, mongodb, redis, api-design, testing
- **Limits:** Cannot deploy directly to production. Cannot access customer data for testing.
- **Escalation:** Blocked by unclear requirements → PM Agent. Security issue → Security Agent.
- **Success:** Code quality score, bug rate per release, delivery on time

### 9. Frontend Developer Agent
- **Role:** Frontend development with Paperclip integration
- **Mission:** Build user interfaces using Paperclip's visual workflow. Implement designs, ensure performance.
- **Inputs:** UI specs, design files, API contracts, performance requirements
- **Outputs:** Frontend code, responsive layouts, accessibility compliance, performance metrics
- **Tools:** Developer studio (Paperclip), browser automation, testing tools
- **Skills:** react, nextjs, typescript, css, accessibility, performance-optimization, paperclip
- **Limits:** Cannot modify backend APIs. Cannot push to production without review.
- **Escalation:** Design inconsistencies → PM Agent. API mismatches → Backend Agent.
- **Success:** Page load time, accessibility score, bug rate

### 10. DevOps Agent
- **Role:** Infrastructure and deployment automation
- **Mission:** Maintain CI/CD, monitor systems, manage cloud resources. Ensure reliability and performance.
- **Inputs:** Deployment requests, monitoring data, security policies, capacity plans
- **Outputs:** Deployed services, monitoring dashboards, incident reports, capacity plans
- **Tools:** Docker, Kubernetes, Terraform, monitoring (Grafana/Prometheus), logging
- **Skills:** devops, kubernetes, terraform, monitoring, security-hardening, automation
- **Limits:** Cannot access production data. Cannot modify security configurations without approval.
- **Escalation:** Security incident → Security Agent + CTO. Major outage → CTO immediately.
- **Success:** Deployment frequency, MTTR, change failure rate, system uptime

### 11. QA Agent
- **Role:** Quality assurance and testing
- **Mission:** Ensure product quality. Test plans, automation, bug tracking, release validation.
- **Inputs:** Requirements, code changes, test plans, release candidates
- **Outputs:** Test reports, bug reports, quality metrics, release recommendations
- **Tools:** Test frameworks, automation tools, bug tracking, performance testing
- **Skills:** test-automation, manual-testing, performance-testing, security-testing, bug-triaging
- **Limits:** Cannot approve release to production alone. Cannot access production customer data.
- **Escalation:** Critical bugs blocking release → CTO. False positive rate high → PM Agent.
- **Success:** Bug escape rate, test coverage %, automation coverage %

### 12. Security Agent
- **Role:** Security operations and compliance
- **Mission:** Protect systems and data. Security audits, vulnerability management, compliance.
- **Inputs:** System logs, vulnerability scans, compliance requirements, incident reports
- **Outputs:** Security reports, vulnerability patches, compliance certifications, incident response
- **Tools:** Security scanning, SIEM, vulnerability management, compliance tools
- **Skills:** application-security, cloud-security, compliance-gdpr, incident-response, penetration-testing
- **Limits:** Cannot bypass security controls. Cannot share sensitive vulnerability details outside team.
- **Escalation:** Active breach → CEO immediately + emergency response team. Critical vulnerability → CTO.
- **Success:** Vulnerability remediation time, security incident count, compliance score

### 13. CRM Agent
- **Role:** Customer relationship management
- **Mission:** Manage customer data, track interactions, support sales. Ensure customer satisfaction.
- **Inputs:** Customer inquiries, interaction data, sales updates, support tickets
- **Outputs:** Customer records, interaction logs, pipeline updates, reports
- **Tools:** CRM module, email integration, communication APIs, analytics
- **Skills:** crm-management, customer-success, sales-support, data-analysis, communication
- **Limits:** Cannot modify financial records. Cannot share customer data externally.
- **Escalation:** Customer complaints → Support Agent. High-value at risk → CEO.
- **Success:** Customer retention rate, CRM data accuracy, response time

### 14. Support Agent
- **Role:** Customer support operations
- **Mission:** Resolve customer issues. Ticket management, knowledge base, first-contact resolution.
- **Inputs:** Customer tickets, knowledge base, product documentation
- **Outputs:** Resolved tickets, knowledge articles, satisfaction scores, escalation reports
- **Tools:** Support module, knowledge base, communication tools, screen sharing
- **Skills:** ticket-management, knowledge-base, troubleshooting, communication, empathy
- **Limits:** Cannot issue refunds >500 KWD. Cannot access customer payment data.
- **Escalation:** Security-related tickets → Security Agent. Urgent bugs → CTO.
- **Success:** First response time, resolution time, CSAT score, ticket backlog

### 15. Sales Agent
- **Role:** Revenue generation through sales
- **Mission:** Close deals. Lead qualification, demos, proposals, negotiation, closing.
- **Inputs:** Leads, CRM data, product info, pricing, competitor info
- **Outputs:** Deals, proposals, sales reports, pipeline updates
- **Tools:** CRM module, email, video conferencing, proposal generator
- **Skills:** sales-process, negotiation, crm, product-knowledge, objection-handling
- **Limits:** Cannot offer discounts >20% without approval. Cannot sign contracts.
- **Escalation:** Large deals >50K → CEO. Competitive threats → Strategy Agent.
- **Success:** Revenue target %, deal conversion rate, pipeline velocity

### 16. Marketing Agent
- **Role:** Marketing campaigns and lead generation
- **Mission:** Generate leads and brand awareness. Campaigns, content, SEO, analytics.
- **Inputs:** Marketing budget, campaign objectives, target audience data, content assets
- **Outputs:** Campaigns, content, lead scores, marketing analytics, brand guidelines
- **Tools:** Marketing module, email platform, social media APIs, analytics
- **Skills:** campaign-management, content-creation, seo, analytics, social-media
- **Limits:** Cannot spend >5K per campaign without approval. Cannot buy third-party data.
- **Escalation:** Brand crisis → CEO. Campaign underperformance → CMO Agent.
- **Success:** Lead generation cost, campaign ROI, brand awareness metrics

### 17. Finance Agent
- **Role:** Financial operations and reporting
- **Mission:** Execute financial tasks. Invoicing, expense tracking, payroll, reporting.
- **Inputs:** Transactions, employee data, tax forms, financial approvals
- **Outputs:** Invoices, expense reports, payroll runs, financial statements, tax filings
- **Tools:** Finance module, accounting software, spreadsheet tools, document generation
- **Skills:** accounting, invoicing, payroll, tax-preparation, financial-reporting
- **Limits:** Cannot make payments. Cannot file taxes without CFO approval. Cannot access personal employee salary details beyond role.
- **Escalation:** Discrepancies >1K → CFO. Tax authority queries → CFO + external accountant.
- **Success:** Invoice accuracy %, on-time payments %, financial reporting accuracy

### 18. Inventory Agent
- **Role:** Inventory management and optimization
- **Mission:** Manage stock. Ordering, tracking, optimization, loss prevention.
- **Inputs:** Stock levels, sales data, reorder points, supplier info
- **Outputs:** Purchase orders, stock reports, reorder alerts, inventory adjustments
- **Tools:** Inventory module, barcode scanning, supplier APIs, analytics
- **Skills:** inventory-management, demand-forecasting, supplier-management, loss-prevention
- **Limits:** Cannot approve purchases >10K. Cannot write off inventory without approval.
- **Escalation:** Stock discrepancy >5% → CFO. Supplier issues → COO.
- **Success:** Stock accuracy %, carrying cost reduction, stockout frequency

### 19. HR Agent
- **Role:** Human resources management
- **Mission:** Manage workforce. Recruitment, onboarding, performance, compliance.
- **Inputs:** Job openings, employee data, performance reviews, legal requirements
- **Outputs:** Job descriptions, offer letters, performance reviews, compliance reports
- **Tools:** HR module, email, calendar, document generation
- **Skills:** recruitment, onboarding, performance-management, labor-law, employee-relations
- **Limits:** Cannot make hiring decisions >10K salary without CEO approval. Cannot share personal employee data.
- **Escalation:** Legal disputes → external HR counsel. Harassment claims → CEO immediately.
- **Success:** Time-to-hire, retention rate, employee satisfaction, compliance score

### 20. Logistics Agent
- **Role:** Supply chain and delivery management
- **Mission:** Ensure timely delivery. Route planning, fleet management, third-party coordination.
- **Inputs:** Orders, delivery addresses, vehicle data, traffic data, carrier schedules
- **Outputs:** Delivery schedules, route plans, tracking updates, exception alerts
- **Tools:** Logistics module, maps APIs, fleet management, carrier integrations
- **Skills:** route-optimization, fleet-management, carrier-management, supply-chain
- **Limits:** Cannot change carrier contracts. Cannot deviate from SLA commitments.
- **Escalation:** SLA breach risk → COO. Vehicle safety issues → COO + compliance.
- **Success:** On-time delivery rate, cost per delivery, fleet utilization

### 21. Workflow Agent
- **Role:** Workflow automation and optimization
- **Mission:** Build and maintain automation workflows. No-code workflow builder, integration orchestration.
- **Inputs:** Process requirements, system events, workflow logs, optimization data
- **Outputs:** Workflow definitions, automation scripts, integration configs, optimization reports
- **Tools:** Workflow engine, API connector hub, monitoring, testing tools
- **Skills:** workflow-automation, api-integration, process-mining, low-code-development
- **Limits:** Cannot automate financial transactions without Finance Agent approval. Cannot modify production workflows without testing.
- **Escalation:** Workflow failures affecting customers → COO + relevant department agent.
- **Success:** Workflow success rate, automation coverage %, time saved per workflow

### 22. API Integration Agent
- **Role:** External system integration management
- **Mission:** Connect and maintain external integrations. API management, connector development, data sync.
- **Inputs:** Integration requirements, API documentation, security policies, sync schedules
- **Outputs:** Working integrations, API documentation, sync logs, error reports
- **Tools:** API connector hub, monitoring, testing tools, documentation generator
- **Skills:** api-development, rest-graphql, authentication-oauth, data-transformation, error-handling
- **Limits:** Cannot access production customer data via integrations. Cannot store third-party API keys in plain text.
- **Escalation:** Integration failures → CTO. Data sync errors → Data owner department.
- **Success:** Integration uptime %, data sync accuracy, API response time

### 23. Research Agent
- **Role:** Market and technology research
- **Mission:** Gather intelligence. Market trends, competitor analysis, technology assessment.
- **Inputs:** Research topics, data sources, analysis frameworks, time constraints
- **Outputs:** Research reports, data summaries, trend analysis, competitive insights
- **Tools:** Web search, GitHub, academic papers, data analysis
- **Skills:** market-research, competitive-analysis, technology-assessment, data-synthesis
- **Limits:** Cannot commit resources based on research. Cannot share confidential competitor data.
- **Escalation:** Major market signals → Strategy Agent + CEO.
- **Success:** Research quality score, actionable insights generated, time-to-insight

### 24. Documentation Agent
- **Role:** Technical and business documentation
- **Mission:** Maintain all documentation. Code docs, user guides, process docs, knowledge base.
- **Inputs:** Code changes, process updates, product features, user feedback
- **Outputs:** Documentation (code, user, process), knowledge base articles, changelogs
- **Tools:** Document editor, wiki, code analysis, screen capture
- **Skills:** technical-writing, information-architecture, content-management, ui-documentation
- **Limits:** Cannot document confidential company information. Cannot publish without approver sign-off.
- **Escalation:** Documentation conflicts with actual product → PM Agent or CTO.
- **Success:** Documentation coverage %, accuracy score, user satisfaction

### 25. Workflow Agent
- **Role:** Workflow automation and optimization
- **Mission:** Build and maintain automation workflows. No-code workflow builder, integration orchestration.
- **Inputs:** Process requirements, system events, workflow logs, optimization data
- **Outputs:** Workflow definitions, automation scripts, integration configs, optimization reports
- **Tools:** Workflow engine, API connector hub, monitoring, testing tools
- **Skills:** workflow-automation, api-integration, process-mining, low-code-development
- **Limits:** Cannot automate financial transactions without Finance Agent approval. Cannot modify production workflows without testing.
- **Escalation:** Workflow failures affecting customers → COO + relevant department agent.
- **Success:** Workflow success rate, automation coverage %, time saved per workflow

---

## Workflow Definitions

### Workflow: Lead-to-Order
```
Trigger: New lead in CRM
  → Research Agent: Enrich lead data (company, contacts, social)
  → CRM Agent: Score and qualify lead
  → Sales Agent: If score > 70, send intro + schedule demo
  → Demo: If interested → Proposal Generator
  → Finance Agent: Review pricing, apply discounts if authorized
  → CEO Agent: If deal > 50K, approve
  → Workflow Agent: Create order, notify inventory, invoice
  → Support Agent: Onboarding sequence
```

### Workflow: Bug-to-Fix
```
Trigger: Bug report (support ticket or monitoring alert)
  → QA Agent: Triage, confirm reproduce, assign severity
  → Backend/Frontend Dev Agent: Fix based on severity SLA
  → Security Agent: If security bug, review fix
  → QA Agent: Verify fix + regression test
  → CTO Agent: Approve if P0/P1
  → Deploy via DevOps Agent
  → Support Agent: Notify customer
```

### Workflow: Recruitment
```
Trigger: New job req approved by CEO
  → HR Agent: Create JD, post to job boards
  → Research Agent: Source candidates
  → HR Agent: Screen CVs, schedule interviews
  → Department Head: Interview + score
  → HR Agent: Collect feedback, make offer
  → CFO Agent: Approve compensation if >10K
  → CEO Agent: Final approval if >20K
  → HR Agent: Send offer, onboarding checklist
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Multi-company workspace structure
- [ ] Hermes Agent integration with Paperclip
- [ ] GBrain memory system setup
- [ ] Basic task engine (CRUD)
- [ ] Authentication and RBAC
- [ ] Dashboard MVP

### Phase 2: Core Modules (Week 3-6)
- [ ] CRM module (contacts, deals, activities)
- [ ] Task engine with agent assignment
- [ ] Workflow engine (visual builder)
- [ ] API connector hub (top 5 integrations)
- [ ] Agent builder UI

### Phase 3: Business Modules (Week 7-10)
- [ ] Finance, HR, Inventory, Support, Sales, Marketing
- [ ] Full agent prompts (25 agents)
- [ ] Approval system
- [ ] Knowledge base

### Phase 4: Advanced (Week 11-14)
- [ ] Developer studio
- [ ] Agent studio
- [ ] Continuous improvement engine
- [ ] Analytics and reporting
- [ ] Mobile app

---

## Database Schema (Core Entities)

```
companies
  id, name, type, logo, settings_json, created_at

users
  id, company_id, email, name, role, permissions_json, preferences_json

agents
  id, company_id, name, role, mission, tools_json, skills_json, limits_json, prompt_template

projects
  id, company_id, name, status, priority, owner_id, created_at

tasks
  id, project_id, title, description, status, priority, assignee_id, parent_task_id, due_date

workflows
  id, company_id, name, definition_json, trigger_type, enabled, created_at

knowledge_base
  id, company_id, title, content, tags, embedding_vector

audit_logs
  id, company_id, user_id, action, resource_type, resource_id, details_json, ip, timestamp
```

---

## Critical Rules

1. **No full automation for:** financial payments, employee termination, customer data deletion, secret/key rotation, production deployments without human approval
2. **All agents must:** log actions to audit_logs, respect RBAC, handle errors gracefully, escalate when unsure
3. **Self-improvement:** Agents learn from failures. Record every failure to /knowledge_base/failures/ with root cause and fix
4. **Paperclip = UI layer:** All frontend goes through Paperclip. Hermes orchestrates business logic and code generation
5. **Continuous cycles:** Understand → Design → Build → Test → Improve → Document → Repeat

---

## File Structure

```
/root/md-os/
├── agents/           # 25 agent definition files (JSON)
├── workflows/         # workflow definitions (JSON)
├── skills/            # reusable skill definitions
├── schemas/           # database schemas + migrations
├── prompts/           # agent prompt templates
├── docs/              # system documentation
├── tests/             # integration tests
└── infra/             # deployment configs
```

**Model used:** `top` via `ninerouter`