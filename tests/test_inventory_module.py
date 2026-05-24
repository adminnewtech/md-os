"""
Test-first: Inventory module (p3-04)
SKU catalog, stock movements, low-stock summary
"""

import sys
from uuid import uuid4

sys.path.insert(0, "/root/md-os")

from fastapi.testclient import TestClient

from api.main import app
from api.store import InMemoryStore
from api.models import SKUCreate, StockMovementCreate


client = TestClient(app)


def token() -> str:
    res = client.post(
        "/api/auth/dev-token",
        json={
            "actor_id": "inventory-tester",
            "role": "admin",
            "company_id": "00000000-0000-0000-0000-000000000001",
            "workspace_id": "default",
        },
    )
    assert res.status_code == 200
    return res.json()["access_token"]


class TestInventoryModels:
    def test_sku_create_defaults(self):
        sku = SKUCreate(
            company_id=str(uuid4()),
            sku_code="SKU-001",
            name="Widget",
        )
        assert sku.quantity_on_hand == 0
        assert sku.unit == "unit"
        assert sku.status == "active"

    def test_stock_movement_create(self):
        move = StockMovementCreate(
            company_id=str(uuid4()),
            sku_id=str(uuid4()),
            movement_type="in",
            quantity=10,
        )
        assert move.movement_type == "in"
        assert move.quantity == 10


class TestInventoryService:
    def setup_method(self):
        self.store = InMemoryStore()

    def _swap_store(self):
        from api import services as svc
        original = svc.store
        svc.store = self.store
        return original

    def _restore_store(self, original):
        from api import services as svc
        svc.store = original

    def test_create_sku(self):
        from api import services as svc
        original = self._swap_store()
        try:
            sku = svc.create_sku({
                "company_id": str(uuid4()),
                "sku_code": "SKU-101",
                "name": "Printer Paper",
                "quantity_on_hand": 50,
                "reorder_point": 20,
                "reorder_quantity": 100,
            })
            assert "id" in sku
            assert sku["sku_code"] == "SKU-101"
            assert sku["quantity_on_hand"] == 50
        finally:
            self._restore_store(original)

    def test_get_sku(self):
        from api import services as svc
        original = self._swap_store()
        try:
            sku = svc.create_sku({
                "company_id": str(uuid4()),
                "sku_code": "SKU-102",
                "name": "USB Cable",
            })
            found = svc.get_sku(sku["id"])
            assert found is not None
            assert found["id"] == sku["id"]
        finally:
            self._restore_store(original)

    def test_update_sku(self):
        from api import services as svc
        original = self._swap_store()
        try:
            sku = svc.create_sku({
                "company_id": str(uuid4()),
                "sku_code": "SKU-103",
                "name": "Old Name",
            })
            updated = svc.update_sku(sku["id"], {"name": "New Name"})
            assert updated is not None
            assert updated["name"] == "New Name"
        finally:
            self._restore_store(original)

    def test_stock_movement_increases_quantity(self):
        from api import services as svc
        original = self._swap_store()
        try:
            sku = svc.create_sku({
                "company_id": str(uuid4()),
                "sku_code": "SKU-104",
                "name": "Laptop",
                "quantity_on_hand": 5,
            })
            move = svc.create_stock_movement({
                "company_id": sku["company_id"],
                "sku_id": sku["id"],
                "movement_type": "in",
                "quantity": 10,
                "reason": "new shipment",
            })
            assert move["quantity"] == 10
            updated = svc.get_sku(sku["id"])
            assert updated["quantity_on_hand"] == 15
        finally:
            self._restore_store(original)

    def test_stock_movement_decreases_quantity(self):
        from api import services as svc
        original = self._swap_store()
        try:
            sku = svc.create_sku({
                "company_id": str(uuid4()),
                "sku_code": "SKU-105",
                "name": "Mouse",
                "quantity_on_hand": 20,
            })
            svc.create_stock_movement({
                "company_id": sku["company_id"],
                "sku_id": sku["id"],
                "movement_type": "out",
                "quantity": 6,
                "reason": "sales order",
            })
            updated = svc.get_sku(sku["id"])
            assert updated["quantity_on_hand"] == 14
        finally:
            self._restore_store(original)

    def test_stock_movement_prevents_negative(self):
        from api import services as svc
        original = self._swap_store()
        try:
            sku = svc.create_sku({
                "company_id": str(uuid4()),
                "sku_code": "SKU-106",
                "name": "Monitor",
                "quantity_on_hand": 2,
            })
            try:
                svc.create_stock_movement({
                    "company_id": sku["company_id"],
                    "sku_id": sku["id"],
                    "movement_type": "out",
                    "quantity": 5,
                    "reason": "oversell",
                })
                assert False, "expected ValueError"
            except ValueError as exc:
                assert "insufficient stock" in str(exc)
        finally:
            self._restore_store(original)

    def test_inventory_summary_low_stock(self):
        from api import services as svc
        original = self._swap_store()
        try:
            company_id = str(uuid4())
            svc.create_sku({
                "company_id": company_id,
                "sku_code": "SKU-201",
                "name": "Item A",
                "quantity_on_hand": 3,
                "reorder_point": 5,
            })
            svc.create_sku({
                "company_id": company_id,
                "sku_code": "SKU-202",
                "name": "Item B",
                "quantity_on_hand": 10,
                "reorder_point": 5,
            })
            summary = svc.get_inventory_summary(company_id)
            assert summary["total_skus"] == 2
            assert summary["low_stock_count"] == 1
            assert summary["total_quantity_on_hand"] == 13
        finally:
            self._restore_store(original)

    def test_list_low_stock_only(self):
        from api import services as svc
        original = self._swap_store()
        try:
            company_id = str(uuid4())
            svc.create_sku({"company_id": company_id, "sku_code": "SKU-301", "name": "Low", "quantity_on_hand": 1, "reorder_point": 3})
            svc.create_sku({"company_id": company_id, "sku_code": "SKU-302", "name": "OK", "quantity_on_hand": 10, "reorder_point": 3})
            low = svc.list_skus(company_id=company_id, low_stock_only=True)
            assert len(low) == 1
            assert low[0]["sku_code"] == "SKU-301"
        finally:
            self._restore_store(original)


