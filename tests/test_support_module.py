"""
Test-first: Support module (p3-02)
Tickets, SLA, macros, customer health, escalation
"""

import pytest
import sys
from uuid import uuid4

sys.path.insert(0, "/root/md-os")

from api.store import store, InMemoryStore
from api.models import (
    TicketCreate, Ticket,
    TicketUpdate,
    MacroCreate, Macro,
    TicketNoteCreate, TicketNote,
    CustomerHealthCreate, CustomerHealth,
)
from api import services as support_services


class TestTicketModel:
    """Ticket model validation."""

    def test_ticket_create_default_status(self):
        """New tickets default to 'open' status."""
        company_id = str(uuid4())
        t = TicketCreate(company_id=company_id, subject="Login broken")
        assert t.status == "open"

    def test_ticket_priority_defaults(self):
        """Priority defaults to medium."""
        company_id = str(uuid4())
        t = TicketCreate(company_id=company_id, subject="Bug report")
        assert t.priority == "medium"

    def test_ticket_sla_deadlines(self):
        """Tickets have sla_response_deadline and sla_resolution_deadline fields."""
        t = Ticket(
            company_id=str(uuid4()),
            subject="Test",
            sla_response_deadline="2026-05-25T10:00:00Z",
            sla_resolution_deadline="2026-05-26T17:00:00Z",
        )
        assert t.sla_response_deadline is not None
        assert t.sla_resolution_deadline is not None


