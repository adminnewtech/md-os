-- MD-OS Initial Schema
-- Run via: alembic or python -m api.migrations

BEGIN;

-- Companies
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    workspace_id TEXT DEFAULT 'default',
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    owner_agent_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_projects_company ON projects(company_id);
CREATE INDEX IF NOT EXISTS idx_projects_workspace ON projects(company_id, workspace_id);

-- Agents
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    mission TEXT NOT NULL,
    config JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agents_company ON agents(company_id);

-- Agent Teams
CREATE TABLE IF NOT EXISTS agent_teams (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    name TEXT NOT NULL,
    leader_agent_id TEXT,
    member_agent_ids TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_teams_company ON agent_teams(company_id);

-- Workflows
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    name TEXT NOT NULL,
    trigger JSONB NOT NULL DEFAULT '{}',
    graph JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_workflows_company ON workflows(company_id);

-- Workflow Runs
CREATE TABLE IF NOT EXISTS workflow_runs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    status TEXT DEFAULT 'queued',
    input JSONB DEFAULT '{}',
    output JSONB DEFAULT '{}',
    error TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow ON workflow_runs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    project_id TEXT REFERENCES projects(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'todo',
    priority TEXT DEFAULT 'medium',
    owner_agent_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tasks_company ON tasks(company_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Approvals
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    requested_by_agent_id TEXT,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    risk_level TEXT DEFAULT 'medium',
    payload JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    decided_by TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_approvals_company ON approvals(company_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    company_id TEXT,
    actor_type TEXT NOT NULL DEFAULT 'user',
    actor_id TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    before JSONB,
    after JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_company ON audit_logs(company_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- Agent Runs (Phase 2: state machine)
CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id),
    company_id TEXT NOT NULL REFERENCES companies(id),
    workflow_run_id TEXT REFERENCES workflow_runs(id),
    task_id TEXT REFERENCES tasks(id),
    status TEXT DEFAULT 'queued',
    input JSONB DEFAULT '{}',
    output JSONB DEFAULT '{}',
    error TEXT,
    waiting_approval_id TEXT REFERENCES approvals(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_company ON agent_runs(company_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);

-- Orchestrator Cycles (Phase 2: plan/delegate/monitor/report)
CREATE TABLE IF NOT EXISTS orchestrator_cycles (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    task_description TEXT NOT NULL,
    agent_ids TEXT[] DEFAULT '{}',
    context JSONB DEFAULT '{}',
    max_parallel INT DEFAULT 4,
    status TEXT DEFAULT 'planning',
    plan JSONB DEFAULT '[]',
    agent_runs JSONB DEFAULT '[]',
    result JSONB DEFAULT '{}',
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_orchestrator_cycles_company ON orchestrator_cycles(company_id);
CREATE INDEX IF NOT EXISTS idx_orchestrator_cycles_status ON orchestrator_cycles(status);

-- Memory Store (Phase 2: vector memory)
CREATE TABLE IF NOT EXISTS memory_entries (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    agent_id TEXT,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_memory_company ON memory_entries(company_id);
CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_entries(company_id, key);
-- HNSW index for vector similarity search (pgvector >= 0.5)
DO $$
BEGIN
    CREATE INDEX IF NOT EXISTS idx_memory_embedding ON memory_entries USING hnsw(embedding vector_cosine_ops);
EXCEPTION WHEN OTHERS THEN
    -- pgvector < 0.5: use ivfflat instead
    CREATE INDEX IF NOT EXISTS idx_memory_embedding ON memory_entries USING ivfflat(embedding vector_cosine_ops);
END $$;

COMMIT;