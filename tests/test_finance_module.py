"""
Test-first: Finance module (p3-03)
Invoices, line items, payments, aging summary
"""

import pytest
import sys
from uuid import uuid4

sys.path.insert(0, "/root/md-os")

from api.store import store, InMemoryStore
from api.models import (
    InvoiceCreate, Invoice,
    LineItemCreate, LineItem,
    PaymentCreate, Payment,
)


class TestInvoiceModel:
    """Invoice model validation."""

    def test_invoice_create_default_status(self):
        """New invoices default to 'draft' status."""
        company_id = str(uuid4())
        inv = InvoiceCreate(
            company_id=company_id,
            invoice_number="INV-001",
            customer_id=str(uuid4()),
            total_amount=1000.0,
        )
        assert inv.status == "draft"

    def test_invoice_number_required(self):
        """Invoice must have an invoice_number."""
        company_id = str(uuid4())
        inv = InvoiceCreate(
            company_id=company_id,
            customer_id=str(uuid4()),
            total_amount=500.0,
        )
        assert inv.invoice_number is not None

    def test_invoice_currency_defaults_usd(self):
        """Currency defaults to USD."""
        inv = InvoiceCreate(
            company_id=str(uuid4()),
            invoice_number="INV-002",
            customer_id=str(uuid4()),
            total_amount=250.0,
        )
        assert inv.currency == "USD"

    def test_invoice_has_line_items_field(self):
        """Invoice has line_items array."""
        inv = InvoiceCreate(
            company_id=str(uuid4()),
            invoice_number="INV-003",
            customer_id=str(uuid4()),
            total_amount=300.0,
            line_items=[],
        )
        assert hasattr(inv, "line_items")


class TestInvoiceService:
    """Invoice CRUD and state transitions."""

    def setup_method(self):
        self.store = InMemoryStore()

    def _svc(self):
        from api import services as svc
        original = svc.store
        svc.store = self.store
        return original

    def _restore(self, original):
        from api import services as svc
        svc.store = original

    def test_create_invoice(self):
        from api import services as svc
        original = self._svc()
        try:
            inv = svc.create_invoice({
                "company_id": str(uuid4()),
                "invoice_number": "INV-100",
                "customer_id": str(uuid4()),
                "total_amount": 1500.0,
                "status": "draft",
            })
            assert "id" in inv
            assert inv["invoice_number"] == "INV-100"
            assert inv["total_amount"] == 1500.0
            assert inv["status"] == "draft"
        finally:
            self._restore(original)

    def test_create_invoice_with_line_items(self):
        from api import services as svc
        original = self._svc()
        try:
            line_items = [
                {"description": "Consulting hours", "quantity": 10, "unit_price": 100.0, "total": 1000.0},
                {"description": "Setup fee", "quantity": 1, "unit_price": 500.0, "total": 500.0},
            ]
            inv = svc.create_invoice({
                "company_id": str(uuid4()),
                "invoice_number": "INV-101",
                "customer_id": str(uuid4()),
                "total_amount": 1500.0,
                "line_items": line_items,
            })
            assert len(inv["line_items"]) == 2
            assert inv["line_items"][0]["description"] == "Consulting hours"
        finally:
            self._restore(original)

    def test_get_invoice(self):
        from api import services as svc
        original = self._svc()
        try:
            inv = svc.create_invoice({
                "company_id": str(uuid4()),
                "invoice_number": "INV-102",
                "customer_id": str(uuid4()),
                "total_amount": 750.0,
            })
            found = svc.get_invoice(inv["id"])
            assert found is not None
            assert found["id"] == inv["id"]
        finally:
            self._restore(original)

    def test_get_invoice_not_found(self):
        from api import services as svc
        original = self._svc()
        try:
            result = svc.get_invoice("nonexistent-invoice-id")
            assert result is None
        finally:
            self._restore(original)

    def test_update_invoice_status_to_sent(self):
        from api import services as svc
        original = self._svc()
        try:
            inv = svc.create_invoice({
                "company_id": str(uuid4()),
                "invoice_number": "INV-103",
                "customer_id": str(uuid4()),
                "total_amount": 2000.0,
                "status": "draft",
            })
            updated = svc.update_invoice(inv["id"], {"status": "sent"})
            assert updated is not None
            assert updated["status"] == "sent"
        finally:
            self._restore(original)

    def test_update_invoice_status_to_paid(self):
        from api import services as svc
        original = self._svc()
        try:
            inv = svc.create_invoice({
                "company_id": str(uuid4()),
                "invoice_number": "INV-104",
                "customer_id": str(uuid4()),
                "total_amount": 3000.0,
                "status": "sent",
            })
            updated = svc.update_invoice(inv["id"], {"status": "paid"})
            assert updated is not None
            assert updated["status"] == "paid"
        finally:
            self._restore(original)

    def test_list_invoices_by_company(self):
        from api import services as svc
        original = self._svc()
        try:
            company_a = str(uuid4())
            company_b = str(uuid4())
            svc.create_invoice({"company_id": company_a, "invoice_number": "INV-A1", "customer_id": str(uuid4()), "total_amount": 100.0})
            svc.create_invoice({"company_id": company_a, "invoice_number": "INV-A2", "customer_id": str(uuid4()), "total_amount": 200.0})
            svc.create_invoice({"company_id": company_b, "invoice_number": "INV-B1", "customer_id": str(uuid4()), "total_amount": 300.0})

            invoices = svc.list_invoices(company_id=company_a)
            assert len(invoices) == 2
            assert all(inv["company_id"] == company_a for inv in invoices)
        finally:
            self._restore(original)

    def test_list_invoices_by_status(self):
        from api import services as svc
        original = self._svc()
        try:
            company_id = str(uuid4())
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-S1", "customer_id": str(uuid4()), "total_amount": 100.0, "status": "draft"})
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-S2", "customer_id": str(uuid4()), "total_amount": 200.0, "status": "sent"})
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-S3", "customer_id": str(uuid4()), "total_amount": 300.0, "status": "paid"})

            draft = svc.list_invoices(company_id=company_id, status="draft")
            assert len(draft) == 1
            assert draft[0]["status"] == "draft"

            paid = svc.list_invoices(company_id=company_id, status="paid")
            assert len(paid) == 1
            assert paid[0]["status"] == "paid"
        finally:
            self._restore(original)

    def test_list_invoices_by_customer(self):
        from api import services as svc
        original = self._svc()
        try:
            company_id = str(uuid4())
            customer_a = str(uuid4())
            customer_b = str(uuid4())
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-CA1", "customer_id": customer_a, "total_amount": 100.0})
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-CA2", "customer_id": customer_a, "total_amount": 200.0})
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-CB1", "customer_id": customer_b, "total_amount": 300.0})

            cust_a_invoices = svc.list_invoices(company_id=company_id, customer_id=customer_a)
            assert len(cust_a_invoices) == 2
        finally:
            self._restore(original)

    def test_invoice_aging_summary(self):
        from api import services as svc
        original = self._svc()
        try:
            company_id = str(uuid4())
            # Current invoices
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-AGE1", "customer_id": str(uuid4()), "total_amount": 100.0, "status": "sent"})
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-AGE2", "customer_id": str(uuid4()), "total_amount": 200.0, "status": "sent"})
            # Paid invoice (should not appear in aging)
            svc.create_invoice({"company_id": company_id, "invoice_number": "INV-AGE3", "customer_id": str(uuid4()), "total_amount": 500.0, "status": "paid"})

            aging = svc.get_invoices_aging_summary(company_id)
            assert "total_outstanding" in aging
            assert aging["total_outstanding"] == 300.0  # only sent, not paid
        finally:
            self._restore(original)

    def test_invoice_cross_company_denied(self):
        """Invoices from company A are not visible to company B."""
        from api import services as svc
        original = self._svc()
        try:
            company_a = str(uuid4())
            company_b = str(uuid4())
            inv_a = svc.create_invoice({
                "company_id": company_a,
                "invoice_number": "INV-CROSS",
                "customer_id": str(uuid4()),
                "total_amount": 999.0,
            })
            inv_b_list = svc.list_invoices(company_id=company_b)
            assert all(i["id"] != inv_a["id"] for i in inv_b_list)
        finally:
            self._restore(original)


