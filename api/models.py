from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CompanyCreate(ApiModel):
    name: str
    industry: str
    status: str = "active"
    settings: dict[str, Any] = Field(default_factory=dict)


class Company(CompanyCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class ProjectCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    name: str
    status: str = "active"
    owner_agent_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Project(ProjectCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class AgentCreate(ApiModel):
    company_id: str
    name: str
    role: str
    mission: str
    config: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"


class Agent(AgentCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class AgentTeamCreate(ApiModel):
    company_id: str
    name: str
    leader_agent_id: str | None = None
    member_agent_ids: list[str] = Field(default_factory=list)


class AgentTeam(AgentTeamCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class WorkflowCreate(ApiModel):
    company_id: str
    name: str
    trigger: dict[str, Any]
    graph: dict[str, Any]
    status: str = "active"


class Workflow(WorkflowCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class WorkflowRunCreate(ApiModel):
    input: dict[str, Any] = Field(default_factory=dict)


class WorkflowRun(ApiModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    status: Literal["queued", "running", "waiting_approval", "done", "failed"] = "queued"
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class TaskCreate(ApiModel):
    company_id: str
    project_id: str | None = None
    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    owner_agent_id: str | None = None


class Task(TaskCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class ApprovalCreate(ApiModel):
    company_id: str
    requested_by_agent_id: str | None = None
    category: str
    title: str
    risk_level: str = "medium"
    payload: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"


class Approval(ApprovalCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    decided_by: str | None = None


class ApprovalDecision(ApiModel):
    decision: Literal["approved", "rejected"]
    decided_by: str


class AgentRunApprovalRequest(ApiModel):
    category: str
    title: str
    risk_level: str = "medium"
    payload: dict[str, Any] = Field(default_factory=dict)


# Agent Run for orchestration (Phase 2)
class AgentRunCreate(ApiModel):
    agent_id: str
    company_id: str
    workflow_run_id: str | None = None
    task_id: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)


class AgentRun(AgentRunCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["queued", "running", "waiting_approval", "done", "failed"] = "queued"
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    waiting_approval_id: str | None = None


class AgentRunTransition(ApiModel):
    to_status: Literal["queued", "running", "waiting_approval", "done", "failed"]


class MemoryEntryCreate(ApiModel):
    company_id: str
    agent_id: str | None = None
    key: str
    value: str
    embedding: list[float] = Field(min_length=768, max_length=768)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(MemoryEntryCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class MemorySearchRequest(ApiModel):
    query_embedding: list[float] = Field(min_length=768, max_length=768)
    top_k: int = Field(default=5, ge=1, le=50)
    agent_id: str | None = None
    key_prefix: str | None = None


class AuditLog(ApiModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    company_id: str | None = None
    actor_type: str
    actor_id: str | None = None
    action: str
    entity_type: str
    entity_id: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None


# CEO Daily Synthesis Report
class CEODailyReportRequest(ApiModel):
    period_start: str | None = None
    period_end: str | None = None


class CEODailyReport(ApiModel):
    company_id: str
    generated_at: str
    period_start: str
    period_end: str
    summary: dict[str, Any]


# ── CRM Models ────────────────────────────────────────────────────────────────

class ContactCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    first_name: str = ""
    last_name: str = ""
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    company_name: str | None = None
    source: str = "manual"
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    owner_agent_id: str | None = None


class Contact(ContactCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class LeadCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    contact_id: str | None = None
    title: str
    status: Literal["new", "contacted", "qualified", "unqualified", "converted", "lost"] = "new"
    source: str = "manual"
    score: int = 0
    assigned_agent_id: str | None = None
    notes: str | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class Lead(LeadCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    converted_at: str | None = None
    converted_to_deal_id: str | None = None


class DealCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    title: str
    value: float = 0
    currency: str = "USD"
    stage: Literal[
        "prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"
    ] = "prospecting"
    probability: int = 10
    contact_id: str | None = None
    lead_id: str | None = None
    owner_agent_id: str | None = None
    expected_close_date: str | None = None
    notes: str | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class Deal(DealCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    closed_at: str | None = None


class DealActivityCreate(ApiModel):
    deal_id: str
    activity_type: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class DealActivity(DealActivityCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    company_id: str


# ── Support Models ────────────────────────────────────────────────────────────

class TicketCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    subject: str
    description: str | None = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    status: Literal["open", "in_progress", "pending", "resolved", "closed"] = "open"
    category: str | None = None
    contact_id: str | None = None
    lead_id: str | None = None
    deal_id: str | None = None
    assigned_agent_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class Ticket(TicketCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sla_response_deadline: str | None = None
    sla_resolution_deadline: str | None = None
    resolved_at: str | None = None
    closed_at: str | None = None


class TicketUpdate(ApiModel):
    status: Literal["open", "in_progress", "pending", "resolved", "closed"] | None = None
    priority: Literal["low", "medium", "high", "urgent"] | None = None
    assigned_agent_id: str | None = None
    resolution_notes: str | None = None


class MacroCreate(ApiModel):
    company_id: str
    title: str
    content: str
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class Macro(MacroCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class TicketNoteCreate(ApiModel):
    ticket_id: str
    content: str
    is_internal: bool = False


class TicketNote(TicketNoteCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    company_id: str
    created_by: str | None = None


class CustomerHealthCreate(ApiModel):
    company_id: str
    contact_id: str
    health_score: int = Field(default=100, ge=0, le=100)
    risk_level: Literal["low", "medium", "high"] = "low"
    factors: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class CustomerHealth(CustomerHealthCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    updated_at: str | None = None
