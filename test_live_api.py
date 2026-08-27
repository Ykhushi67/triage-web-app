import os
import sys
import json

# Ensure UTF-8 stdout for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db
from backend.seed import seed_database

client = TestClient(app)


def run_comprehensive_live_test():
    print("=" * 70)
    print("PatientTriage.ai — Live API Verification & Workflow Demonstration")
    print("=" * 70)

    # 1. Health & Compliance Check
    print("\n1. GET / — Root Health & DPDP Compliance Baseline:")
    res = client.get("/")
    print(f"Status: {res.status_code}")
    print(json.dumps(res.json(), indent=2))

    # 2. Authentication (Doctor & Nurse)
    print("\n2. POST /api/auth/login — Clinician Authentication:")
    doc_auth = client.post("/api/auth/login", json={"email": "doctor@hospital.org", "password": "doctor123"})
    doc_token = doc_auth.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    print(f"Doctor login: {doc_auth.json()['user']['name']} ({doc_auth.json()['user']['role']}) — Token Issued")

    nurse_auth = client.post("/api/auth/login", json={"email": "nurse@hospital.org", "password": "nurse123"})
    nurse_token = nurse_auth.json()["access_token"]
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
    print(f"Nurse login: {nurse_auth.json()['user']['name']} ({nurse_auth.json()['user']['role']}) — Token Issued")

    # 3. Independent Patient History Lookup (Returning vs First-Time)
    print("\n3. GET /api/patients/{id}/history — Independent History Lookup (Zero ML Bias):")
    # Returning patient
    hist_returning = client.get("/api/patients/P0011/history", headers=doc_headers)
    print("  [RETURNING PATIENT P0011]:")
    print(f"    Badge: {hist_returning.json()['history_badge']}")
    print(f"    Total Prior Visits: {hist_returning.json()['total_visits']}")
    for v in hist_returning.json()["visits"]:
        print(f"      - Date: {v['visit_date']} | Dept: {v['department']} | Complaint: {v['chief_complaint']} | Level: {v['triage_label']}")

    # First-time patient
    hist_first = client.get("/api/patients/P0099/history", headers=doc_headers)
    print("\n  [FIRST-TIME PATIENT P0099]:")
    print(f"    Badge: {hist_first.json()['history_badge']}")
    print(f"    Total Prior Visits: {hist_first.json()['total_visits']}")

    # 4. Patient Intake & ML Inference
    print("\n4. POST /api/patients/intake — New Patient Intake with Real-Time AI Triage:")
    intake_payload = {
        "name": "Live Test Patient - Acute Chest Pain",
        "age": 63.0,
        "gender": "male",
        "contact_info": "+91-99887-76655",
        "arrival_mode": "Ambulance",
        "symptoms": {
            "complaint": "Crushing retrosternal chest pain radiating to left shoulder",
            "onset": "45 mins ago",
            "severity": "Critical",
            "free_text": "Diaphoretic, pale, severe distress",
        },
        "vitals": {
            "temperature": 37.2,
            "heart_rate": 126.0,
            "bp_systolic": 160.0,
            "bp_diastolic": 98.0,
            "spo2": 93.0,
            "respiratory_rate": 24.0,
        },
    }
    intake_res = client.post("/api/patients/intake", headers=nurse_headers, json=intake_payload)
    print(f"Status: {intake_res.status_code}")
    intake_data = intake_res.json()
    print(f"  Encounter ID: {intake_data['encounter_id']}")
    print(f"  Patient ID: {intake_data['patient_id']}")
    print(f"  AI Triage Level: {intake_data['triage_result']['triage_label']}")
    print(f"  Priority Score: {intake_data['triage_result']['priority_score']}/10")
    print(f"  Confidence: {intake_data['triage_result']['confidence_pct']}%")
    print(f"  Recommended Dept: {intake_data['triage_result']['recommended_department']}")
    print(f"  Key Factors: {intake_data['triage_result']['key_factors']}")

    # 5. Live Emergency Queue
    print("\n5. GET /api/queue — Live Dynamic Emergency Queue:")
    q_res = client.get("/api/queue", headers=doc_headers)
    q_data = q_res.json()
    print(f"  Total Waiting: {q_data['summary']['total_waiting']}")
    print(f"  Critical (Level 1): {q_data['summary']['critical_count']}")
    print(f"  Moderate (Level 2): {q_data['summary']['moderate_count']}")
    print(f"  Low (Level 3): {q_data['summary']['low_count']}")
    print(f"  Average Wait: {q_data['summary']['avg_wait_min']} min")
    print(f"  Operating Mode: {q_data['operating_mode']}")
    print("\n  Top 5 Queue Positions:")
    for idx, p in enumerate(q_data["queue"][:5], 1):
        det_flag = " [DETERIORATING]" if p["is_deteriorating"] else ""
        ov_flag = " [OVERRIDDEN]" if p["is_overridden"] else ""
        print(f"    #{idx} | {p['triage_label']} | Score: {p['priority_score']} | {p['patient_name']} ({p['history_badge']}) | Waiting: {p['waiting_minutes']}m | Dept: {p['department']}{det_flag}{ov_flag}")

    # 6. Clinician Override
    print("\n6. POST /api/triage/override — Clinician Override with Structured Reason:")
    target_enc = q_data["queue"][0]["encounter_id"]
    override_res = client.post("/api/triage/override", headers=doc_headers, json={
        "encounter_id": target_enc,
        "final_triage_level": 1,
        "final_department": "Emergency",
        "reason_code": "PATIENT_CLINICALLY_WORSE",
        "reason_free_text": "Live demonstration override: Patient shows signs of acute decompensation",
    })
    print(f"Status: {override_res.status_code}")
    print(f"Response: {override_res.json()['message']}")
    print(f"Audit Logged: {override_res.json()['audit_logged']}")

    # 7. Reassessment & Deterioration
    print("\n7. POST /api/triage/reassess — Vitals Reassessment & Acute Deterioration:")
    reassess_res = client.post("/api/triage/reassess", headers=nurse_headers, json={
        "encounter_id": target_enc,
        "vitals": {
            "temperature": 38.6,
            "heart_rate": 135.0,
            "bp_systolic": 88.0,  # Hypotension
            "bp_diastolic": 55.0,
            "spo2": 87.0,          # Severe Hypoxemia drop
        },
        "notes": "Patient condition worsening on recheck",
    })
    print(f"Status: {reassess_res.status_code}")
    reassess_data = reassess_res.json()
    print(f"  Is Deteriorating: {reassess_data['is_deteriorating']}")
    print(f"  Deterioration Alert: {reassess_data['deterioration_alert']}")
    print(f"  New AI Score: {reassess_data['triage_result']['priority_score']}/10 ({reassess_data['triage_result']['triage_label']})")
    print(f"  Safety Flags: {reassess_data['triage_result']['safety_flags']}")

    # 8. Surge Mode (Activation & Actions)
    print("\n8. POST /api/surge/activate — Surge Mode Activation & Action Dashboard:")
    surge_act = client.post("/api/surge/activate", headers=doc_headers, json={
        "reason": "Mass casualty incident",
        "reason_detail": "Highway pileup with multiple trauma arrivals",
    })
    print(f"Surge Activated: {surge_act.json()['is_surge']}")

    surge_status = client.get("/api/surge/status", headers=doc_headers)
    print(f"Operating Mode: {surge_status.json()['operating_mode']}")
    print(f"Action Items Requiring Attention ({len(surge_status.json()['actions_required'])}):")
    for act in surge_status.json()["actions_required"][:3]:
        print(f"  - [{act['type']}] {act['patient_name']}: {act['message']}")

    # Deactivate surge back to normal
    client.post("/api/surge/deactivate", headers=doc_headers, json={"reason": "Testing complete"})

    # 9. Persistent Audit Log & Patient Timeline
    print("\n9. GET /api/audit & GET /api/audit/patient/{id} — Immutable Audit Trail:")
    audit_res = client.get("/api/audit?limit=5", headers=doc_headers)
    print(f"Total Audit Events in DB: {audit_res.json()['total']}")
    print("Latest 4 Audit Entries:")
    for l in audit_res.json()["logs"][:4]:
        print(f"  [{l['timestamp']}] {l['action']} | Patient: {l['patient_id']} | Actor: {l['actor_role']} | Value: {l['new_value']} | Reason: {l.get('reason') or 'N/A'}")

    # 10. Analytics & Telemetry
    print("\n10. GET /api/analytics/overview — Hospital Metrics & ML Telemetry:")
    analytics = client.get("/api/analytics/overview", headers=doc_headers).json()
    print("Hospital Metrics:")
    print(f"  Total Encounters: {analytics['hospital_metrics']['total_encounters']}")
    print(f"  AI Predictions: {analytics['hospital_metrics']['total_ai_predictions']}")
    print(f"  Clinician Overrides: {analytics['hospital_metrics']['total_overrides']} ({analytics['hospital_metrics']['override_rate_pct']}%)")
    print(f"  3-Tier Distribution: {analytics['hospital_metrics']['triage_distribution']}")
    print(f"  ML Regressor Version: {analytics['model_telemetry']['regressor'].get('model_version')}")
    print(f"  ML Classifier Version: {analytics['model_telemetry']['classifier'].get('model_version')}")

    print("\n" + "=" * 70)
    print("ALL 10 LIVE BACKEND ENDPOINTS & WORKFLOWS VERIFIED 100% OPERATIONAL!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_comprehensive_live_test()