class TestInventoryAPIFlow:
    def test_inventory_lifecycle(self):
        t = token()
        headers = {"Authorization": f"Bearer {t}"}
        company_id = "00000000-0000-0000-0000-000000000001"

        create = client.post(
            "/api/inventory/skus",
            headers=headers,
            json={
                "company_id": company_id,
                "sku_code": "SKU-API-1",
                "name": "Server Rack",
                "quantity_on_hand": 10,
                "reorder_point": 4,
            },
        )
        assert create.status_code == 201
        sku = create.json()

        move_out = client.post(
            "/api/inventory/movements",
            headers=headers,
            json={
                "company_id": company_id,
                "sku_id": sku["id"],
                "movement_type": "out",
                "quantity": 7,
                "reason": "deployment",
            },
        )
        assert move_out.status_code == 201

        get_sku = client.get(f"/api/inventory/skus/{sku['id']}", headers=headers)
        assert get_sku.status_code == 200
        assert get_sku.json()["quantity_on_hand"] == 3

        summary = client.get("/api/inventory/summary", headers=headers)
        assert summary.status_code == 200
        assert summary.json()["low_stock_count"] >= 1

    def test_inventory_rejects_negative_stock_via_api(self):
        t = token()
        headers = {"Authorization": f"Bearer {t}"}
        company_id = "00000000-0000-0000-0000-000000000001"

        create = client.post(
            "/api/inventory/skus",
            headers=headers,
            json={
                "company_id": company_id,
                "sku_code": "SKU-API-NEG",
                "name": "GPU",
                "quantity_on_hand": 1,
                "reorder_point": 1,
            },
        )
        assert create.status_code == 201
        sku = create.json()

        move_out = client.post(
            "/api/inventory/movements",
            headers=headers,
            json={
                "company_id": company_id,
                "sku_id": sku["id"],
                "movement_type": "out",
                "quantity": 2,
                "reason": "invalid oversell",
            },
        )
        assert move_out.status_code == 400
        assert "insufficient stock" in move_out.json()["detail"]
