from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field

import yaml
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .stack_orchestrator import (
    get_full_status,
    is_stack_healthy,
    codegraph_analyze,
    multica_agent_snapshot,
)
from .bootstrap import bootstrap_full
from .auth import AuthContext, create_access_token, get_auth_context
from .db import init_db
from .models import (
    Agent,
    AgentCreate,
    AgentRun,
    AgentRunCreate,
    AgentRunTransition,
    AgentTeam,
    AgentTeamCreate,
    Approval,
    ApprovalCreate,
    ApprovalDecision,
    AgentRunApprovalRequest,
    Company,
    CompanyCreate,
    MemoryEntryCreate,
    MemorySearchRequest,
    Project,
    ProjectCreate,
    Task,
    TaskCreate,
    Workflow,
    WorkflowCreate,
    WorkflowRunCreate,
    # CRM
    Contact,
    ContactCreate,
    Lead,
    LeadCreate,
    Deal,
    DealCreate,
    DealActivityCreate,
    # Support
    TicketCreate,
    TicketUpdate,
    MacroCreate,
    # Finance
    InvoiceCreate,
    PaymentCreate,
    # Inventory
    SKUCreate,
    StockMovementCreate,
    # Integrations
    ApiCredentialCreate,
    WebhookConfigCreate,
    ApiLogCreate,
    # HR
    EmployeeCreate,
    RecruitmentPipelineCreate,
    # Logistics
    VehicleCreate,
    ShipmentCreate,
)
from .security import approval_required, require_permission
from .services import (
    create_agent_run,
    create_approval,
    create_item,
    create_workflow_run,
    decide_approval,
    get_agent_run,
    create_memory_entry,
    get_memory_entry,
    get_item,
    list_agent_runs,
    list_memory_entries,
    list_items,
    log_audit,
    transition_agent_run,
    search_memory_entries,
    # CRM services
    create_contact,
    create_lead,
    convert_lead_to_deal,
    create_deal,
    update_deal_stage,
    create_deal_activity,
    get_crm_pipeline,
    # Support services
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket,
    close_ticket,
    add_ticket_note,
    list_ticket_notes,
    create_macro,
    get_macro,
    list_macros,
    update_macro,
    update_customer_health,
    get_customer_health,
    get_support_summary,
    # Finance services
    create_invoice,
    get_invoice,
    update_invoice,
    list_invoices,
    get_invoices_aging_summary,
    create_payment,
    list_payments_for_invoice,
    # Inventory services
    create_sku,
    get_sku,
    update_sku,
    list_skus,
    create_stock_movement,
    get_inventory_summary,
    # Integration services
    create_api_credential,
    get_api_credential,
    list_api_credentials,
    delete_api_credential,
    create_webhook_config,
    get_webhook_config,
    list_webhook_configs,
    delete_webhook_config,
    log_api_call,
    list_api_logs,
    get_connector_health,
    # HR services
    create_employee,
    get_employee,
    list_employees,
    update_employee,
    create_recruitment,
    get_recruitment,
    list_recruitments,
    update_recruitment,
    get_hr_summary,
    # Logistics services
    create_vehicle,
    get_vehicle,
    list_vehicles,
    update_vehicle_status,
    create_shipment,
    get_shipment,
    list_shipments,
    update_shipment_status,
    get_logistics_summary,
)
from .orchestrator import create_cycle, get_cycle, list_cycles, run_cycle
from .reporting import generate_agent_periodic_report, generate_ceo_daily_report
from .tool_permissions import resolve_tool_permissions, is_tool_allowed
from .store import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_info = init_db()
    bootstrap_full()
    app.state.db = db_info
    yield


app = FastAPI(title="MD-OS API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.83-171-249-32\.nip\.io",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
bootstrap_full()
T = TypeVar("T", bound=BaseModel)


class HealthResponse(BaseModel):
    status: str
    service: str


class DevTokenRequest(BaseModel):
    actor_id: str = "system"
    role: str = "admin"
    company_id: str = "00000000-0000-0000-0000-000000000001"
    workspace_id: str = "default"


class OrchestratorCycleCreateRequest(BaseModel):
    task_description: str
    company_id: str
    agent_ids: list[str]
    context: dict[str, Any] = {}
    max_parallel: int = 4


def _company_allowed(ctx: AuthContext, company_id: str | None) -> None:
    if company_id and ctx.company_id != company_id:
        raise HTTPException(status_code=403, detail="cross-company access denied")


def _workspace_allowed(ctx: AuthContext, workspace_id: str | None) -> None:
    if workspace_id and ctx.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="cross-workspace access denied")


def _create(bucket: str, entity: str, model: T, ctx: AuthContext, permission: str) -> dict[str, Any]:
    require_permission(ctx.model_dump(), permission)
    data = model.model_dump()
    _company_allowed(ctx, data.get("company_id") or ctx.company_id)
    _workspace_allowed(ctx, data.get("workspace_id"))
    item = create_item(bucket, data)
    log_audit(data.get("company_id") or ctx.company_id, ctx.actor_id, "create", entity, item["id"], None, item)
    return item


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="md-os-api")


# ═══════════════════════════════════════════════════════════════════════════════
# Stack Orchestrator Endpoints — full integration layer
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/stack/status")
def stack_status() -> dict[str, Any]:
    """Full stack health + metrics from all 6 tools."""
    return get_full_status()


@app.get("/api/stack/health")
def stack_health_simple() -> dict[str, Any]:
    """Simple health check → True/False for monitoring."""
    healthy = is_stack_healthy()
    return {"healthy": healthy, "status": "ok" if healthy else "degraded"}