class TestPaymentService:
    """Payment recording against invoices."""

    def setup_method(self):
        self.store = InMemoryStore()

    def test_create_payment(self):
        from api import services as svc
        original = svc.store
        svc.store = self.store
        try:
            inv = svc.create_invoice({
                "company_id": str(uuid4()),
                "invoice_number": "INV-PAY1",
                "customer_id": str(uuid4()),
                "total_amount": 1000.0,
                "status": "sent",
            })
            payment = svc.create_payment({
                "invoice_id": inv["id"],
                "company_id": inv["company_id"],
                "amount": 500.0,
                "method": "bank_transfer",
            })
            assert "id" in payment
            assert payment["amount"] == 500.0
            assert payment["invoice_id"] == inv["id"]
        finally:
            svc.store = original

    def test_payment_updates_invoice_status_to_paid_when_full(self):
        from api import services as svc
        original = svc.store
        svc.store = self.store
        try:
            inv = svc.create_invoice({
                "company_id": str(uuid4()),
                "invoice_number": "INV-PAY2",
                "customer_id": str(uuid4()),
                "total_amount": 500.0,
                "status": "sent",
            })
            svc.create_payment({
                "invoice_id": inv["id"],
                "company_id": inv["company_id"],
                "amount": 500.0,
                "method": "credit_card",
            })
            updated = svc.get_invoice(inv["id"])
            assert updated["status"] == "paid"
        finally:
            svc.store = original

    def test_list_payments_by_invoice(self):
        from api import services as svc
        original = svc.store
        svc.store = self.store
        try:
            inv = svc.create_invoice({
                "company_id": str(uuid4()),
                "invoice_number": "INV-PAY3",
                "customer_id": str(uuid4()),
                "total_amount": 1000.0,
                "status": "sent",
            })
            svc.create_payment({"invoice_id": inv["id"], "company_id": inv["company_id"], "amount": 300.0, "method": "bank_transfer"})
            svc.create_payment({"invoice_id": inv["id"], "company_id": inv["company_id"], "amount": 200.0, "method": "paypal"})

            payments = svc.list_payments_for_invoice(inv["id"])
            assert len(payments) == 2
            assert sum(p["amount"] for p in payments) == 500.0
        finally:
            svc.store = original