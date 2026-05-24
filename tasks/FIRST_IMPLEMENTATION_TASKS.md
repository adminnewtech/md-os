# First Implementation Tasks v0.1

## Phase 1 — Foundation
1. Create DB migrations from `schemas/001_core_schema.sql`
2. Create seed script for default company: MD Platform
3. Import 25 agent definitions into `agents` table
4. Import workflow JSON files into `workflows` table
5. Build approval guard middleware
6. Build audit log middleware
7. Build task creation + assignment API
8. Build agent registry API
9. Build workflow run skeleton
10. Build Paperclip dashboard shell

## Phase 2 — Orchestration
1. Hermes Orchestrator service: plan → delegate → monitor → report
2. Agent run lifecycle: queued/running/waiting_approval/done/failed
3. Memory write/search adapter: GBrain/PGLite + vector
4. Tool permission resolver per agent
5. Human approval interrupt mechanism

## Phase 3 — Business Modules
1. CRM contacts + deals
2. Support tickets
3. Finance invoices
4. Inventory SKU/reorder
5. HR recruitment/onboarding
6. Logistics shipments/routes

## Phase 4 — Improvement Engine
1. Capture failures → classify root cause
2. Generate improvement backlog item
3. Propose skill/prompt/workflow patch
4. Require approval only for risky changes
5. Track before/after metrics