@app.post("/api/stack/analyze")
def stack_analyze(
    repo_path: str = "/root/md-os",
    limit: int = 50,
    ctx: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    """Run Codegraph deep analysis → hotspots for coding targets."""
    require_permission(ctx.model_dump(), "approvals:read")
    return codegraph_analyze(repo_path=repo_path, limit=limit)


@app.get("/api/stack/multica")
def stack_multica_agents(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    """Multica agent snapshot — status, runtime, provider."""
    require_permission(ctx.model_dump(), "agents:read")
    return multica_agent_snapshot()


@app.post("/api/auth/dev-token")
def dev_token(payload: DevTokenRequest) -> dict[str, str]:
    return {
        "access_token": create_access_token(
            payload.actor_id, payload.role, payload.company_id, payload.workspace_id
        ),
        "token_type": "bearer",
    }


@app.get("/api/openapi-spec")
def openapi_spec() -> dict[str, Any]:
    with open("/root/md-os/api/openapi.yaml", "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@app.get("/api/audit-logs")
def audit_logs(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "approvals:read")
    return [row for row in store.audit_logs if row.get("company_id") in (None, ctx.company_id)]


@app.post("/api/companies", status_code=201)
def create_company(payload: CompanyCreate, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "companies:write")
    item = create_item("companies", Company(**payload.model_dump()).model_dump())
    log_audit(item["id"], ctx.actor_id, "create", "company", item["id"], None, item)
    return item


@app.get("/api/companies")
def list_companies(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "companies:read")
    return [c for c in list_items("companies") if c["id"] == ctx.company_id]


@app.get("/api/companies/{company_id}")
def get_company(company_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "companies:read")
    item = get_item("companies", company_id)
    if item is None:
        raise HTTPException(status_code=404, detail="company not found")
    _company_allowed(ctx, item["id"])
    return item


@app.put("/api/companies/{company_id}")
def update_company(
    company_id: str, payload: CompanyCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "companies:write")
    before = get_item("companies", company_id)
    if before is None:
        raise HTTPException(status_code=404, detail="company not found")
    _company_allowed(ctx, before["id"])
    after = Company(id=company_id, **payload.model_dump()).model_dump()
    store.companies[company_id] = after
    log_audit(after["id"], ctx.actor_id, "update", "company", company_id, before.copy(), after)
    return after


@app.post("/api/projects", status_code=201)
def create_project(
    payload: ProjectCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    return _create("projects", "project", Project(**payload.model_dump()), ctx, "projects:write")


@app.get("/api/projects")
def list_projects(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "projects:read")
    return [
        p for p in list_items("projects")
        if p["company_id"] == ctx.company_id and p["workspace_id"] == ctx.workspace_id
    ]


@app.get("/api/projects/{project_id}")
def get_project(project_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "projects:read")
    item = get_item("projects", project_id)
    if item is None:
        raise HTTPException(status_code=404, detail="project not found")
    _company_allowed(ctx, item.get("company_id"))
    _workspace_allowed(ctx, item.get("workspace_id"))
    return item


@app.put("/api/projects/{project_id}")
def update_project(
    project_id: str, payload: ProjectCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "projects:write")
    before = get_item("projects", project_id)
    if before is None:
        raise HTTPException(status_code=404, detail="project not found")
    _company_allowed(ctx, before.get("company_id"))
    _workspace_allowed(ctx, before.get("workspace_id"))
    after = Project(id=project_id, **payload.model_dump()).model_dump()
    store.projects[project_id] = after
    log_audit(
        after.get("company_id"), ctx.actor_id, "update", "project", project_id, before.copy(), after
    )
    return after


@app.delete("/api/projects/{project_id}")
def delete_project(
    project_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, str]:
    require_permission(ctx.model_dump(), "projects:write")
    before = get_item("projects", project_id)
    if before is None:
        raise HTTPException(status_code=404, detail="project not found")
    _company_allowed(ctx, before.get("company_id"))
    _workspace_allowed(ctx, before.get("workspace_id"))
    del store.projects[project_id]
    log_audit(
        before.get("company_id"),
        ctx.actor_id,
        "delete",
        "project",
        project_id,
        before.copy(),
        None,
    )
    return {"status": "deleted", "id": project_id}


@app.post("/api/agents", status_code=201)
def create_agent(payload: AgentCreate, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    return _create("agents", "agent", Agent(**payload.model_dump()), ctx, "agents:write")


@app.get("/api/agents")
def list_agents(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "agents:read")
    return [a for a in list_items("agents") if a.get("company_id") in (None, ctx.company_id)]


@app.get("/api/agents/{agent_id}")
def get_agent(agent_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:read")
    item = get_item("agents", agent_id)
    if item is None:
        raise HTTPException(status_code=404, detail="agent not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.put("/api/agents/{agent_id}")
def update_agent(
    agent_id: str, payload: AgentCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:write")
    before = get_item("agents", agent_id)
    if before is None:
        raise HTTPException(status_code=404, detail="agent not found")
    _company_allowed(ctx, before.get("company_id"))
    after = Agent(id=agent_id, **payload.model_dump()).model_dump()
    store.agents[agent_id] = after
    log_audit(
        after.get("company_id"), ctx.actor_id, "update", "agent", agent_id, before.copy(), after
    )
    return after


@app.delete("/api/agents/{agent_id}")
def delete_agent(agent_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, str]:
    require_permission(ctx.model_dump(), "agents:write")
    before = get_item("agents", agent_id)
    if before is None:
        raise HTTPException(status_code=404, detail="agent not found")
    _company_allowed(ctx, before.get("company_id"))
    del store.agents[agent_id]
    log_audit(
        before.get("company_id"),
        ctx.actor_id,
        "delete",
        "agent",
        agent_id,
        before.copy(),
        None,
    )
    return {"status": "deleted", "id": agent_id}


# -----------------------------------------------------------------------
# Tool Permission Resolver (p2-04)
# -----------------------------------------------------------------------


@app.get("/api/agents/{agent_id}/tool-permissions")
def get_agent_tool_permissions(
    agent_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    """Return resolved tool permissions for an agent based on role."""
    require_permission(ctx.model_dump(), "agents:read")
    agent = get_item("agents", agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    _company_allowed(ctx, agent.get("company_id"))
    return resolve_tool_permissions(agent)


@app.get("/api/agents/{agent_id}/tool-permissions/check")
def check_agent_tool_permission(
    agent_id: str,
    tool_name: str,
    ctx: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    """Check whether a specific tool is allowed for an agent."""
    require_permission(ctx.model_dump(), "agents:read")
    agent = get_item("agents", agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    _company_allowed(ctx, agent.get("company_id"))
    return is_tool_allowed(agent, tool_name)


@app.post("/api/agent-teams", status_code=201)
def create_agent_team(
    payload: AgentTeamCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    return _create(
        "agent_teams", "agent_team", AgentTeam(**payload.model_dump()), ctx, "agents:write"
    )


@app.get("/api/agent-teams")
def list_agent_teams(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "agents:read")
    return [t for t in list_items("agent_teams") if t["company_id"] == ctx.company_id]


@app.get("/api/agent-teams/{team_id}")
def get_agent_team(team_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:read")
    item = get_item("agent_teams", team_id)
    if item is None:
        raise HTTPException(status_code=404, detail="agent team not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.put("/api/agent-teams/{team_id}")
def update_agent_team(
    team_id: str, payload: AgentTeamCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:write")
    before = get_item("agent_teams", team_id)
    if before is None:
        raise HTTPException(status_code=404, detail="agent team not found")
    _company_allowed(ctx, before.get("company_id"))
    after = AgentTeam(id=team_id, **payload.model_dump()).model_dump()
    store.agent_teams[team_id] = after
    log_audit(
        after.get("company_id"),
        ctx.actor_id,
        "update",
        "agent_team",
        team_id,
        before.copy(),
        after,
    )
    return after


@app.delete("/api/agent-teams/{team_id}")
def delete_agent_team(team_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, str]:
    require_permission(ctx.model_dump(), "agents:write")
    before = get_item("agent_teams", team_id)
    if before is None:
        raise HTTPException(status_code=404, detail="agent team not found")
    _company_allowed(ctx, before.get("company_id"))
    del store.agent_teams[team_id]
    log_audit(
        before.get("company_id"),
        ctx.actor_id,
        "delete",
        "agent_team",
        team_id,
        before.copy(),
        None,
    )
    return {"status": "deleted", "id": team_id}


@app.post("/api/workflows", status_code=201)
def create_workflow(
    payload: WorkflowCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    return _create(
        "workflows", "workflow", Workflow(**payload.model_dump()), ctx, "workflows:write"
    )


@app.get("/api/workflows")
def list_workflows(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "workflows:read")
    return [w for w in list_items("workflows") if w["company_id"] == ctx.company_id]


@app.get("/api/workflows/{workflow_id}")
def get_workflow(workflow_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "workflows:read")
    item = get_item("workflows", workflow_id)
    if item is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.put("/api/workflows/{workflow_id}")
def update_workflow(
    workflow_id: str, payload: WorkflowCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "workflows:write")
    before = get_item("workflows", workflow_id)
    if before is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    _company_allowed(ctx, before.get("company_id"))
    after = Workflow(id=workflow_id, **payload.model_dump()).model_dump()
    store.workflows[workflow_id] = after
    log_audit(
        after.get("company_id"),
        ctx.actor_id,
        "update",
        "workflow",
        workflow_id,
        before.copy(),
        after,
    )
    return after


@app.delete("/api/workflows/{workflow_id}")
def delete_workflow(
    workflow_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, str]:
    require_permission(ctx.model_dump(), "workflows:write")
    before = get_item("workflows", workflow_id)
    if before is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    _company_allowed(ctx, before.get("company_id"))
    del store.workflows[workflow_id]
    log_audit(
        before.get("company_id"),
        ctx.actor_id,
        "delete",
        "workflow",
        workflow_id,
        before.copy(),
        None,
    )
    return {"status": "deleted", "id": workflow_id}


@app.get("/api/workflow-runs")
def list_workflow_runs(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "workflow_runs:write")
    return list(list_items("workflow_runs"))


@app.get("/api/workflow-runs/{run_id}")
def get_workflow_run(run_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "workflow_runs:write")
    item = get_item("workflow_runs", run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="workflow run not found")
    return item


@app.post("/api/workflows/{workflow_id}/run", status_code=202)
def run_workflow(
    workflow_id: str, payload: WorkflowRunCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "workflow_runs:write")
    workflow = get_item("workflows", workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="workflow not found")
    _company_allowed(ctx, workflow["company_id"])
    run = create_workflow_run(workflow_id, payload.input)
    run["status"] = "done"
    run["output"] = {
        "message": "workflow accepted",
        "node_count": len(workflow.get("graph", {}).get("nodes", [])),
    }
    log_audit(workflow["company_id"], ctx.actor_id, "run", "workflow", workflow_id, None, run)
    return run


@app.post("/api/tasks", status_code=201)
def create_task(payload: TaskCreate, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    return _create("tasks", "task", Task(**payload.model_dump()), ctx, "tasks:write")


@app.get("/api/tasks")
def list_tasks(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "tasks:read")
    return [t for t in list_items("tasks") if t["company_id"] == ctx.company_id]


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "tasks:read")
    item = get_item("tasks", task_id)
    if item is None:
        raise HTTPException(status_code=404, detail="task not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.put("/api/tasks/{task_id}")
def update_task(
    task_id: str, payload: TaskCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "tasks:write")
    before = get_item("tasks", task_id)
    if before is None:
        raise HTTPException(status_code=404, detail="task not found")
    _company_allowed(ctx, before.get("company_id"))
    after = Task(id=task_id, **payload.model_dump()).model_dump()
    store.tasks[task_id] = after
    log_audit(
        after.get("company_id"), ctx.actor_id, "update", "task", task_id, before.copy(), after
    )
    return after


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, str]:
    require_permission(ctx.model_dump(), "tasks:write")
    before = get_item("tasks", task_id)
    if before is None:
        raise HTTPException(status_code=404, detail="task not found")
    _company_allowed(ctx, before.get("company_id"))
    del store.tasks[task_id]
    log_audit(
        before.get("company_id"),
        ctx.actor_id,
        "delete",
        "task",
        task_id,
        before.copy(),
        None,
    )
    return {"status": "deleted", "id": task_id}


@app.post("/api/approvals", status_code=201)
def request_approval(
    payload: ApprovalCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "approvals:write")
    _company_allowed(ctx, payload.company_id)
    approval = create_approval(Approval(**payload.model_dump()).model_dump())
    log_audit(payload.company_id, ctx.actor_id, "request", "approval", approval["id"], None, approval)
    return approval


@app.get("/api/approvals")
def list_approvals(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "approvals:read")
    return [a for a in list_items("approvals") if a["company_id"] == ctx.company_id]


@app.get("/api/approvals/{approval_id}")
def get_approval(
    approval_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "approvals:read")
    item = get_item("approvals", approval_id)
    if item is None:
        raise HTTPException(status_code=404, detail="approval not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.post("/api/approvals/{approval_id}/decide")
def decide(
    approval_id: str, payload: ApprovalDecision, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "approvals:write")
    before = get_item("approvals", approval_id)
    if before is None:
        raise HTTPException(status_code=404, detail="approval not found")
    _company_allowed(ctx, before["company_id"])
    after = decide_approval(approval_id, payload.decision, payload.decided_by)
    if after is None:
        raise HTTPException(status_code=404, detail="approval not found")
    _company_allowed(ctx, after["approval"].get("company_id"))
    log_audit(
        after["approval"]["company_id"],
        ctx.actor_id,
        "decide",
        "approval",
        approval_id,
        before.copy(),
        after["approval"],
    )
    return after


# ---------------------------------------------------------------------------
# Agent Runs (Phase 2: orchestration)
# ---------------------------------------------------------------------------


@app.post("/api/agent-runs", status_code=201)
def create_agent_run_api(payload: AgentRunCreate, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:write")
    _company_allowed(ctx, payload.company_id)
    run = create_agent_run(AgentRun(**payload.model_dump()).model_dump())
    log_audit(payload.company_id, ctx.actor_id, "create", "agent_run", run["id"], None, run)
    return run


@app.get("/api/agent-runs")
def list_agent_runs_api(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "agents:read")
    return [r for r in list_agent_runs() if r.get("company_id") == ctx.company_id]


@app.get("/api/agent-runs/{run_id}")
def get_agent_run_api(run_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:read")
    item = get_agent_run(run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="agent run not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.post("/api/agent-runs/{run_id}/transition")
def transition_agent_run_api(
    run_id: str,
    payload: AgentRunTransition,
    ctx: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:write")
    run = get_agent_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="agent run not found")
    _company_allowed(ctx, run.get("company_id"))
    result = transition_agent_run(run_id, payload.to_status)
    if result is None:
        raise HTTPException(
            status_code=409,
            detail=f"invalid transition from '{run['status']}' to '{payload.to_status}'",
        )
    log_audit(run["company_id"], ctx.actor_id, "transition", "agent_run", run_id, run.copy(), result)
    return result


# --------------------------------------------------------------------------------
# Agent Approval Interrupt (Phase 2: human approval interrupt)
# --------------------------------------------------------------------------------


@app.post("/api/agent-runs/{run_id}/request-approval", status_code=201)
def request_approval_for_agent_run(
    run_id: str,
    payload: AgentRunApprovalRequest,
    ctx: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    """Pause agent run, create approval request, link them."""
    require_permission(ctx.model_dump(), "agents:write")
    run = get_agent_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="agent run not found")
    _company_allowed(ctx, run.get("company_id"))

    if run["status"] != "running":
        raise HTTPException(
            status_code=409,
            detail=f"cannot interrupt — agent run is '{run['status']}'",
        )

    approval_payload = {
        **payload.model_dump(exclude_unset=True),
        "company_id": run["company_id"],
        "requested_by_agent_id": run["agent_id"],
    }
    approval = create_approval(approval_payload)
    result = transition_agent_run(run_id, "waiting_approval", waiting_approval_id=approval["id"])

    log_audit(
        run["company_id"],
        ctx.actor_id,
        "request",
        "approval",
        approval["id"],
        None,
        approval,
    )
    log_audit(
        run["company_id"],
        ctx.actor_id,
        "transition",
        "agent_run",
        run_id,
        run.copy(),
        result,
    )
    return {"agent_run": result, "approval": approval}


@app.post("/api/orchestrator/cycles", status_code=201)
def create_orchestrator_cycle(
    payload: OrchestratorCycleCreateRequest, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:write")
    _company_allowed(ctx, payload.company_id)
    cycle = create_cycle(
        task_description=payload.task_description,
        company_id=payload.company_id,
        agent_ids=payload.agent_ids,
        context=payload.context,
        max_parallel=payload.max_parallel,
    )
    log_audit(payload.company_id, ctx.actor_id, "create", "orchestrator_cycle", cycle["id"], None, cycle)
    return cycle


@app.post("/api/orchestrator/cycles/{cycle_id}/run")
def run_orchestrator_cycle(cycle_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:write")
    cycle = get_cycle(cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="orchestrator cycle not found")
    _company_allowed(ctx, cycle.get("company_id"))
    before = cycle.copy()
    after = run_cycle(cycle_id)
    log_audit(after["company_id"], ctx.actor_id, "run", "orchestrator_cycle", cycle_id, before, after)
    return after


@app.get("/api/orchestrator/cycles")
def list_orchestrator_cycles(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "agents:read")
    return list_cycles(company_id=ctx.company_id)


@app.get("/api/orchestrator/cycles/{cycle_id}")
def get_orchestrator_cycle(cycle_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:read")
    cycle = get_cycle(cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="orchestrator cycle not found")
    _company_allowed(ctx, cycle.get("company_id"))
    return cycle


@app.get("/api/reports/agent-periodic")
def agent_periodic_report(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "agents:read")
    report = generate_agent_periodic_report(ctx.company_id)
    log_audit(ctx.company_id, ctx.actor_id, "read", "agent_periodic_report", ctx.company_id, None, report)
    return report


@app.get("/api/reports/ceo-daily", response_model=None)
def ceo_daily_report(
    period_start: str | None = None,
    period_end: str | None = None,
    ctx: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    """CEO daily synthesis report — aggregates all modules, action items, insights."""
    require_permission(ctx.model_dump(), "agents:read")
    report = generate_ceo_daily_report(
        ctx.company_id,
        period_start=period_start,
        period_end=period_end,
    )
    log_audit(ctx.company_id, ctx.actor_id, "read", "ceo_daily_report", ctx.company_id, None, report)
    return report


@app.post("/api/memory", status_code=201)
def create_memory_endpoint(
    payload: MemoryEntryCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "memory:write")
    _company_allowed(ctx, payload.company_id)
    data = payload.model_dump()
    entry = create_memory_entry(data)
    log_audit(ctx.company_id, ctx.actor_id, "create", "memory_entry", entry["id"], None, entry)
    return entry


@app.get("/api/memory")
def list_memory_endpoint(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "memory:read")
    return list_memory_entries(company_id=ctx.company_id)


@app.get("/api/memory/{memory_id}")
def get_memory_endpoint(
    memory_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "memory:read")
    entry = get_memory_entry(memory_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="memory entry not found")
    _company_allowed(ctx, entry.get("company_id"))
    return entry


@app.delete("/api/memory/{memory_id}")
def delete_memory_endpoint(
    memory_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "memory:write")
    entry = get_memory_entry(memory_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="memory entry not found")
    _company_allowed(ctx, entry.get("company_id"))
    del store.memory_entries[memory_id]
    log_audit(ctx.company_id, ctx.actor_id, "delete", "memory_entry", memory_id, entry, None)
    return {"deleted": True, "id": memory_id}


@app.post("/api/memory/search")
def search_memory_endpoint(
    payload: MemorySearchRequest, ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "memory:read")
    return search_memory_entries(
        company_id=ctx.company_id,
        embedding=payload.query_embedding,
        limit=payload.top_k,
        agent_id=payload.agent_id,
        key_prefix=payload.key_prefix,
    )


@app.middleware("http")
async def approval_guard(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        category = request.headers.get("x-action-category", "")
        if approval_required(category) and request.headers.get("x-approval-id") is None:
            return JSONResponse(
                status_code=428, content={"detail": f"approval required for {category}"}
            )
    return await call_next(request)


# ── CRM Endpoints ───────────────────────────────────────────────────────────────

@app.post("/api/crm/contacts", status_code=201)
def create_contact_api(
    payload: ContactCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:write")
    _company_allowed(ctx, payload.company_id)
    item = create_contact(Contact(**payload.model_dump()).model_dump())
    log_audit(payload.company_id, ctx.actor_id, "create", "contact", item["id"], None, item)
    return item


@app.get("/api/crm/contacts")
def list_contacts_api(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "crm:read")
    return [
        c for c in store.contacts.values()
        if c.get("company_id") == ctx.company_id
    ]


@app.get("/api/crm/contacts/{contact_id}")
def get_contact_api(
    contact_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:read")
    item = store.contacts.get(contact_id)
    if item is None:
        raise HTTPException(status_code=404, detail="contact not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.post("/api/crm/leads", status_code=201)
def create_lead_api(
    payload: LeadCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:write")
    _company_allowed(ctx, payload.company_id)
    item = create_lead(Lead(**payload.model_dump()).model_dump())
    log_audit(payload.company_id, ctx.actor_id, "create", "lead", item["id"], None, item)
    return item


@app.get("/api/crm/leads")
def list_leads_api(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "crm:read")
    return [
        l for l in store.leads.values()
        if l.get("company_id") == ctx.company_id
    ]


@app.get("/api/crm/leads/{lead_id}")
def get_lead_api(
    lead_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:read")
    item = store.leads.get(lead_id)
    if item is None:
        raise HTTPException(status_code=404, detail="lead not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.post("/api/crm/leads/{lead_id}/convert")
def convert_lead_api(
    lead_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:write")
    lead = store.leads.get(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="lead not found")
    _company_allowed(ctx, lead.get("company_id"))
    result = convert_lead_to_deal(lead_id)
    if result is None:
        raise HTTPException(status_code=400, detail="lead already converted")
    log_audit(lead["company_id"], ctx.actor_id, "convert", "lead", lead_id, lead, result["lead"])
    return result


@app.post("/api/crm/deals", status_code=201)
def create_deal_api(
    payload: DealCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:write")
    _company_allowed(ctx, payload.company_id)
    item = create_deal(Deal(**payload.model_dump()).model_dump())
    log_audit(payload.company_id, ctx.actor_id, "create", "deal", item["id"], None, item)
    return item


@app.get("/api/crm/deals")
def list_deals_api(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "crm:read")
    return [
        d for d in store.deals.values()
        if d.get("company_id") == ctx.company_id
    ]


@app.get("/api/crm/deals/{deal_id}")
def get_deal_api(
    deal_id: str, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:read")
    item = store.deals.get(deal_id)
    if item is None:
        raise HTTPException(status_code=404, detail="deal not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/crm/deals/{deal_id}/stage")
def update_deal_stage_api(
    deal_id: str,
    stage: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:write")
    deal = store.deals.get(deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="deal not found")
    _company_allowed(ctx, deal.get("company_id"))
    
    valid_stages = {"prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"}
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"invalid stage")
    
    from datetime import datetime, timezone
    closed_at = None
    if stage in ("closed_won", "closed_lost"):
        closed_at = datetime.now(timezone.utc).isoformat()
    
    before = deal.copy()
    result = update_deal_stage(deal_id, stage, closed_at)
    log_audit(deal["company_id"], ctx.actor_id, "update", "deal_stage", deal_id, before, result)
    return result


@app.post("/api/crm/deals/{deal_id}/activities")
def create_deal_activity_api(
    deal_id: str,
    payload: DealActivityCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:write")
    deal = store.deals.get(deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="deal not found")
    _company_allowed(ctx, deal.get("company_id"))
    
    data = payload.model_dump()
    data["company_id"] = deal["company_id"]
    item = create_deal_activity(data)
    return item


@app.get("/api/crm/pipeline")
def crm_pipeline_api(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "crm:read")
    return get_crm_pipeline(ctx.company_id)


# ── Support Endpoints ─────────────────────────────────────────────────────────


@app.post("/api/support/tickets", status_code=201)
def create_ticket_api(
    payload: TicketCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:write")
    _company_allowed(ctx, payload.company_id)
    item = create_ticket(payload.model_dump())
    log_audit(payload.company_id, ctx.actor_id, "create", "ticket", item["id"], None, item)
    return item


@app.get("/api/support/tickets")
def list_tickets_api(
    status: str | None = None,
    priority: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "support:read")
    return list_tickets(company_id=ctx.company_id, status=status, priority=priority)


@app.get("/api/support/tickets/{ticket_id}")
def get_ticket_api(ticket_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:read")
    item = get_ticket(ticket_id)
    if item is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/support/tickets/{ticket_id}")
def update_ticket_api(
    ticket_id: str,
    payload: TicketUpdate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:write")
    item = get_ticket(ticket_id)
    if item is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    updated = update_ticket(ticket_id, {k: v for k, v in payload.model_dump().items() if v is not None})
    log_audit(item["company_id"], ctx.actor_id, "update", "ticket", ticket_id, before, updated)
    return updated


@app.post("/api/support/tickets/{ticket_id}/close")
def close_ticket_api(
    ticket_id: str,
    resolution_notes: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:write")
    item = get_ticket(ticket_id)
    if item is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    closed = close_ticket(ticket_id, resolution_notes)
    log_audit(item["company_id"], ctx.actor_id, "close", "ticket", ticket_id, before, closed)
    return closed


@app.post("/api/support/tickets/{ticket_id}/notes")
def add_ticket_note_api(
    ticket_id: str,
    content: str,
    is_internal: bool = False,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:write")
    item = get_ticket(ticket_id)
    if item is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    _company_allowed(ctx, item.get("company_id"))
    note = add_ticket_note({
        "ticket_id": ticket_id,
        "content": content,
        "is_internal": is_internal,
        "created_by": ctx.actor_id,
    })
    log_audit(item["company_id"], ctx.actor_id, "create", "ticket_note", note["id"], None, note)
    return note


@app.get("/api/support/tickets/{ticket_id}/notes")
def list_ticket_notes_api(
    ticket_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "support:read")
    item = get_ticket(ticket_id)
    if item is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    _company_allowed(ctx, item.get("company_id"))
    return list_ticket_notes(ticket_id)


@app.post("/api/support/macros", status_code=201)
def create_macro_api(
    payload: MacroCreate, ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:write")
    _company_allowed(ctx, payload.company_id)
    item = create_macro(payload.model_dump())
    log_audit(payload.company_id, ctx.actor_id, "create", "macro", item["id"], None, item)
    return item


@app.get("/api/support/macros")
def list_macros_api(
    active_only: bool = False,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "support:read")
    return list_macros(company_id=ctx.company_id, active_only=active_only)


@app.get("/api/support/macros/{macro_id}")
def get_macro_api(macro_id: str, ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:read")
    item = get_macro(macro_id)
    if item is None:
        raise HTTPException(status_code=404, detail="macro not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/support/macros/{macro_id}")
def update_macro_api(
    macro_id: str,
    title: str | None = None,
    content: str | None = None,
    category: str | None = None,
    is_active: bool | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:write")
    item = get_macro(macro_id)
    if item is None:
        raise HTTPException(status_code=404, detail="macro not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    updated = update_macro(macro_id, {
        k: v for k, v in {"title": title, "content": content, "category": category, "is_active": is_active}.items()
        if v is not None
    })
    log_audit(item["company_id"], ctx.actor_id, "update", "macro", macro_id, before, updated)
    return updated


class CustomerHealthPayload(BaseModel):
    contact_id: str
    health_score: int = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high"] = "low"
    factors: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


@app.post("/api/support/customer-health")
def update_customer_health_api(
    payload: CustomerHealthPayload,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:write")
    item = update_customer_health({
        "company_id": ctx.company_id,
        **payload.model_dump(),
    })
    log_audit(ctx.company_id, ctx.actor_id, "upsert", "customer_health", item["id"], None, item)
    return item


@app.get("/api/support/customer-health/{contact_id}")
def get_customer_health_api(
    contact_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:read")
    item = get_customer_health(contact_id)
    if item is None:
        raise HTTPException(status_code=404, detail="customer health record not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.get("/api/support/summary")
def support_summary_api(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "support:read")
    return get_support_summary(ctx.company_id)


# ── Finance API ───────────────────────────────────────────────────────────────────

@app.post("/api/finance/invoices", status_code=201)
def create_invoice_api(
    payload: InvoiceCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "finance:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = create_invoice(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "invoice", item["id"], None, item)
    return item


@app.get("/api/finance/invoices")
def list_invoices_api(
    status: str | None = None,
    customer_id: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "finance:read")
    return list_invoices(ctx.company_id, status=status, customer_id=customer_id)


@app.get("/api/finance/invoices/{invoice_id}")
def get_invoice_api(
    invoice_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "finance:read")
    item = get_invoice(invoice_id)
    if item is None:
        raise HTTPException(status_code=404, detail="invoice not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/finance/invoices/{invoice_id}")
def update_invoice_api(
    invoice_id: str,
    status: str | None = None,
    due_date: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "finance:write")
    item = get_invoice(invoice_id)
    if item is None:
        raise HTTPException(status_code=404, detail="invoice not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    updated = update_invoice(invoice_id, {k: v for k, v in {"status": status, "due_date": due_date}.items() if v is not None})
    log_audit(item["company_id"], ctx.actor_id, "update", "invoice", invoice_id, before, updated)
    return updated


@app.post("/api/finance/payments", status_code=201)
def create_payment_api(
    payload: PaymentCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "finance:write")
    invoice = get_invoice(payload.invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="invoice not found")
    _company_allowed(ctx, invoice.get("company_id"))
    item = create_payment(payload.model_dump())
    log_audit(invoice["company_id"], ctx.actor_id, "create", "payment", item["id"], None, item)
    return item


@app.get("/api/finance/invoices/{invoice_id}/payments")
def list_invoice_payments_api(
    invoice_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "finance:read")
    invoice = get_invoice(invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="invoice not found")
    _company_allowed(ctx, invoice.get("company_id"))
    return list_payments_for_invoice(invoice_id)


@app.get("/api/finance/summary/aging")
def get_aging_summary_api(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "finance:read")
    return get_invoices_aging_summary(ctx.company_id)


# ── Inventory API ─────────────────────────────────────────────────────────────────

@app.post("/api/inventory/skus", status_code=201)
def create_sku_api(
    payload: SKUCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "inventory:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = create_sku(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "sku", item["id"], None, item)
    return item


@app.get("/api/inventory/skus")
def list_skus_api(
    category: str | None = None,
    status: str | None = None,
    low_stock_only: bool = False,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "inventory:read")
    return list_skus(ctx.company_id, category=category, status=status, low_stock_only=low_stock_only)


@app.get("/api/inventory/skus/{sku_id}")
def get_sku_api(
    sku_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "inventory:read")
    item = get_sku(sku_id)
    if item is None:
        raise HTTPException(status_code=404, detail="sku not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/inventory/skus/{sku_id}")
def update_sku_api(
    sku_id: str,
    name: str | None = None,
    reorder_point: int | None = None,
    status: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "inventory:write")
    item = get_sku(sku_id)
    if item is None:
        raise HTTPException(status_code=404, detail="sku not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    updated = update_sku(sku_id, {
        k: v for k, v in {"name": name, "reorder_point": reorder_point, "status": status}.items()
        if v is not None
    })
    log_audit(item["company_id"], ctx.actor_id, "update", "sku", sku_id, before, updated)
    return updated


@app.post("/api/inventory/movements", status_code=201)
def create_stock_movement_api(
    payload: StockMovementCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "inventory:write")
    sku = get_sku(payload.sku_id)
    if sku is None:
        raise HTTPException(status_code=404, detail="sku not found")
    _company_allowed(ctx, sku.get("company_id"))
    try:
        item = create_stock_movement(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_audit(sku["company_id"], ctx.actor_id, "create", "stock_movement", item["id"], None, item)
    return item


@app.get("/api/inventory/summary")
def inventory_summary_api(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "inventory:read")
    return get_inventory_summary(ctx.company_id)


# ── API Connector Hub Routes ────────────────────────────────────────────────────────

@app.post("/api/integrations/credentials", status_code=201)
def create_credential_api(
    payload: ApiCredentialCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "integrations:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = create_api_credential(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "api_credential", item["id"], None, item)
    return item


@app.get("/api/integrations/credentials")
def list_credentials_api(
    provider: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "integrations:read")
    return list_api_credentials(ctx.company_id, provider=provider)


@app.get("/api/integrations/credentials/{cred_id}")
def get_credential_api(
    cred_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "integrations:read")
    item = get_api_credential(cred_id)
    if item is None:
        raise HTTPException(status_code=404, detail="credential not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.delete("/api/integrations/credentials/{cred_id}")
def delete_credential_api(
    cred_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, str]:
    require_permission(ctx.model_dump(), "integrations:write")
    item = get_api_credential(cred_id)
    if item is None:
        raise HTTPException(status_code=404, detail="credential not found")
    _company_allowed(ctx, item.get("company_id"))
    delete_api_credential(cred_id)
    log_audit(item["company_id"], ctx.actor_id, "delete", "api_credential", cred_id, item, None)
    return {"status": "deleted"}


@app.post("/api/integrations/webhooks", status_code=201)
def create_webhook_api(
    payload: WebhookConfigCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "integrations:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = create_webhook_config(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "webhook_config", item["id"], None, item)
    return item


@app.get("/api/integrations/webhooks")
def list_webhooks_api(ctx: AuthContext = Depends(get_auth_context)) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "integrations:read")
    return list_webhook_configs(ctx.company_id)


@app.get("/api/integrations/webhooks/{webhook_id}")
def get_webhook_api(
    webhook_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "integrations:read")
    item = get_webhook_config(webhook_id)
    if item is None:
        raise HTTPException(status_code=404, detail="webhook not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.delete("/api/integrations/webhooks/{webhook_id}")
def delete_webhook_api(
    webhook_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, str]:
    require_permission(ctx.model_dump(), "integrations:write")
    item = get_webhook_config(webhook_id)
    if item is None:
        raise HTTPException(status_code=404, detail="webhook not found")
    _company_allowed(ctx, item.get("company_id"))
    delete_webhook_config(webhook_id)
    log_audit(item["company_id"], ctx.actor_id, "delete", "webhook_config", webhook_id, item, None)
    return {"status": "deleted"}


@app.post("/api/integrations/logs", status_code=201)
def create_integration_log_api(
    payload: ApiLogCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "integrations:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = log_api_call(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "api_log", item["id"], None, item)
    return item


@app.get("/api/integrations/logs")
def list_integration_logs_api(
    connector_id: str | None = None,
    limit: int = 100,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "integrations:read")
    return list_api_logs(ctx.company_id, connector_id=connector_id, limit=limit)


@app.get("/api/integrations/health")
def connector_health_api(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "integrations:read")
    return get_connector_health(ctx.company_id)

# ── HR Routes ────────────────────────────────────────────────────────────────────────

@app.post("/api/hr/employees", status_code=201)
def create_employee_api(
    payload: EmployeeCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "hr:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = create_employee(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "employee", item["id"], None, item)
    return item


@app.get("/api/hr/employees")
def list_employees_api(
    status: str | None = None,
    department: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "hr:read")
    return list_employees(ctx.company_id, status=status, department=department)


@app.get("/api/hr/employees/{emp_id}")
def get_employee_api(
    emp_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "hr:read")
    item = get_employee(emp_id)
    if item is None:
        raise HTTPException(status_code=404, detail="employee not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/hr/employees/{emp_id}")
def update_employee_api(
    emp_id: str,
    status: str | None = None,
    department: str | None = None,
    role: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "hr:write")
    item = get_employee(emp_id)
    if item is None:
        raise HTTPException(status_code=404, detail="employee not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    updated = update_employee(emp_id, {k: v for k, v in {"status": status, "department": department, "role": role}.items() if v is not None})
    log_audit(item["company_id"], ctx.actor_id, "update", "employee", emp_id, before, updated)
    return updated


@app.get("/api/hr/summary")
def hr_summary_api(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "hr:read")
    return get_hr_summary(ctx.company_id)


# ── Recruitment Routes ─────────────────────────────────────────────────────

@app.post("/api/hr/recruitment", status_code=201)
def create_recruitment_api(
    payload: RecruitmentPipelineCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "hr:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = create_recruitment(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "recruitment", item["id"], None, item)
    return item


@app.get("/api/hr/recruitment")
def list_recruitment_api(
    stage: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "hr:read")
    return list_recruitments(ctx.company_id, stage=stage)


@app.get("/api/hr/recruitment/{rec_id}")
def get_recruitment_api(
    rec_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "hr:read")
    item = get_recruitment(rec_id)
    if item is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/hr/recruitment/{rec_id}/stage")
def promote_recruitment_api(
    rec_id: str,
    stage: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "hr:write")
    item = get_recruitment(rec_id)
    if item is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    updated = update_recruitment(rec_id, stage)
    log_audit(item["company_id"], ctx.actor_id, "update", "recruitment", rec_id, before, updated)
    return updated


# ── Logistics Routes ───────────────────────────────────────────────────────

@app.post("/api/logistics/vehicles", status_code=201)
def create_vehicle_api(
    payload: VehicleCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "logistics:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = create_vehicle(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "vehicle", item["id"], None, item)
    return item


@app.get("/api/logistics/vehicles")
def list_vehicles_api(
    status: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "logistics:read")
    return list_vehicles(ctx.company_id, status=status)


@app.get("/api/logistics/vehicles/{veh_id}")
def get_vehicle_api(
    veh_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "logistics:read")
    item = get_vehicle(veh_id)
    if item is None:
        raise HTTPException(status_code=404, detail="vehicle not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/logistics/vehicles/{veh_id}/status")
def update_vehicle_status_api(
    veh_id: str,
    status: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "logistics:write")
    item = get_vehicle(veh_id)
    if item is None:
        raise HTTPException(status_code=404, detail="vehicle not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    updated = update_vehicle_status(veh_id, status)
    log_audit(item["company_id"], ctx.actor_id, "update", "vehicle", veh_id, before, updated)
    return updated


@app.post("/api/logistics/shipments", status_code=201)
def create_shipment_api(
    payload: ShipmentCreate,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "logistics:write")
    data = payload.model_dump()
    _company_allowed(ctx, data.get("company_id"))
    item = create_shipment(data)
    log_audit(item["company_id"], ctx.actor_id, "create", "shipment", item["id"], None, item)
    return item


@app.get("/api/logistics/shipments")
def list_shipments_api(
    status: str | None = None,
    vehicle_id: str | None = None,
    ctx: AuthContext = Depends(get_auth_context)
) -> list[dict[str, Any]]:
    require_permission(ctx.model_dump(), "logistics:read")
    return list_shipments(ctx.company_id, status=status, vehicle_id=vehicle_id)


@app.get("/api/logistics/shipments/{ship_id}")
def get_shipment_api(
    ship_id: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "logistics:read")
    item = get_shipment(ship_id)
    if item is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    _company_allowed(ctx, item.get("company_id"))
    return item


@app.patch("/api/logistics/shipments/{ship_id}/status")
def update_shipment_status_api(
    ship_id: str,
    status: str,
    ctx: AuthContext = Depends(get_auth_context)
) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "logistics:write")
    item = get_shipment(ship_id)
    if item is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    _company_allowed(ctx, item.get("company_id"))
    before = item.copy()
    from datetime import datetime, timezone
    delivered = datetime.now(timezone.utc).isoformat() if status == "delivered" else None
    updated = update_shipment_status(ship_id, status, delivered_at=delivered)
    log_audit(item["company_id"], ctx.actor_id, "update", "shipment", ship_id, before, updated)
    return updated


@app.get("/api/logistics/summary")
def logistics_summary_api(ctx: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    require_permission(ctx.model_dump(), "logistics:read")
    return get_logistics_summary(ctx.company_id)
