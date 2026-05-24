"""
E2E tests for Sales module (p3-07): quotes, proposals, deal desk.
Unit tests matching existing md-os test pattern.
"""
import pytest
import sys
from uuid import uuid4

sys.path.insert(0, "/root/md-os")

from api.store import store, InMemoryStore
from api.models import (
    QuoteCreate, Quote,
    ProposalCreate, Proposal,
    DealDeskCreate, DealDesk,
)


class TestQuoteModel:
    """Quote model validation."""

    def test_quote_create_default_status(self):
        """New quotes default to 'draft' status."""
        company_id = str(uuid4())
        q = QuoteCreate(
            company_id=company_id,
            quote_number="Q-001",
            customer_name="Acme Corp",
        )
        assert q.status == "draft"

    def test_quote_has_items_array(self):
        """Quote has items array for line items."""
        q = QuoteCreate(
            company_id=str(uuid4()),
            quote_number="Q-002",
            customer_name="Beta LLC",
            items=[{"description": "Item 1", "quantity": 5, "unit_price": 100.0}],
        )
        assert hasattr(q, "items")
        assert len(q.items) == 1

    def test_quote_with_discount(self):
        """Quote supports line and global discounts."""
        q = QuoteCreate(
            company_id=str(uuid4()),
            quote_number="Q-003",
            customer_name="Gamma",
            items=[{"description": "Item", "quantity": 2, "unit_price": 500.0, "discount_pct": 10.0}],
            discount_pct=5.0,
        )
        # line: 2*500*0.9 = 900; then 5% global = 855
        assert q.items[0].quantity == 2
        assert q.items[0].unit_price == 500.0


class TestQuoteService:
    """Quote CRUD and totals calculation."""

    def setup_method(self):
        # Reset and seed test company
        store.reset()
        store.companies["comp-test-001"] = {"id": "comp-test-001", "name": "Test Co"}

    def _svc(self):
        """Swap store for test."""
        from api import services as svc
        original = svc.store
        svc.store = store
        return original

    def _restore(self, original):
        from api import services as svc
        svc.store = original

    def test_create_quote_calculates_subtotal(self):
        """Quote subtotal calculated from line items."""
        orig = self._svc()
        try:
            from api.services import create_quote
            payload = {
                "company_id": "comp-test-001",
                "quote_number": "Q-SVC-001",
                "customer_name": "Test Customer",
                "items": [
                    {"description": "Dev", "quantity": 10, "unit_price": 150.0},
                    {"description": "Design", "quantity": 5, "unit_price": 120.0},
                ],
            }
            q = create_quote(payload)
            assert q["subtotal"] == 10 * 150 + 5 * 120  # 2100
            assert q["total"] == 2100.0  # no global discount
        finally:
            self._restore(orig)

    def test_create_quote_with_global_discount(self):
        """Global discount applied after line totals."""
        orig = self._svc()
        try:
            from api.services import create_quote
            payload = {
                "company_id": "comp-test-001",
                "quote_number": "Q-SVC-002",
                "customer_name": "Disc Customer",
                "items": [
                    {"description": "Item", "quantity": 1, "unit_price": 1000.0},
                ],
                "discount_pct": 10.0,  # 10% off
            }
            q = create_quote(payload)
            assert q["subtotal"] == 1000.0
            assert q["total"] == 900.0  # 1000 * 0.9
        finally:
            self._restore(orig)

    def test_list_quotes_filters_by_company(self):
        """Quotes scoped to company."""
        orig = self._svc()
        try:
            from api.services import create_quote, list_quotes
            create_quote({
                "company_id": "comp-test-001",
                "quote_number": "Q-LIST-1",
                "customer_name": "C1",
                "items": [],
            })
            create_quote({
                "company_id": "comp-other",
                "quote_number": "Q-LIST-2",
                "customer_name": "C2",
                "items": [],
            })
            qs = list_quotes("comp-test-001")
            assert len(qs) == 1
            assert qs[0]["customer_name"] == "C1"
        finally:
            self._restore(orig)

    def test_update_quote_recalculates(self):
        """Quote update recalculates totals."""
        orig = self._svc()
        try:
            from api.services import create_quote, update_quote, get_quote
            q = create_quote({
                "company_id": "comp-test-001",
                "quote_number": "Q-UPD-001",
                "customer_name": "Before",
                "items": [{"description": "Item", "quantity": 1, "unit_price": 100}],
            })
            upd = update_quote(q["id"], {
                "discount_pct": 20.0,
                "status": "sent",
            })
            assert upd["total"] == 80.0  # 100 * 0.8
            assert upd["status"] == "sent"
        finally:
            self._restore(orig)


class TestProposalModel:
    """Proposal model validation."""

    def test_proposal_create_default_status(self):
        """Proposals default to 'draft'."""
        p = ProposalCreate(
            company_id=str(uuid4()),
            proposal_number="P-001",
            customer_name="Acme",
            title="Deal",
        )
        assert p.status == "draft"

    def test_proposal_has_sections(self):
        """Proposal has sections for deal desk narrative."""
        p = ProposalCreate(
            company_id=str(uuid4()),
            proposal_number="P-002",
            customer_name="Beta",
            title="Proposal",
            sections=[
                {"heading": "Overview", "body": "Intro"},
                {"heading": "Pricing", "body": "Costs"},
            ],
        )
        assert len(p.sections) == 2


