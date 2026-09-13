"""Integration test for the primary manager demo path."""
import os
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:///./test_workflow.db"
if os.path.exists("test_workflow.db"):
    os.remove("test_workflow.db")

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import ReplacementAssignment

def test_manager_can_find_and_assign_replacement():
    with TestClient(app) as client:
        login = client.post("/auth/login", json={"email": "manager@talentreadiness.demo", "password": "demo123"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        dashboard = client.get("/dashboard/manager", headers=headers).json()
        absence = dashboard["absences"][0]
        find = client.post("/replacement/find", headers=headers, json={
            "absent_employee_id": absence["employee_id"], "project_id": absence["project_id"],
            "date": date.today().isoformat(), "required_hours": 8,
        })
        assert find.status_code == 200
        candidates = find.json()["candidates"]
        assert candidates and candidates[0]["overall_score"] > 0
        # The local demo database can retain assignments between manual runs.
        # Clear this test's exact fixture before asserting a fresh write.
        db = SessionLocal()
        db.query(ReplacementAssignment).filter_by(
            project_id=absence["project_id"], absent_employee_id=absence["employee_id"], date=date.today()
        ).delete()
        db.commit(); db.close()
        assign = client.post(f"/replacement/{absence['project_id']}/assign", headers=headers, json={
            "absent_employee_id": absence["employee_id"], "replacement_employee_id": candidates[0]["id"],
            "date": date.today().isoformat(),
        })
        assert assign.status_code == 200
