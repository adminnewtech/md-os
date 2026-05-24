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


# ── Finance Models ────────────────────────────────────────────────────────────────

InvoiceStatus = Literal["draft", "sent", "paid", "overdue", "cancelled"]


class LineItemCreate(ApiModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0


class LineItem(LineItemCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))


class InvoiceCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    invoice_number: str = ""
    customer_id: str
    customer_name: str | None = None
    total_amount: float = 0.0
    currency: str = "USD"
    status: InvoiceStatus = "draft"
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    due_date: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Invoice(InvoiceCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    paid_amount: float = 0.0
    created_at: str | None = None
    updated_at: str | None = None


class PaymentCreate(ApiModel):
    company_id: str
    invoice_id: str
    amount: float
    method: str = "bank_transfer"
    reference: str | None = None
    notes: str | None = None


class Payment(PaymentCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None


# ── Inventory Models ─────────────────────────────────────────────────────────────

class SKUCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    sku_code: str = ""
    name: str
    description: str | None = None
    category: str | None = None
    quantity_on_hand: float = 0.0
    unit: str = "unit"
    reorder_point: float = 0.0
    reorder_quantity: float = 0.0
    unit_cost: float = 0.0
    status: Literal["active", "inactive", "discontinued"] = "active"
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class SKU(SKUCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    updated_at: str | None = None


class StockMovementCreate(ApiModel):
    company_id: str
    sku_id: str
    movement_type: Literal["in", "out", "adjustment"]
    quantity: float
    reason: str | None = None
    reference: str | None = None


class StockMovement(StockMovementCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None


# ── API Connector Hub Models ──────────────────────────────────────────────────

class ApiCredentialCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    name: str
    provider: str  # telegram, github, zoho, stripe, paperclip, custom
    auth_type: Literal["api_key", "oauth2", "bearer_token", "basic"] = "api_key"
    credentials: dict[str, Any] = Field(default_factory=dict)  # store encrypted
    base_url: str | None = None
    is_active: bool = True


class ApiCredential(ApiCredentialCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None


class WebhookConfigCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    name: str
    target_url: str
    events: list[str] = Field(default_factory=list)
    secret: str | None = None
    is_active: bool = True


class WebhookConfig(WebhookConfigCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None


class ApiLogCreate(ApiModel):
    company_id: str
    connector_id: str
    direction: Literal["incoming", "outgoing"]
    method: str
    endpoint: str
    status_code: int
    duration_ms: int
    request_body: str | None = None
    response_body: str | None = None


class ApiLog(ApiLogCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str | None = None


# ── HR / Recruitment Models ───────────────────────────────────────────────────

class EmployeeCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    department: str | None = None
    role: str | None = None
    hire_date: str | None = None
    status: Literal["active", "inactive", "onboarding", "offboarded"] = "active"


class Employee(EmployeeCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None


class RecruitmentPipelineCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    candidate_name: str
    email: str
    position: str
    stage: Literal["applied", "screening", "interview", "offer", "hired", "rejected"] = "applied"
    source: str | None = None
    notes: str | None = None


class RecruitmentPipeline(RecruitmentPipelineCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None


# ── Logistics Models ─────────────────────────────────────────────────────────

class VehicleCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    name: str
    plate_number: str
    vehicle_type: str | None = None
    capacity_kg: float = 0.0
    driver_name: str | None = None
    status: Literal["available", "in_use", "maintenance", "retired"] = "available"


class Vehicle(VehicleCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None


class ShipmentCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    tracking_number: str
    vehicle_id: str | None = None
    origin: str
    destination: str
    status: Literal["pending", "in_transit", "delivered", "cancelled"] = "pending"
    estimated_delivery: str | None = None
    actual_delivery: str | None = None
    notes: str | None = None


class Shipment(ShipmentCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None


# ── Sales Models ──────────────────────────────────────────────────────────────

class QuoteLineItemCreate(ApiModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    discount_pct: float = 0.0

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price * (1 - self.discount_pct / 100)


class QuoteLineItem(QuoteLineItemCreate):
    pass


class QuoteCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    quote_number: str
    customer_name: str
    customer_email: str | None = None
    customer_phone: str | None = None
    valid_until: str | None = None
    status: Literal["draft", "sent", "accepted", "rejected", "expired", "converted"] = "draft"
    items: list[QuoteLineItemCreate] = Field(default_factory=list)
    discount_pct: float = 0.0
    notes: str | None = None
    created_by_agent_id: str | None = None
    converted_to_proposal_id: str | None = None


class Quote(QuoteCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None
    updated_at: str | None = None


class ProposalSectionCreate(ApiModel):
    heading: str
    body: str


class ProposalCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    proposal_number: str
    quote_id: str | None = None
    customer_name: str
    customer_email: str | None = None
    title: str
    status: Literal["draft", "sent", "under_review", "approved", "rejected", "signed"] = "draft"
    total_amount: float = 0.0
    sections: list[ProposalSectionCreate] = Field(default_factory=list)
    valid_until: str | None = None
    signed_by: str | None = None
    signed_at: str | None = None
    notes: str | None = None
    created_by_agent_id: str | None = None


class Proposal(ProposalCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None
    updated_at: str | None = None


class DealDeskCreate(ApiModel):
    company_id: str
    workspace_id: str = "default"
    title: str
    description: str | None = None
    quote_id: str | None = None
    proposal_id: str | None = None
    customer_name: str
    total_amount: float = 0.0
    stage: Literal["initiated", "negotiation", "pending_approval", "approved", "rejected", "closed_won", "closed_lost"] = "initiated"
    owner_agent_id: str | None = None
    notes: str | None = None


class DealDesk(DealDeskCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str | None = None
    updated_at: str | None = None
