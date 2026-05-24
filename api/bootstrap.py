from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from models import Agent, Company, Workflow
    from store import store
except ImportError:
    from .models import Agent, Company, Workflow
    from .store import store

DEFAULT_COMPANY_ID = "00000000-0000-0000-0000-000000000001"
ROOT = Path("/root/md-os")


def seed_default_company() -> dict[str, Any]:
    company = Company(
        id=DEFAULT_COMPANY_ID,
        name="MD Platform (NewTech Kuwait)",
        industry="ai-company-operating-system",
        status="active",
        settings={"country": "KW", "currency": "KWD", "locale": "ar-KW"},
    ).model_dump()
    store.companies.setdefault(DEFAULT_COMPANY_ID, company)
    return store.companies[DEFAULT_COMPANY_ID]


def _load_json_files(directory: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        payload["_source_file"] = str(path)
        rows.append(payload)
    return rows


def _stable_import_id(prefix: str, source_file: str) -> str:
    stem = Path(source_file).stem
    return f"{prefix}:{stem}"


def seed_agents(company_id: str = DEFAULT_COMPANY_ID) -> int:
    count = 0
    for definition in _load_json_files(ROOT / "agents"):
        source_file = definition.pop("_source_file")
        agent_id = _stable_import_id("agent", source_file)
        config = dict(definition)
        config["source_file"] = source_file
        agent = Agent(
            id=agent_id,
            company_id=company_id,
            name=definition["name"],
            role=definition["role"],
            mission=definition["mission"],
            config=config,
            status="active",
        ).model_dump()
        if agent_id not in store.agents:
            count += 1
        store.agents[agent_id] = agent
    return count


def seed_workflows(company_id: str = DEFAULT_COMPANY_ID) -> int:
    count = 0
    for definition in _load_json_files(ROOT / "workflows"):
        source_file = definition.pop("_source_file")
        workflow_id = definition.get("id") or _stable_import_id("workflow", source_file)
        graph = {"nodes": definition.get("nodes", []), "source_file": source_file}
        workflow = Workflow(
            id=workflow_id,
            company_id=company_id,
            name=definition["name"],
            trigger=definition["trigger"],
            graph=graph,
            status="active",
        ).model_dump()
        if workflow_id not in store.workflows:
            count += 1
        store.workflows[workflow_id] = workflow
    return count


def bootstrap_seed_data() -> dict[str, int]:
    seed_default_company()
    agents = seed_agents()
    workflows = seed_workflows()
    return {"companies": len(store.companies), "agents_imported": agents, "workflows_imported": workflows}

# ── CRM Seed ──────────────────────────────────────────────────────────────────

def seed_crm(company_id: str = DEFAULT_COMPANY_ID) -> dict[str, int]:
    """Seed contacts, leads and deals for demo."""
    from .models import Contact, Lead, Deal

    contacts_data = [
        {"first_name": "أحمد", "last_name": "الحربي", "email": "a.alharbi@newtech-kw.com", "phone": "+96522223344", "title": "CTO", "company_name": "NewTech Kuwait", "source": "referral", "tags": ["vip", "kuwait"]},
        {"first_name": "فاطمة", "last_name": "المطيري", "email": "fatima@majid-group.com", "phone": "+96598887766", "title": "VP Operations", "company_name": "Majid Group", "source": "website", "tags": ["enterprise", "lead"]},
        {"first_name": "عبدالله", "last_name": "العتيبي", "email": "abdullah@alshanah.com", "phone": "+96565544332", "title": "CEO", "company_name": "Al Shanah Holdings", "source": "conference", "tags": ["decision-maker"]},
        {"first_name": "نورة", "last_name": "السيد", "email": "noura@zain.net", "phone": "+96591112233", "title": "IT Director", "company_name": "Zain Kuwait", "source": "linkedin", "tags": ["telecom", "enterprise"]},
        {"first_name": "محمد", "last_name": "الزبن", "email": "m.alzabin@alshamsi.com", "phone": "+96570001122", "title": "Procurement Head", "company_name": "Al Shamsi Co.", "source": "referral", "tags": ["procurement"]},
        {"first_name": "سارة", "last_name": "القحطاني", "email": "sara@gulfmart.com", "phone": "+96533344555", "title": "Digital Manager", "company_name": "Gulf Mart", "source": "email_campaign", "tags": ["retail"]},
        {"first_name": "خالد", "last_name": "الشمري", "email": "khaled@benaia.com", "phone": "+96544455667", "title": "CEO", "company_name": "Benaia Industries", "source": "referral", "tags": ["manufacturing"]},
        {"first_name": "ريم", "last_name": "الرشيد", "email": "reem@rashedlaw.com", "phone": "+96522221133", "title": "Partner", "company_name": "Al Rashid Law Firm", "source": "website", "tags": ["legal"]},
    ]

    leads_data = [
        {"contact_id": None, "title": "MD Platform Enterprise License", "status": "qualified", "source": "website", "score": 85, "notes": "High intent, budget approved"},
        {"contact_id": None, "title": "AI Agent Integration Project", "status": "contacted", "source": "linkedin", "score": 70, "notes": "Follow-up next week"},
        {"contact_id": None, "title": "CRM Module Subscription", "status": "new", "source": "email_campaign", "score": 50, "notes": "Inbound inquiry"},
        {"contact_id": None, "title": "Logistics Automation Suite", "status": "qualified", "source": "referral", "score": 90, "notes": "Urgent requirement"},
        {"contact_id": None, "title": "Support Desk Enterprise", "status": "contacted", "source": "conference", "score": 60, "notes": "Evaluating competitors"},
    ]

    deals_data = [
        {"title": "MD Platform Enterprise - Annual", "value": 45000, "currency": "KWD", "stage": "proposal", "probability": 60, "expected_close_date": "2026-06-15"},
        {"title": "AI Agent Swarm License", "value": 22000, "currency": "KWD", "stage": "negotiation", "probability": 75, "expected_close_date": "2026-05-30"},
        {"title": "Finance Module - SMB Pack", "value": 8500, "currency": "KWD", "stage": "closed_won", "probability": 100, "expected_close_date": "2026-04-20"},
        {"title": "HR Automation Project", "value": 31000, "currency": "KWD", "stage": "qualification", "probability": 40, "expected_close_date": "2026-07-10"},
        {"title": "Logistics Tracking System", "value": 18000, "currency": "KWD", "stage": "prospecting", "probability": 20, "expected_close_date": "2026-08-01"},
    ]

    from .store import store
    count_contacts = 0
    for idx, c in enumerate(contacts_data, start=1):
        from .models import Contact as CModel
        item = CModel(id=f"demo:contact:{idx}", company_id=company_id, **c).model_dump()
        if item["id"] not in store.contacts:
            store.contacts[item["id"]] = item
            count_contacts += 1
        # link first lead to this contact
        if leads_data and c["email"] == "a.alharbi@newtech-kw.com":
            leads_data[0]["contact_id"] = item["id"]

    count_leads = 0
    for idx, l in enumerate(leads_data, start=1):
        from .models import Lead as LModel
        item = LModel(id=f"demo:lead:{idx}", company_id=company_id, **l).model_dump()
        if item["id"] not in store.leads:
            store.leads[item["id"]] = item
            count_leads += 1

    count_deals = 0
    for idx, d in enumerate(deals_data, start=1):
        from .models import Deal as DModel
        item = DModel(id=f"demo:deal:{idx}", company_id=company_id, **d).model_dump()
        if item["id"] not in store.deals:
            store.deals[item["id"]] = item
            count_deals += 1

    return {"contacts": count_contacts, "leads": count_leads, "deals": count_deals}


# ── Support Seed ───────────────────────────────────────────────────────────────

def seed_support(company_id: str = DEFAULT_COMPANY_ID) -> dict[str, int]:
    """Seed tickets and macros."""
    from .models import Ticket, Macro, TicketNote

    tickets_data = [
        {"subject": "خطأ في توليد التقارير اليومية", "description": "التقرير يظهر تاريخ اليوم السابق بدل الحالي", "priority": "high", "status": "in_progress", "category": "bug", "tags": ["reports", "urgent"]},
        {"subject": "طلب إضافة حقل مخصص في CRM", "description": "نحتاج حقل رقم التسجيل التجاري", "priority": "medium", "status": "open", "category": "feature", "tags": ["crm", "custom-field"]},
        {"subject": "مشكلة تسجيل الدخول SSO", "description": "用户在Kuwait SSO登录失败", "priority": "urgent", "status": "open", "category": "bug", "tags": ["auth", "sso"]},
        {"subject": "استفسار عن طريقة ربط API مع HubSpot", "description": "هل تدعمون تكامل HubSpot مباشر؟", "priority": "low", "status": "pending", "category": "question", "tags": ["integration", "hubspot"]},
        {"subject": "طلب تدريب الفريق على نظام HR", "description": "نحتاج جلسة تدريب للفريق الجديد", "priority": "medium", "status": "resolved", "category": "training", "tags": ["hr", "training"]},
        {"subject": "خطأ في تصدير بيانات الموظفين", "description": "التصدير يرجع ملف فارغ", "priority": "high", "status": "in_progress", "category": "bug", "tags": ["hr", "export"]},
        {"subject": "ترقية خطة النظام", "description": "نريد الترقية من SMB إلى Enterprise", "priority": "medium", "status": "open", "category": "sales", "tags": ["upgrade", "billing"]},
        {"subject": "طلب إضافة مستخدم جديد", "description": "إضافة 5 موظفين جدد للنظام", "priority": "low", "status": "closed", "category": "onboarding", "tags": ["users"]},
    ]

    macros_data = [
        {"title": "رد تلقائي - تذاكر جديدة", "content": "شكراً لتواصلك معنا! 🎫\nتم استلام تذكرتك وستتم مراجعتها خلال 24 ساعة.\nرقم التذكرة: {{ticket_id}}", "category": "auto-reply", "tags": ["auto"]},
        {"title": "حل مشكلة إعادة تعيين كلمة المرور", "content": "لإعادة تعيين كلمة المرور: 1. اذهب إلى صفحة تسجيل الدخول 2. اضغط نسيت كلمة المرور 3. أدخل بريدك الإلكتروني 4. تحقق من بريدك الوارد", "category": "howto", "tags": ["auth", "password"]},
        {"title": "إغلاق التذكرة - تم الحل", "content": "تم حل مشكلتك بنجاح ✅\nإذا احتجت مساعدة إضافية، لا تتردد في التواصل.\nنقدر تقييمك لخدمة الدعم!", "category": "resolution", "tags": ["close"]},
    ]

    from .store import store
    count_tickets = 0
    for idx, t in enumerate(tickets_data, start=1):
        from .models import Ticket as TModel
        item = TModel(id=f"demo:ticket:{idx}", company_id=company_id, **t).model_dump()
        if item["id"] not in store.tickets:
            store.tickets[item["id"]] = item
            count_tickets += 1

    count_macros = 0
    for idx, m in enumerate(macros_data, start=1):
        from .models import Macro as MModel
        item = MModel(id=f"demo:macro:{idx}", company_id=company_id, **m).model_dump()
        if item["id"] not in store.macros:
            store.macros[item["id"]] = item
            count_macros += 1

    return {"tickets": count_tickets, "macros": count_macros}


# ── Finance Seed ───────────────────────────────────────────────────────────────

def seed_finance(company_id: str = DEFAULT_COMPANY_ID) -> dict[str, int]:
    """Seed invoices and payments."""
    from .models import Invoice, Payment
    from datetime import datetime, timedelta, timezone

    tz = timezone.utc
    now = datetime.now(tz)
    invoices_data = [
        {"invoice_number": "INV-2026-001", "customer_id": "cust-001", "customer_name": "Majid Group", "total_amount": 45000, "currency": "KWD", "status": "paid", "line_items": [{"description": "MD Platform Enterprise Annual License", "quantity": 1, "unit_price": 45000, "total": 45000}], "due_date": "2026-03-15"},
        {"invoice_number": "INV-2026-002", "customer_id": "cust-002", "customer_name": "Al Shanah Holdings", "total_amount": 22000, "currency": "KWD", "status": "paid", "line_items": [{"description": "AI Agent Swarm License", "quantity": 1, "unit_price": 22000, "total": 22000}], "due_date": "2026-04-01"},
        {"invoice_number": "INV-2026-003", "customer_id": "cust-003", "customer_name": "Gulf Mart", "total_amount": 8500, "currency": "KWD", "status": "sent", "line_items": [{"description": "Finance Module SMB Pack", "quantity": 1, "unit_price": 8500, "total": 8500}], "due_date": "2026-05-15"},
        {"invoice_number": "INV-2026-004", "customer_id": "cust-004", "customer_name": "Zain Kuwait", "total_amount": 31000, "currency": "KWD", "status": "sent", "line_items": [{"description": "HR Automation Project - Phase 1", "quantity": 1, "unit_price": 31000, "total": 31000}], "due_date": "2026-06-01"},
        {"invoice_number": "INV-2026-005", "customer_id": "cust-005", "customer_name": "Benaia Industries", "total_amount": 18000, "currency": "KWD", "status": "overdue", "line_items": [{"description": "Logistics Tracking System Setup", "quantity": 1, "unit_price": 18000, "total": 18000}], "due_date": "2026-04-15"},
        {"invoice_number": "INV-2026-006", "customer_id": "cust-001", "customer_name": "Majid Group", "total_amount": 12500, "currency": "KWD", "status": "draft", "line_items": [{"description": "Support Desk Enterprise - Monthly", "quantity": 1, "unit_price": 12500, "total": 12500}], "due_date": "2026-06-30"},
    ]

    from .store import store
    count_invoices = 0
    for idx, inv in enumerate(invoices_data, start=1):
        from .models import Invoice as IModel
        item = IModel(id=f"demo:invoice:{idx}", company_id=company_id, **inv).model_dump()
        if item["id"] not in store.invoices:
            store.invoices[item["id"]] = item
            count_invoices += 1

    # seed a payment for first invoice
    first_inv_id = list(store.invoices.values())[0]["id"]
    if first_inv_id:
        from .models import Payment as PModel
        payment = PModel(id="demo:payment:1", company_id=company_id, invoice_id=first_inv_id, amount=45000, method="bank_transfer", reference="TRF-2026-001").model_dump()
        if payment["id"] not in store.payments:
            store.payments[payment["id"]] = payment

    return {"invoices": count_invoices}


# ── HR Seed ───────────────────────────────────────────────────────────────────

def seed_hr(company_id: str = DEFAULT_COMPANY_ID) -> dict[str, int]:
    """Seed employees and recruitment pipeline."""
    from .models import Employee, RecruitmentPipeline

    employees_data = [
        {"first_name": "عبدالله", "last_name": "الحربي", "email": "abdullah@md-platform.com", "phone": "+96522220011", "department": "Engineering", "role": "Senior Backend Engineer", "hire_date": "2024-01-15", "status": "active"},
        {"first_name": "نورة", "last_name": "الشمري", "email": "noura@md-platform.com", "phone": "+96593334455", "department": "Engineering", "role": "Frontend Engineer", "hire_date": "2024-03-01", "status": "active"},
        {"first_name": "محمد", "last_name": "العتيبي", "email": "mohammed@md-platform.com", "phone": "+96574445566", "department": "Product", "role": "Product Manager", "hire_date": "2023-08-20", "status": "active"},
        {"first_name": "سارة", "last_name": "المطيري", "email": "sara@md-platform.com", "phone": "+96565556677", "department": "Operations", "role": "Operations Manager", "hire_date": "2023-05-10", "status": "active"},
        {"first_name": "خالد", "last_name": "الزبن", "email": "khaled@md-platform.com", "phone": "+96556667788", "department": "Sales", "role": "Sales Director", "hire_date": "2024-02-01", "status": "active"},
        {"first_name": "ريم", "last_name": "القحطاني", "email": "reem@md-platform.com", "phone": "+96547778899", "department": "Finance", "role": "Financial Analyst", "hire_date": "2024-06-15", "status": "active"},
        {"first_name": "أحمد", "last_name": "السيد", "email": "ahmed@md-platform.com", "phone": "+96538889900", "department": "Engineering", "role": "DevOps Engineer", "hire_date": "2024-09-01", "status": "onboarding"},
        {"first_name": "فاطمة", "last_name": "الرشيد", "email": "fatima@md-platform.com", "phone": "+96529990011", "department": "HR", "role": "HR Manager", "hire_date": "2023-11-01", "status": "active"},
    ]

    pipeline_data = [
        {"candidate_name": "يوسف الأحمد", "email": "youssef@outlook.com", "position": "Senior Frontend Engineer", "stage": "interview", "source": "linkedin"},
        {"candidate_name": "لمى السالم", "email": "lama@gmail.com", "position": "Product Designer", "stage": "screening", "source": "referral"},
        {"candidate_name": "تركي العتيبي", "email": "turki.e@gmail.com", "position": "AI Engineer", "stage": "offer", "source": "indeed"},
        {"candidate_name": "هند الموسى", "email": "hind.m@gmail.com", "position": "Marketing Manager", "stage": "applied", "source": "website"},
    ]

    from .store import store
    count_employees = 0
    for idx, e in enumerate(employees_data, start=1):
        from .models import Employee as EModel
        item = EModel(id=f"demo:employee:{idx}", company_id=company_id, **e).model_dump()
        if item["id"] not in store.employees:
            store.employees[item["id"]] = item
            count_employees += 1

    count_pipeline = 0
    for idx, p in enumerate(pipeline_data, start=1):
        from .models import RecruitmentPipeline as PModel
        item = PModel(id=f"demo:recruitment:{idx}", company_id=company_id, **p).model_dump()
        if item["id"] not in store.recruitment_pipeline:
            store.recruitment_pipeline[item["id"]] = item
            count_pipeline += 1

    return {"employees": count_employees, "pipeline": count_pipeline}


# ── Inventory Seed ─────────────────────────────────────────────────────────────

def seed_inventory(company_id: str = DEFAULT_COMPANY_ID) -> dict[str, int]:
    """Seed SKUs and stock movements."""
    from .models import SKU, StockMovement

    skus_data = [
        {"sku_code": "MD-ENT-001", "name": "MD Platform Enterprise License", "description": "Annual enterprise license - unlimited users", "category": "software", "quantity_on_hand": 999, "unit": "license", "reorder_point": 10, "unit_cost": 12000},
        {"sku_code": "MD-SMB-002", "name": "MD Platform SMB License", "description": "Small business license - up to 25 users", "category": "software", "quantity_on_hand": 999, "unit": "license", "reorder_point": 10, "unit_cost": 3500},
        {"sku_code": "MD-SUP-003", "name": "Premium Support Package", "description": "24/7 priority support with dedicated account manager", "category": "support", "quantity_on_hand": 999, "unit": "package", "reorder_point": 5, "unit_cost": 2500},
        {"sku_code": "MD-TRA-004", "name": "Implementation Training", "description": "2-day on-site training session for up to 10 users", "category": "training", "quantity_on_hand": 50, "unit": "session", "reorder_point": 5, "unit_cost": 1500},
        {"sku_code": "HW-SRV-001", "name": "AI Compute Node - Standard", "description": "GPU compute node for agent workloads", "category": "hardware", "quantity_on_hand": 12, "unit": "node", "reorder_point": 3, "unit_cost": 8500},
        {"sku_code": "HW-SRV-002", "name": "AI Compute Node - High-Memory", "description": "High-memory GPU node for large models", "category": "hardware", "quantity_on_hand": 4, "unit": "node", "reorder_point": 2, "unit_cost": 15000},
    ]

    from .store import store
    count_skus = 0
    for idx, s in enumerate(skus_data, start=1):
        from .models import SKU as SModel
        item = SModel(id=f"demo:sku:{idx}", company_id=company_id, **s).model_dump()
        if item["id"] not in store.skus:
            store.skus[item["id"]] = item
            count_skus += 1

    return {"skus": count_skus}


# ── Logistics Seed ────────────────────────────────────────────────────────────

def seed_logistics(company_id: str = DEFAULT_COMPANY_ID) -> dict[str, int]:
    """Seed vehicles and shipments."""
    from .models import Vehicle, Shipment

    vehicles_data = [
        {"name": "شاحنة التوصيل الرئيسية", "plate_number": "KWA 1234", "vehicle_type": "delivery_van", "capacity_kg": 500, "driver_name": "بدر الشمري", "status": "available"},
        {"name": "ونسة التوصيل السريع", "plate_number": "KWA 5678", "vehicle_type": "cargo_van", "capacity_kg": 200, "driver_name": "فهد الحربي", "status": "in_use"},
        {"name": "شاحنة البضائع الثقيلة", "plate_number": "KWA 9012", "vehicle_type": "truck", "capacity_kg": 5000, "driver_name": "سلطان المطيري", "status": "available"},
    ]

    shipments_data = [
        {"tracking_number": "SHP-2026-0001", "origin": "مقر NewTech - حولي", "destination": "Majid Group - مدينة الكويت", "status": "in_transit", "estimated_delivery": "2026-05-25"},
        {"tracking_number": "SHP-2026-0002", "origin": "مقر NewTech - حولي", "destination": "Al Shanah Holdings - شرق", "status": "delivered", "estimated_delivery": "2026-05-20"},
        {"tracking_number": "SHP-2026-0003", "origin": "مقر NewTech - حولي", "destination": "Zain Kuwait - المرقاب", "status": "pending", "estimated_delivery": "2026-05-28"},
        {"tracking_number": "SHP-2026-0004", "origin": "مقر NewTech - حولي", "destination": "Benaia Industries - الصناعية", "status": "in_transit", "estimated_delivery": "2026-05-26"},
    ]

    from .store import store
    count_vehicles = 0
    for idx, v in enumerate(vehicles_data, start=1):
        from .models import Vehicle as VModel
        item = VModel(id=f"demo:vehicle:{idx}", company_id=company_id, **v).model_dump()
        if item["id"] not in store.vehicles:
            store.vehicles[item["id"]] = item
            count_vehicles += 1

    count_shipments = 0
    for idx, s in enumerate(shipments_data, start=1):
        from .models import Shipment as SModel
        item = SModel(id=f"demo:shipment:{idx}", company_id=company_id, **s).model_dump()
        if item["id"] not in store.shipments:
            store.shipments[item["id"]] = item
            count_shipments += 1

    return {"vehicles": count_vehicles, "shipments": count_shipments}


# ── Projects Seed ─────────────────────────────────────────────────────────────

def seed_projects(company_id: str = DEFAULT_COMPANY_ID) -> dict[str, int]:
    """Seed active projects."""
    from .models import Project, Task
    from .store import store

    projects_data = [
        {"name": "MD Platform Enterprise Rollout", "status": "active", "metadata": {"progress": 72, "budget_kd": 45000, "client": "Majid Group"}},
        {"name": "AI Agent Swarm Integration", "status": "active", "metadata": {"progress": 58, "budget_kd": 22000, "client": "Al Shanah Holdings"}},
        {"name": "Finance Automation Module", "status": "active", "metadata": {"progress": 90, "budget_kd": 8500, "client": "Gulf Mart"}},
        {"name": "HR Recruitment Portal", "status": "planning", "metadata": {"progress": 35, "budget_kd": 31000, "client": "Zain Kuwait"}},
        {"name": "Logistics Tracking Dashboard", "status": "active", "metadata": {"progress": 44, "budget_kd": 18000, "client": "Benaia Industries"}},
    ]
    tasks_data = [
        {"title": "Finalize RTL dashboard", "description": "Polish Arabic UX and charts", "status": "done", "priority": "high"},
        {"title": "Connect live API modules", "description": "Wire CRM, finance, HR, support", "status": "done", "priority": "high"},
        {"title": "Customer onboarding checklist", "description": "Prepare go-live handoff", "status": "in_progress", "priority": "medium"},
        {"title": "Security hardening pass", "description": "Headers, rate limits, auth review", "status": "todo", "priority": "high"},
        {"title": "Monthly KPI export", "description": "PDF/CSV report", "status": "todo", "priority": "medium"},
    ]

    count_projects = 0
    for idx, prj in enumerate(projects_data, start=1):
        item = Project(id=f"demo:project:{idx}", company_id=company_id, workspace_id="default", **prj).model_dump()
        if item["id"] not in store.projects:
            store.projects[item["id"]] = item
            count_projects += 1

    count_tasks = 0
    for idx, task in enumerate(tasks_data, start=1):
        project_id = f"demo:project:{((idx - 1) % len(projects_data)) + 1}"
        item = Task(id=f"demo:task:{idx}", company_id=company_id, project_id=project_id, **task).model_dump()
        if item["id"] not in store.tasks:
            store.tasks[item["id"]] = item
            count_tasks += 1

    return {"projects": count_projects, "tasks": count_tasks}


# ── Full Bootstrap ───────────────────────────────────────────────────────────

def bootstrap_full() -> dict[str, Any]:
    """Seed ALL data across all modules."""
    result = bootstrap_seed_data()
    result["crm"] = seed_crm()
    result["support"] = seed_support()
    result["projects"] = seed_projects()
    result["finance"] = seed_finance()
    result["hr"] = seed_hr()
    result["inventory"] = seed_inventory()
    result["logistics"] = seed_logistics()
    return result