class TestTicketService:
    """Ticket CRUD and state transitions."""

    def setup_method(self):
        # Fresh store per test
        self.store = InMemoryStore()

    def test_create_ticket(self):
        """create_ticket returns a ticket dict with id."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "Cannot export PDF",
                "priority": "high",
                "status": "open",
            })
            assert "id" in t
            assert t["subject"] == "Cannot export PDF"
            assert t["priority"] == "high"
            assert t["status"] == "open"
        finally:
            svc.store = original_store

    def test_create_ticket_minimal(self):
        """create_ticket with only required fields."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "Question about billing",
            })
            assert "id" in t
            assert t["status"] == "open"
            assert t["priority"] == "medium"
        finally:
            svc.store = original_store

    def test_get_ticket(self):
        """get_ticket retrieves by id."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "Test ticket",
            })
            found = svc.get_ticket(t["id"])
            assert found is not None
            assert found["id"] == t["id"]
        finally:
            svc.store = original_store

    def test_get_ticket_not_found(self):
        """get_ticket returns None for unknown id."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            result = svc.get_ticket("nonexistent-id")
            assert result is None
        finally:
            svc.store = original_store

    def test_update_ticket_status(self):
        """update_ticket can change status."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "Bug",
            })
            updated = svc.update_ticket(t["id"], {"status": "in_progress"})
            assert updated is not None
            assert updated["status"] == "in_progress"
        finally:
            svc.store = original_store

    def test_update_ticket_assignee(self):
        """update_ticket can assign to agent."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "Support request",
            })
            agent_id = str(uuid4())
            updated = svc.update_ticket(t["id"], {"assigned_agent_id": agent_id})
            assert updated is not None
            assert updated["assigned_agent_id"] == agent_id
        finally:
            svc.store = original_store

    def test_update_ticket_priority(self):
        """update_ticket can escalate priority."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "Urgent issue",
                "priority": "low",
            })
            updated = svc.update_ticket(t["id"], {"priority": "urgent"})
            assert updated is not None
            assert updated["priority"] == "urgent"
        finally:
            svc.store = original_store

    def test_close_ticket(self):
        """close_ticket marks ticket as closed with resolved_at."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "Feature request",
            })
            closed = svc.close_ticket(t["id"], resolution_notes="Implemented in v2.1")
            assert closed is not None
            assert closed["status"] == "closed"
            assert closed.get("resolved_at") is not None
        finally:
            svc.store = original_store

    def test_list_tickets_by_company(self):
        """list_tickets returns only tickets for a company."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            company_a = str(uuid4())
            company_b = str(uuid4())

            t_a = svc.create_ticket({"company_id": company_a, "subject": "Ticket A"})
            svc.create_ticket({"company_id": company_a, "subject": "Ticket B"})
            svc.create_ticket({"company_id": company_b, "subject": "Ticket C"})

            tickets = svc.list_tickets(company_id=company_a)
            assert len(tickets) == 2
            assert all(t["company_id"] == company_a for t in tickets)
        finally:
            svc.store = original_store

    def test_list_tickets_by_status(self):
        """list_tickets can filter by status."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            company_id = str(uuid4())
            svc.create_ticket({"company_id": company_id, "subject": "Open 1", "status": "open"})
            svc.create_ticket({"company_id": company_id, "subject": "Open 2", "status": "open"})
            svc.create_ticket({"company_id": company_id, "subject": "In Progress", "status": "in_progress"})
            svc.create_ticket({"company_id": company_id, "subject": "Closed", "status": "closed"})

            open_tickets = svc.list_tickets(company_id=company_id, status="open")
            assert len(open_tickets) == 2
        finally:
            svc.store = original_store

    def test_list_tickets_by_priority(self):
        """list_tickets can filter by priority."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            company_id = str(uuid4())
            svc.create_ticket({"company_id": company_id, "subject": "Low 1", "priority": "low"})
            svc.create_ticket({"company_id": company_id, "subject": "Low 2", "priority": "low"})
            svc.create_ticket({"company_id": company_id, "subject": "High 1", "priority": "high"})

            low_tickets = svc.list_tickets(company_id=company_id, priority="low")
            assert len(low_tickets) == 2
        finally:
            svc.store = original_store


class TestTicketNoteService:
    """Ticket notes (internal and public)."""

    def setup_method(self):
        self.store = InMemoryStore()

    def test_add_ticket_note(self):
        """add_ticket_note creates a note on a ticket."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "API issue",
            })
            note = svc.add_ticket_note({
                "ticket_id": t["id"],
                "content": "Investigating the 500 error logs.",
                "is_internal": True,
                "created_by": "agent-42",
            })
            assert "id" in note
            assert note["content"] == "Investigating the 500 error logs."
            assert note["is_internal"] is True
            assert note["ticket_id"] == t["id"]
        finally:
            svc.store = original_store

    def test_add_ticket_note_public(self):
        """add_ticket_note can be public (not internal)."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({
                "company_id": str(uuid4()),
                "subject": "Billing question",
            })
            note = svc.add_ticket_note({
                "ticket_id": t["id"],
                "content": "Your invoice has been sent to your email.",
                "is_internal": False,
            })
            assert note["is_internal"] is False
        finally:
            svc.store = original_store

    def test_list_ticket_notes(self):
        """list_ticket_notes returns notes for a ticket."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            t = svc.create_ticket({"company_id": str(uuid4()), "subject": "Bug"})
            svc.add_ticket_note({"ticket_id": t["id"], "content": "Note 1", "is_internal": False})
            svc.add_ticket_note({"ticket_id": t["id"], "content": "Note 2", "is_internal": True})
            svc.add_ticket_note({"ticket_id": t["id"], "content": "Note 3", "is_internal": False})

            notes = svc.list_ticket_notes(t["id"])
            assert len(notes) == 3
        finally:
            svc.store = original_store


