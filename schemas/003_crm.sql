-- MD-OS CRM Schema
-- Contacts, Leads, Deals, Pipeline

BEGIN;

-- Contacts
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    workspace_id TEXT DEFAULT 'default',
    first_name TEXT NOT NULL DEFAULT '',
    last_name TEXT NOT NULL DEFAULT '',
    email TEXT,
    phone TEXT,
    title TEXT,
    company_name TEXT,
    source TEXT DEFAULT 'manual',
    tags TEXT[] DEFAULT '{}',
    custom_fields JSONB DEFAULT '{}',
    owner_agent_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(company_id, email);

-- Leads
CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    workspace_id TEXT DEFAULT 'default',
    contact_id TEXT REFERENCES contacts(id),
    title TEXT NOT NULL,
    status TEXT DEFAULT 'new' CHECK (status IN ('new','contacted','qualified','unqualified','converted','lost')),
    source TEXT DEFAULT 'manual',
    score INTEGER DEFAULT 0,
    assigned_agent_id TEXT,
    notes TEXT,
    custom_fields JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    converted_at TIMESTAMPTZ,
    converted_to_deal_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(company_id, status);

-- Deals
CREATE TABLE IF NOT EXISTS deals (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id),
    workspace_id TEXT DEFAULT 'default',
    title TEXT NOT NULL,
    value DECIMAL(15,2) DEFAULT 0,
    currency TEXT DEFAULT 'USD',
    stage TEXT DEFAULT 'prospecting' CHECK (stage IN ('prospecting','qualification','proposal','negotiation','closed_won','closed_lost')),
    probability INTEGER DEFAULT 10 CHECK (probability >= 0 AND probability <= 100),
    contact_id TEXT REFERENCES contacts(id),
    lead_id TEXT REFERENCES leads(id),
    owner_agent_id TEXT,
    expected_close_date DATE,
    notes TEXT,
    custom_fields JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_deals_company ON deals(company_id);
CREATE INDEX IF NOT EXISTS idx_deals_stage ON deals(company_id, stage);

-- Deal Activity Log
CREATE TABLE IF NOT EXISTS deal_activities (
    id TEXT PRIMARY KEY,
    deal_id TEXT NOT NULL REFERENCES deals(id),
    company_id TEXT NOT NULL REFERENCES companies(id),
    activity_type TEXT NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_deal_activities_deal ON deal_activities(deal_id);

COMMIT;