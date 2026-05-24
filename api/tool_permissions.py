from __future__ import annotations

import re
from typing import Any

SAFE_READ_TOOLS = {
    "web_search",
    "session_search",
    "browser_navigate",
    "file_read",
}
DEFAULT_AGENT_TOOLS = {
    "web_search",
    "file_read_write",
    "session_search",
    "browser_navigate",
}
ENGINEERING_TOOLS = DEFAULT_AGENT_TOOLS | {"terminal", "git", "test_runner"}
FINANCE_TOOLS = DEFAULT_AGENT_TOOLS | {"terminal", "finance_read", "invoice_write", "budget_read"}
BUSINESS_TOOLS = DEFAULT_AGENT_TOOLS | {"crm_read", "crm_write", "support_read", "support_write"}
OPERATIONS_TOOLS = DEFAULT_AGENT_TOOLS | {"inventory_read", "inventory_write", "logistics_read", "logistics_write"}

ROLE_TOOL_PERMISSIONS: dict[str, set[str]] = {
    "chief executive officer": DEFAULT_AGENT_TOOLS | {"terminal", "approval_decide", "report_read"},
    "chief technology officer": ENGINEERING_TOOLS | {"deployment_read"},
    "backend developer": ENGINEERING_TOOLS,
    "frontend developer": ENGINEERING_TOOLS,
    "system architect": ENGINEERING_TOOLS | {"architecture_review"},
    "devops engineer": ENGINEERING_TOOLS | {"deployment_write", "infra_read"},
    "security engineer": ENGINEERING_TOOLS | {"security_scan", "audit_read"},
    "quality assurance engineer": ENGINEERING_TOOLS,
    "quality engineer": ENGINEERING_TOOLS,
    "chief financial officer": FINANCE_TOOLS | {"approval_request"},
    "finance manager": FINANCE_TOOLS,
    "crm manager": BUSINESS_TOOLS,
    "customer support manager": BUSINESS_TOOLS,
    "sales manager": BUSINESS_TOOLS | {"quote_write"},
    "marketing manager": BUSINESS_TOOLS | {"campaign_write"},
    "inventory manager": OPERATIONS_TOOLS,
    "logistics manager": OPERATIONS_TOOLS,
    "hr manager": DEFAULT_AGENT_TOOLS | {"hr_read", "hr_write"},
    "product manager": DEFAULT_AGENT_TOOLS | {"roadmap_write", "task_write"},
    "workflow automation engineer": ENGINEERING_TOOLS | {"workflow_write"},
    "integration engineer": ENGINEERING_TOOLS | {"connector_write", "webhook_read"},
    "research analyst": SAFE_READ_TOOLS | {"report_write"},
    "technical writer": DEFAULT_AGENT_TOOLS | {"docs_write"},
    "chief operating officer": DEFAULT_AGENT_TOOLS | {"operations_read", "operations_write"},
    "chief strategy officer": DEFAULT_AGENT_TOOLS | {"strategy_write", "report_read"},
}


def normalize_role(role: str | None) -> str:
    return re.sub(r"\s+", " ", (role or "").strip().lower())


def resolve_tool_permissions(agent: dict[str, Any]) -> dict[str, Any]:
    config = agent.get("config") or {}
    configured_tools = set(config.get("tools") or agent.get("tools") or [])
    role_key = normalize_role(agent.get("role"))
    role_tools = ROLE_TOOL_PERMISSIONS.get(role_key, DEFAULT_AGENT_TOOLS)
    allowed_tools = sorted(role_tools | configured_tools)
    return {
        "agent_id": agent.get("id"),
        "agent_name": agent.get("name"),
        "role": agent.get("role"),
        "resolved_role": role_key.replace(" ", "-"),
        "allowed_tools": allowed_tools,
        "tool_count": len(allowed_tools),
    }


def is_tool_allowed(agent: dict[str, Any], tool_name: str) -> dict[str, Any]:
    permissions = resolve_tool_permissions(agent)
    allowed = tool_name in permissions["allowed_tools"]
    return {
        **permissions,
        "tool_name": tool_name,
        "allowed": allowed,
    }