class TestMacroService:
    """Macros: reusable response templates."""

    def setup_method(self):
        self.store = InMemoryStore()

    def test_create_macro(self):
        """create_macro stores a response template."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            m = svc.create_macro({
                "company_id": str(uuid4()),
                "title": "Password Reset",
                "content": "Please reset your password via the portal at https://...",
                "category": "auth",
                "is_active": True,
            })
            assert "id" in m
            assert m["title"] == "Password Reset"
            assert m["is_active"] is True
        finally:
            svc.store = original_store

    def test_get_macro(self):
        """get_macro retrieves by id."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            m = svc.create_macro({
                "company_id": str(uuid4()),
                "title": "Billing inquiry",
                "content": "Thank you for contacting billing...",
            })
            found = svc.get_macro(m["id"])
            assert found is not None
            assert found["id"] == m["id"]
        finally:
            svc.store = original_store

    def test_list_macros_by_company(self):
        """list_macros returns company-scoped macros."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            c1 = str(uuid4())
            c2 = str(uuid4())
            svc.create_macro({"company_id": c1, "title": "Macro 1", "content": "..."})
            svc.create_macro({"company_id": c1, "title": "Macro 2", "content": "..."})
            svc.create_macro({"company_id": c2, "title": "Macro 3", "content": "..."})

            macros = svc.list_macros(company_id=c1)
            assert len(macros) == 2
            assert all(m["company_id"] == c1 for m in macros)
        finally:
            svc.store = original_store

    def test_update_macro(self):
        """update_macro modifies content/title/category."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            m = svc.create_macro({
                "company_id": str(uuid4()),
                "title": "Old title",
                "content": "Old content",
                "is_active": True,
            })
            updated = svc.update_macro(m["id"], {
                "title": "New title",
                "content": "New content",
                "is_active": False,
            })
            assert updated is not None
            assert updated["title"] == "New title"
            assert updated["content"] == "New content"
            assert updated["is_active"] is False
        finally:
            svc.store = original_store


class TestCustomerHealthService:
    """Customer health tracking."""

    def setup_method(self):
        self.store = InMemoryStore()

    def test_update_customer_health(self):
        """update_customer_health creates or updates health record."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            company_id = str(uuid4())
            contact_id = str(uuid4())

            # First update
            h = svc.update_customer_health({
                "company_id": company_id,
                "contact_id": contact_id,
                "health_score": 85,
                "risk_level": "low",
                "notes": "Active customer, no issues.",
            })
            assert "id" in h
            assert h["health_score"] == 85
            assert h["risk_level"] == "low"

            # Second update (upsert)
            h2 = svc.update_customer_health({
                "company_id": company_id,
                "contact_id": contact_id,
                "health_score": 60,
                "risk_level": "medium",
                "notes": "SLA breach last month.",
            })
            # Should update same record
            assert h2["id"] == h["id"]
            assert h2["health_score"] == 60
        finally:
            svc.store = original_store

    def test_get_customer_health(self):
        """get_customer_health retrieves for contact."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            company_id = str(uuid4())
            contact_id = str(uuid4())

            svc.update_customer_health({
                "company_id": company_id,
                "contact_id": contact_id,
                "health_score": 40,
                "risk_level": "high",
            })
            h = svc.get_customer_health(contact_id)
            assert h is not None
            assert h["health_score"] == 40
        finally:
            svc.store = original_store


class TestSupportAPIFlow:
    """End-to-end: create ticket → add notes → escalate → close."""

    def setup_method(self):
        self.store = InMemoryStore()

    def test_ticket_lifecycle(self):
        """Full ticket lifecycle: create → note → escalate → resolve."""
        from api import services as svc
        original_store = svc.store
        svc.store = self.store
        try:
            company_id = str(uuid4())
            agent_id = str(uuid4())

            # 1. Create ticket
            t = svc.create_ticket({
                "company_id": company_id,
                "subject": "Cannot login to dashboard",
                "description": "User reports 403 on every page.",
                "priority": "high",
                "contact_id": str(uuid4()),
            })
            assert t["status"] == "open"
            assert t["priority"] == "high"

            # 2. Escalate to urgent
            t2 = svc.update_ticket(t["id"], {"priority": "urgent", "assigned_agent_id": agent_id})
            assert t2["priority"] == "urgent"
            assert t2["assigned_agent_id"] == agent_id

            # 3. Add internal note
            note = svc.add_ticket_note({
                "ticket_id": t["id"],
                "content": "Reproduced on staging. Root cause: expired JWT.",
                "is_internal": True,
            })
            assert note["is_internal"] is True

            # 4. Close ticket
            closed = svc.close_ticket(t["id"], resolution_notes="Fixed JWT expiry handling.")
            assert closed["status"] == "closed"
            assert closed.get("resolved_at") is not None

            # 5. Verify ticket history
            notes = svc.list_ticket_notes(t["id"])
            assert len(notes) == 1
            tickets = svc.list_tickets(company_id=company_id, status="closed")
            assert len(tickets) == 1
            assert tickets[0]["id"] == t["id"]
        finally:
            svc.store = original_store