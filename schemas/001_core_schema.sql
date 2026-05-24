-- MD-OS Core Schema v0.1
-- Multi-company, multi-project, multi-agent operating system

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE companies (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  industry text NOT NULL,
  status text NOT NULL DEFAULT 'active',
  settings jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workspaces (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid NOT NULL REFERENCES companies(id),
  name text NOT NULL,
  type text NOT NULL DEFAULT 'business',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid REFERENCES companies(id),
  email text UNIQUE NOT NULL,
  display_name text NOT NULL,
  role text NOT NULL DEFAULT 'member',
  permissions jsonb NOT NULL DEFAULT '[]',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE projects (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid NOT NULL REFERENCES companies(id),
  workspace_id uuid REFERENCES workspaces(id),
  name text NOT NULL,
  status text NOT NULL DEFAULT 'active',
  owner_agent_id uuid,
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE agents (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid REFERENCES companies(id),
  name text NOT NULL,
  role text NOT NULL,
  mission text NOT NULL,
  config jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE agent_teams (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid NOT NULL REFERENCES companies(id),
  name text NOT NULL,
  leader_agent_id uuid REFERENCES agents(id),
  member_agent_ids uuid[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE skills (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid REFERENCES companies(id),
  name text NOT NULL,
  description text,
  content text NOT NULL,
  tags text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflows (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid NOT NULL REFERENCES companies(id),
  name text NOT NULL,
  trigger jsonb NOT NULL,
  graph jsonb NOT NULL,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow_runs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_id uuid NOT NULL REFERENCES workflows(id),
  status text NOT NULL DEFAULT 'queued',
  input jsonb NOT NULL DEFAULT '{}',
  output jsonb NOT NULL DEFAULT '{}',
  error text,
  started_at timestamptz DEFAULT now(),
  finished_at timestamptz
);

CREATE TABLE tasks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid NOT NULL REFERENCES companies(id),
  project_id uuid REFERENCES projects(id),
  title text NOT NULL,
  description text,
  status text NOT NULL DEFAULT 'todo',
  priority text NOT NULL DEFAULT 'medium',
  owner_agent_id uuid REFERENCES agents(id),
  due_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE memories (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid REFERENCES companies(id),
  agent_id uuid REFERENCES agents(id),
  type text NOT NULL CHECK (type IN ('episodic','semantic','procedural')),
  content text NOT NULL,
  embedding vector(768),
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE approvals (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid NOT NULL REFERENCES companies(id),
  requested_by_agent_id uuid REFERENCES agents(id),
  category text NOT NULL,
  title text NOT NULL,
  risk_level text NOT NULL DEFAULT 'medium',
  payload jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'pending',
  decided_by uuid REFERENCES users(id),
  decided_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE api_connectors (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id uuid NOT NULL REFERENCES companies(id),
  name text NOT NULL,
  type text NOT NULL,
  auth_ref text,
  config jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'enabled',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE crm_contacts (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), company_id uuid NOT NULL REFERENCES companies(id), name text NOT NULL, email text, phone text, stage text DEFAULT 'lead', metadata jsonb DEFAULT '{}', created_at timestamptz DEFAULT now());
CREATE TABLE deals (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), company_id uuid NOT NULL REFERENCES companies(id), contact_id uuid REFERENCES crm_contacts(id), title text NOT NULL, value_kwd numeric(14,3) DEFAULT 0, stage text DEFAULT 'new', close_date date, created_at timestamptz DEFAULT now());
CREATE TABLE support_tickets (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), company_id uuid NOT NULL REFERENCES companies(id), contact_id uuid REFERENCES crm_contacts(id), subject text NOT NULL, status text DEFAULT 'open', priority text DEFAULT 'medium', created_at timestamptz DEFAULT now());
CREATE TABLE inventory_items (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), company_id uuid NOT NULL REFERENCES companies(id), sku text NOT NULL, name text NOT NULL, quantity numeric DEFAULT 0, reorder_point numeric DEFAULT 0, unit_cost_kwd numeric(14,3) DEFAULT 0, created_at timestamptz DEFAULT now());
CREATE TABLE invoices (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), company_id uuid NOT NULL REFERENCES companies(id), customer_id uuid REFERENCES crm_contacts(id), amount_kwd numeric(14,3) NOT NULL, status text DEFAULT 'draft', due_date date, created_at timestamptz DEFAULT now());
CREATE TABLE audit_logs (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), company_id uuid REFERENCES companies(id), actor_type text NOT NULL, actor_id uuid, action text NOT NULL, entity_type text, entity_id uuid, before jsonb, after jsonb, created_at timestamptz DEFAULT now());
