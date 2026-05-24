from __future__ import annotations

from fastapi import Header, HTTPException


ROLE_PERMISSIONS = {
    "admin": {"*"},
    "manager": {
        "companies:read",
        "projects:read",
        "projects:write",
        "agents:read",
        "agents:write",
        "workflows:read",
        "workflows:write",
        "workflow_runs:write",
        "tasks:read",
        "tasks:write",
        "approvals:read",
        "approvals:write",
        "memory:read",
        "memory:write",
        "support:read",
        "support:write",
        "crm:read",
        "crm:write",
        "finance:read",
        "finance:write",
        "inventory:read",
        "inventory:write",
        "integrations:read",
        "integrations:write",
    },
    "viewer": {
        "companies:read",
        "projects:read",
        "agents:read",
        "workflows:read",
        "tasks:read",
        "approvals:read",
        "memory:read",
    },
}

APPROVAL_CATEGORIES = {
    "destructive",
    "financial",
    "production",
    "customer-data",
    "secret",
}


def get_actor(
    x_actor_role: str = Header(default="viewer"),
    x_actor_id: str = Header(default="system"),
    x_workspace_id: str | None = Header(default=None),
) -> dict[str, str | None]:
    return {
        "role": x_actor_role,
        "actor_id": x_actor_id,
        "workspace_id": x_workspace_id,
    }


def require_permission(actor: dict[str, str | None], permission: str) -> None:
    role = actor.get("role") or "viewer"
    permissions = ROLE_PERMISSIONS.get(role, set())
    if "*" in permissions or permission in permissions:
        return
    raise HTTPException(status_code=403, detail=f"missing permission: {permission}")


def require_workspace(actor: dict[str, str | None]) -> None:
    if not actor.get("workspace_id"):
        raise HTTPException(status_code=400, detail="workspace header required")


def approval_required(category: str) -> bool:
    return category in APPROVAL_CATEGORIES
