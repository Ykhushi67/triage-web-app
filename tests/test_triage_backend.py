import os
import sys

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from backend.seed import seed_database
from ml.inference import inference_engine

client = TestClient(app)


def setup_test_environment():
    """Initializes database and seeds demo data."""
    init_db()
    seed_database()


def test_root_health():
    """Test health endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "DPDP" in data["regulatory_alignment"]
    assert "3-Tier" in data["triage_system"]


def test_auth_login():
    """Test login for Doctor and Nurse roles."""
    # Doctor login
    doc_res = client.post("/api/auth/login", json={"email": "doctor@hospital.org", "password": "doctor123"})
    assert doc_res.status_code == 200
    assert "access_token" in doc_res.json()
    assert doc_res.json()["user"]["role"] == "DOCTOR"

    # Nurse login
    nurse_res = client.post("/api/auth/login", json={"email": "nurse@hospital.org", "password": "nurse123"})
    assert nurse_res.status_code == 200
    assert nurse_res.json()["user"]["role"] == "TRIAGE_NURSE"


def test_ml_inference_cardiac_emergency():
    """Scenario: High risk chest pain patient receives Level 1 Critical."""
    result = inference_engine.predict({
        "age": 62.0,
        "gender": "male",
        "symptoms": "Severe crushing retrosternal chest pain radiating to left arm",
        "notes": "Diaphoretic, pale, distress",
        "temperature": 37.1,
        "heart_rate": 122.0,
        "blood_pressure": "155/95",
        "spo2": 93.0,
    })
    assert result["available"] is True
    assert result["triage_level"] == 1
    assert result["priority_score"] >= 7.0
    assert result["confidence"] > 0.70
    assert any("cardiac" in f.lower() or "chest" in f.lower() for f in result["key_factors"])


def test_ml_inference_missing_vitals_uncertainty():
    """Scenario: Patient with omitted vitals receives uncertainty penalty and clinician review flag."""
    result = inference_engine.predict({
        "age": 35.0,
        "symptoms": "Generalized weakness and malaise",
        "temperature": None,
        "heart_rate": None,
        "blood_pressure": None,
        "spo2": None,
    })
    assert result["available"] is True
    assert result["requires_clinician_review"] is True
    assert result["missing_vitals_count"] >= 3
    assert len(result["uncertainty_flags"]) > 0


def test_ml_safety_rule_hypoxemia_floor():
    """Scenario: SpO2 < 90% triggers hard safety floor to Level 1 and Emergency routing."""
    result = inference_engine.predict({
        "age": 28.0,
        "symptoms": "Mild cough",
        "temperature": 37.0,
        "heart_rate": 80.0,
        "blood_pressure": "120/80",
        "spo2": 86.0,  # Critical hypoxemia
    })
    assert result["available"] is True
    assert result["triage_level"] == 1
    assert result["priority_score"] >= 8.5
    assert result["recommended_department"] == "Emergency"
    assert any("Hypoxemia" in f for f in result["safety_flags"])


def test_independent_patient_history_lookup():
    """Scenario: Returning patient P0011 has history, without biasing ML inference."""
    # Login as doctor
    doc_login = client.post("/api/auth/login", json={"email": "doctor@hospital.org", "password": "doctor123"})
    token = doc_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query history for returning patient
    res = client.get("/api/patients/P0011/history", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_history"] is True
    assert data["total_visits"] >= 2
    assert "Returning Patient" in data["history_badge"]

    # Query history for first-time patient
    res_new = client.get("/api/patients/NON_EXISTENT/history", headers=headers)
    assert res_new.status_code == 200
    data_new = res_new.json()
    assert data_new["has_history"] is False
    assert "First-Time Patient" in data_new["history_badge"]


def test_live_queue_and_override():
    """Scenario: Doctor overrides AI recommendation, verifies audit logging."""
    doc_login = client.post("/api/auth/login", json={"email": "doctor@hospital.org", "password": "doctor123"})
    token = doc_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get queue
    q_res = client.get("/api/queue", headers=headers)
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert len(q_data["queue"]) > 0

    # Pick a patient to override
    target = q_data["queue"][0]
    override_res = client.post("/api/triage/override", headers=headers, json={
        "encounter_id": target["encounter_id"],
        "final_triage_level": 1,
        "final_department": "Emergency",
        "reason_code": "PATIENT_CLINICALLY_WORSE",
        "reason_free_text": "Patient exhibits signs of decompensating shock",
    })
    assert override_res.status_code == 200
    assert override_res.json()["audit_logged"] is True

    # Check audit log contains the override
    audit_res = client.get("/api/audit", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()["logs"]
    assert any(l["action"] == "CLINICIAN_OVERRIDDEN" for l in logs)


def test_surge_mode_and_actions():
    """Scenario: Surge mode activation and retrieval of action required items."""
    doc_login = client.post("/api/auth/login", json={"email": "doctor@hospital.org", "password": "doctor123"})
    token = doc_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Activate surge
    act_res = client.post("/api/surge/activate", headers=headers, json={
        "reason": "Mass casualty influx",
        "reason_detail": "Multi-vehicle collision on highway",
    })
    assert act_res.status_code == 200
    assert act_res.json()["is_surge"] is True

    # Check surge status
    status_res = client.get("/api/surge/status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["operating_mode"] == "SURGE"

    # Deactivate surge
    deact_res = client.post("/api/surge/deactivate", headers=headers, json={})
    assert deact_res.status_code == 200
    assert deact_res.json()["is_surge"] is False
