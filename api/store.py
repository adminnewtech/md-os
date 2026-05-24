from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any


class InMemoryStore:
    def __init__(self) -> None:
        self.companies: dict[str, dict[str, Any]] = {}
        self.projects: dict[str, dict[str, Any]] = {}
        self.agents: dict[str, dict[str, Any]] = {}
        self.agent_teams: dict[str, dict[str, Any]] = {}
        self.workflows: dict[str, dict[str, Any]] = {}
        self.workflow_runs: dict[str, dict[str, Any]] = {}
        self.agent_runs: dict[str, dict[str, Any]] = {}
        self.tasks: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, dict[str, Any]] = {}
        self.audit_logs: list[dict[str, Any]] = []
        self.orchestrator_cycles: dict[str, dict[str, Any]] = {}
        self.memory_entries: dict[str, dict[str, Any]] = {}
        self.contacts: dict[str, dict[str, Any]] = {}
        self.leads: dict[str, dict[str, Any]] = {}
        self.deals: dict[str, dict[str, Any]] = {}
        self.deal_activities: dict[str, dict[str, Any]] = {}
        self.tickets: dict[str, dict[str, Any]] = {}
        self.ticket_notes: dict[str, dict[str, Any]] = {}
        self.macros: dict[str, dict[str, Any]] = {}
        self.customer_health: dict[str, dict[str, Any]] = {}

    def bucket(self, name: str) -> MutableMapping[str, dict[str, Any]]:
        return getattr(self, name)


store = InMemoryStore()
