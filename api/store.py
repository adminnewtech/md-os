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
        self.invoices: dict[str, dict[str, Any]] = {}
        self.payments: dict[str, dict[str, Any]] = {}
        self.skus: dict[str, dict[str, Any]] = {}
        self.stock_movements: dict[str, dict[str, Any]] = {}
        self.api_credentials: dict[str, dict[str, Any]] = {}
        self.webhook_configs: dict[str, dict[str, Any]] = {}
        self.api_logs: list[dict[str, Any]] = []
        self.employees: dict[str, dict[str, Any]] = {}
        self.recruitment_pipeline: dict[str, dict[str, Any]] = {}
        self.vehicles: dict[str, dict[str, Any]] = {}
        self.shipments: dict[str, dict[str, Any]] = {}

    def reset(self) -> None:
        self.companies.clear()
        self.projects.clear()
        self.agents.clear()
        self.agent_teams.clear()
        self.workflows.clear()
        self.workflow_runs.clear()
        self.agent_runs.clear()
        self.tasks.clear()
        self.approvals.clear()
        self.audit_logs.clear()
        self.orchestrator_cycles.clear()
        self.memory_entries.clear()
        self.contacts.clear()
        self.leads.clear()
        self.deals.clear()
        self.deal_activities.clear()
        self.tickets.clear()
        self.ticket_notes.clear()
        self.macros.clear()
        self.customer_health.clear()
        self.invoices.clear()
        self.payments.clear()
        self.skus.clear()
        self.stock_movements.clear()
        self.api_credentials.clear()
        self.webhook_configs.clear()
        self.api_logs.clear()
        self.employees.clear()
        self.recruitment_pipeline.clear()
        self.vehicles.clear()
        self.shipments.clear()

    def bucket(self, name: str) -> MutableMapping[str, dict[str, Any]]:
        return getattr(self, name)


store = InMemoryStore()