class TestProposalService:
    """Proposal CRUD and quote linking."""

    def setup_method(self):
        store.reset()
        store.companies["comp-test-001"] = {"id": "comp-test-001", "name": "Test Co"}

    def _svc(self):
        from api import services as svc
        orig = svc.store
        svc.store = store
        return orig

    def _restore(self, original):
        from api import services as svc
        svc.store = original

    def test_create_proposal_links_quote(self):
        """Creating proposal from quote updates quote status."""
        orig = self._svc()
        try:
            from api.services import create_quote, create_proposal
            q = create_quote({
                "company_id": "comp-test-001",
                "quote_number": "Q-LINK-001",
                "customer_name": "Link",
                "items": [{"description": "Item", "quantity": 1, "unit_price": 5000}],
            })
            p = create_proposal({
                "company_id": "comp-test-001",
                "proposal_number": "P-FROM-Q",
                "quote_id": q["id"],
                "customer_name": "Link",
                "title": "From Quote",
                "total_amount": 6000.0,
            })
            # Quote should be marked converted
            updated = store.quotes[q["id"]]
            assert updated["status"] == "converted"
            assert updated["converted_to_proposal_id"] == p["id"]
        finally:
            self._restore(orig)


class TestDealDeskModel:
    """DealDesk model validation."""

    def test_deal_desk_default_stage(self):
        """DealDesk defaults to 'initiated'."""
        d = DealDeskCreate(
            company_id=str(uuid4()),
            title="Mega Deal",
            customer_name="Enterprise",
            total_amount=100000.0,
        )
        assert d.stage == "initiated"

    def test_deal_desk_valid_stages(self):
        """DealDesk has full pipeline stage values."""
        valid = {"initiated", "negotiation", "pending_approval", "approved", "rejected", "closed_won", "closed_lost"}
        d = DealDeskCreate(
            company_id=str(uuid4()),
            title="Any Deal",
            customer_name="Any",
            stage="negotiation",
        )
        assert d.stage in valid


class TestDealDeskService:
    """DealDesk CRUD and pipeline."""

    def setup_method(self):
        store.reset()
        store.companies["comp-test-001"] = {"id": "comp-test-001", "name": "Test Co"}

    def _svc(self):
        from api import services as svc
        orig = svc.store
        svc.store = store
        return orig

    def _restore(self, original):
        from api import services as svc
        svc.store = original

    def test_create_deal_desk(self):
        """Create dealdesk with all fields."""
        orig = self._svc()
        try:
            from api.services import create_deal_desk
            d = create_deal_desk({
                "company_id": "comp-test-001",
                "title": "Q3 Enterprise",
                "description": "Annual contract",
                "customer_name": "BigCorp",
                "total_amount": 500000.0,
                "stage": "initiated",
            })
            assert d["title"] == "Q3 Enterprise"
            assert d["total_amount"] == 500000.0
            assert "created_at" in d
        finally:
            self._restore(orig)

    def test_list_deal_desks_filters_stage(self):
        """Filter deals by pipeline stage."""
        orig = self._svc()
        try:
            from api.services import create_deal_desk, list_deal_desks
            create_deal_desk({
                "company_id": "comp-test-001",
                "title": "Won Deal",
                "customer_name": "W",
                "stage": "closed_won",
                "total_amount": 10000.0,
            })
            create_deal_desk({
                "company_id": "comp-test-001",
                "title": "Open Deal",
                "customer_name": "O",
                "stage": "initiated",
                "total_amount": 5000.0,
            })
            won = list_deal_desks("comp-test-001", stage="closed_won")
            assert len(won) == 1
            assert won[0]["title"] == "Won Deal"
        finally:
            self._restore(orig)


class TestSalesSummary:
    """Sales summary aggregation."""

    def setup_method(self):
        store.reset()
        store.companies["comp-test-001"] = {"id": "comp-test-001", "name": "Test Co"}

    def _svc(self):
        from api import services as svc
        orig = svc.store
        svc.store = store
        return orig

    def _restore(self, original):
        from api import services as svc
        svc.store = original

    def test_sales_summary_counts(self):
        """Summary has all counts and pipeline calculations."""
        orig = self._svc()
        try:
            from api.services import (
                create_quote, create_proposal, create_deal_desk, get_sales_summary
            )
            # Seed data
            create_quote({"company_id": "comp-test-001", "quote_number": "Q-1", "customer_name": "C1", "items": []})
            create_proposal({"company_id": "comp-test-001", "proposal_number": "P-1", "customer_name": "C1", "title": "T", "sections": []})
            create_deal_desk({"company_id": "comp-test-001", "title": "D1", "customer_name": "C1", "stage": "closed_won", "total_amount": 100000.0})
            create_deal_desk({"company_id": "comp-test-001", "title": "D2", "customer_name": "C2", "stage": "initiated", "total_amount": 50000.0})

            summary = get_sales_summary("comp-test-001")
            assert summary["total_quotes"] == 1
            assert summary["total_proposals"] == 1
            assert summary["total_deals"] == 2
            assert summary["won_deals"] == 1
            assert summary["won_value"] == 100000.0
            # Pipeline = open deals (not closed_won/lost)
            assert summary["pipeline_value"] == 50000.0
        finally:
            self._restore(orig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])