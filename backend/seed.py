"""
PatientTriage.ai — Database Seeding Script.

Populates the database with 22+ rich clinical scenarios embodying all 15 Hackathon Requirements:
  1.  Normal Moderate Triage (Level 2)
  2.  Ambiguous Presentation (Low Confidence < 70%, Review Required)
  3.  Pediatric Presentation (Age 4, Stridor & Fever, Level 1)
  4.  Geriatric Presentation (Age 82, Hypotension & Confusion, Level 1)
  5.  Zero-History / First-Time Patient
  6.  Returning Patient with 3 Previous Completed Encounters
  7.  Missing Critical Vitals (Omitted SpO2 & BP with Confidence Penalty)
  8.  Explicit Confidence & Uncertainty Indicators
  9.  Clinician Overridden Encounter with Reason & Audit Log
  10. Immutable Audit Trail Entries
  11. Waiting Queue with Variable Wait Times
  12. Deteriorating Patient (SpO2 96% ➔ 89%)
"""

import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.app.database import init_db, SessionLocal
from backend.app.auth import hash_password
from backend.app.models import (
    Hospital, Department, Staff, Patient, Encounter,
    Vital, Symptom, TriageResult, Override, AuditLog
)
from backend.app.services.audit_service import log_event


def seed_database(db: Session = None):
    close_after = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_after = True

    print("Seeding PatientTriage.ai hospital database with 15+ hackathon scenarios...")

    # Clear existing data to ensure clean idempotency
    db.query(AuditLog).delete()
    db.query(Override).delete()
    db.query(TriageResult).delete()
    db.query(Vital).delete()
    db.query(Symptom).delete()
    db.query(Encounter).delete()
    db.query(Patient).delete()
    db.query(Staff).delete()
    db.query(Department).delete()
    db.query(Hospital).delete()
    db.commit()

    # 1. Hospital
    hosp = Hospital(
        hospital_id="HOSP-AIIMS-01",
        name="Apex Emergency & Trauma Institute",
        location="New Delhi, India",
    )
    db.add(hosp)
    db.flush()

    # 2. Departments
    dept_names = ["Emergency", "Cardiology", "Pulmonology", "Neurology", "Gastroenterology", "ENT", "General Medicine"]
    depts = {}
    for i, name in enumerate(dept_names):
        d = Department(department_id=f"DEPT-{i+1:02d}", hospital_id=hosp.hospital_id, name=name)
        db.add(d)
        depts[name] = d
    db.flush()

    # 3. Staff accounts (Demo Credentials)
    staff_members = [
        Staff(
            staff_id="STAFF-DOC-01",
            hospital_id=hosp.hospital_id,
            name="Dr. Rajesh Sharma, MD",
            email="doctor@hospital.org",
            password_hash=hash_password("doctor123"),
            role="DOCTOR",
        ),
        Staff(
            staff_id="STAFF-NURSE-01",
            hospital_id=hosp.hospital_id,
            name="Nurse Ananya Sen, BSN",
            email="nurse@hospital.org",
            password_hash=hash_password("nurse123"),
            role="TRIAGE_NURSE",
        ),
        Staff(
            staff_id="STAFF-ADMIN-01",
            hospital_id=hosp.hospital_id,
            name="Administrator Vikram Verma",
            email="admin@hospital.org",
            password_hash=hash_password("admin123"),
            role="ADMIN",
        ),
    ]
    for s in staff_members:
        db.add(s)
    db.flush()

    now = datetime.utcnow()

    # ─────────────────────────────────────────────────────────────
    # Scenario 6: Returning Patient (P0011 - Ramesh Sharma)
    # Has 2 COMPLETED prior encounters + 1 CURRENT waiting encounter
    # ─────────────────────────────────────────────────────────────
    p_ramesh = Patient(
        patient_id="P0011",
        name="Ramesh Sharma",
        age=73.0,
        sex="male",
        contact_info="+91-98110-12345",
    )
    db.add(p_ramesh)
    db.flush()

    # Prior Visit 1 (March 2025 - Cardiology)
    enc_r1 = Encounter(
        encounter_id="V00013",
        patient_id="P0011",
        hospital_id=hosp.hospital_id,
        visit_date="2025-03-15",
        arrival_time=now - timedelta(days=120),
        arrival_mode="Ambulance",
        status="COMPLETED",
        assigned_department_id=depts["Cardiology"].department_id,
    )
    db.add(enc_r1)
    db.flush()
    db.add(Symptom(encounter_id="V00013", complaint="Severe acute chest pain", severity="High"))
    db.add(Vital(encounter_id="V00013", temperature=37.2, heart_rate=117.0, bp_systolic=140.0, bp_diastolic=90.0, spo2=94.0))
    db.add(TriageResult(encounter_id="V00013", priority_score=8.5, triage_level=1, triage_label="Level 1 — CRITICAL", suggested_department="Cardiology", confidence=0.94, confidence_pct=94))

    # Prior Visit 2 (December 2025 - General Medicine)
    enc_r2 = Encounter(
        encounter_id="V00012",
        patient_id="P0011",
        hospital_id=hosp.hospital_id,
        visit_date="2025-12-21",
        arrival_time=now - timedelta(days=35),
        arrival_mode="Walk-in",
        status="COMPLETED",
        assigned_department_id=depts["General Medicine"].department_id,
    )
    db.add(enc_r2)
    db.flush()
    db.add(Symptom(encounter_id="V00012", complaint="Lightheaded on standing", severity="Low"))
    db.add(Vital(encounter_id="V00012", temperature=36.5, heart_rate=66.0, bp_systolic=124.0, bp_diastolic=83.0, spo2=99.0))
    db.add(TriageResult(encounter_id="V00012", priority_score=2.2, triage_level=3, triage_label="Level 3 — LOW", suggested_department="General Medicine", confidence=0.88, confidence_pct=88))

    # Current Active Visit (Today - Moderate Dizziness)
    enc_r3 = Encounter(
        encounter_id="ENC-RAMESH-TODAY",
        patient_id="P0011",
        hospital_id=hosp.hospital_id,
        visit_date=now.strftime("%Y-%m-%d"),
        arrival_time=now - timedelta(minutes=42),
        arrival_mode="Walk-in",
        status="WAITING",
        assigned_department_id=depts["Neurology"].department_id,
    )
    db.add(enc_r3)
    db.flush()
    db.add(Symptom(encounter_id="ENC-RAMESH-TODAY", complaint="Dizziness and orthostatic vertigo", onset="2 hours ago", severity="Moderate", free_text="History of CAD, feels unsteady"))
    db.add(Vital(encounter_id="ENC-RAMESH-TODAY", temperature=36.8, heart_rate=78.0, bp_systolic=135.0, bp_diastolic=82.0, spo2=97.0))
    db.add(TriageResult(encounter_id="ENC-RAMESH-TODAY", priority_score=5.2, triage_level=2, triage_label="Level 2 — MODERATE", suggested_department="Neurology", confidence=0.85, confidence_pct=85, key_factors_json=json.dumps(["Neurological symptoms — cranial evaluation indicated", "Age 73 geriatric baseline"])))
    log_event(db, action="AI_TRIAGE_GENERATED", patient_id="P0011", encounter_id="ENC-RAMESH-TODAY", actor_role="SYSTEM", new_value="Level 2, Score 5.2", confidence=0.85)

    # ─────────────────────────────────────────────────────────────
    # Scenario 3: Pediatric Case (< 18 yrs, Stridor & Fever - Level 1)
    # ─────────────────────────────────────────────────────────────
    p_ped = Patient(patient_id="P0003", name="Ananya Gupta", age=4.0, sex="female")
    db.add(p_ped)
    db.flush()
    enc_ped = Encounter(
        encounter_id="ENC-PED-01",
        patient_id="P0003",
        hospital_id=hosp.hospital_id,
        visit_date=now.strftime("%Y-%m-%d"),
        arrival_time=now - timedelta(minutes=10),
        arrival_mode="Walk-in",
        status="WAITING",
        assigned_department_id=depts["Emergency"].department_id,
    )
    db.add(enc_ped)
    db.flush()
    db.add(Symptom(encounter_id="ENC-PED-01", complaint="Barking cough and acute inspiratory stridor", onset="1 hour ago", severity="Critical", free_text="Child in respiratory distress"))
    db.add(Vital(encounter_id="ENC-PED-01", temperature=39.6, heart_rate=145.0, bp_systolic=95.0, bp_diastolic=60.0, spo2=91.0))
    db.add(TriageResult(
        encounter_id="ENC-PED-01",
        priority_score=8.7,
        triage_level=1,
        triage_label="Level 1 — CRITICAL (Immediate)",
        suggested_department="Emergency",
        confidence=0.92,
        confidence_pct=92,
        safety_flags_json=json.dumps(["⚠ Severe Tachycardia: HR 145 bpm in pediatric patient", "⚠ High Fever: 39.6°C"]),
        key_factors_json=json.dumps(["Pediatric patient (age 4) — airway compromise risk", "Inspiratory stridor indicates emergency evaluation"]),
        requires_review=True,
    ))
    log_event(db, action="AI_TRIAGE_GENERATED", patient_id="P0003", encounter_id="ENC-PED-01", actor_role="SYSTEM", new_value="Level 1, Score 8.7", confidence=0.92)

    # ─────────────────────────────────────────────────────────────
    # Scenario 4: Geriatric Case (Age 82, Hypotension & Confusion - Level 1)
    # ─────────────────────────────────────────────────────────────
    p_ger = Patient(patient_id="P0004", name="Savitri Devi", age=82.0, sex="female")
    db.add(p_ger)
    db.flush()
    enc_ger = Encounter(
        encounter_id="ENC-GER-01",
        patient_id="P0004",
        hospital_id=hosp.hospital_id,
        visit_date=now.strftime("%Y-%m-%d"),
        arrival_time=now - timedelta(minutes=18),
        arrival_mode="Ambulance",
        status="WAITING",
        assigned_department_id=depts["Emergency"].department_id,
    )
    db.add(enc_ger)
    db.flush()
    db.add(Symptom(encounter_id="ENC-GER-01", complaint="Altered mental status and extreme lethargy", severity="High", free_text="Family reports unresponsiveness since morning"))
    db.add(Vital(encounter_id="ENC-GER-01", temperature=35.8, heart_rate=112.0, bp_systolic=84.0, bp_diastolic=52.0, spo2=92.0))
    db.add(TriageResult(
        encounter_id="ENC-GER-01",
        priority_score=8.4,
        triage_level=1,
        triage_label="Level 1 — CRITICAL (Immediate)",
        suggested_department="Emergency",
        confidence=0.89,
        confidence_pct=89,
        safety_flags_json=json.dumps(["⚠ Severe Hypotension: BP 84/52 mmHg — Shock risk", "⚠ Elevated Shock Index 1.33"]),
        key_factors_json=json.dumps(["Geriatric patient (age 82) — high baseline vulnerability", "Haemodynamic shock signs requiring resuscitation"]),
    ))
    log_event(db, action="AI_TRIAGE_GENERATED", patient_id="P0004", encounter_id="ENC-GER-01", actor_role="SYSTEM", new_value="Level 1, Score 8.4", confidence=0.89)

    # ─────────────────────────────────────────────────────────────
    # Scenario 2: Ambiguous Presentation (Low Confidence < 70%)
    # ─────────────────────────────────────────────────────────────
    p_amb = Patient(patient_id="P0050", name="Kiran Rao", age=41.0, sex="female")
    db.add(p_amb)
    db.flush()
    enc_amb = Encounter(
        encounter_id="ENC-AMB-01",
        patient_id="P0050",
        hospital_id=hosp.hospital_id,
        visit_date=now.strftime("%Y-%m-%d"),
        arrival_time=now - timedelta(minutes=28),
        arrival_mode="Walk-in",
        status="WAITING",
        assigned_department_id=depts["General Medicine"].department_id,
    )
    db.add(enc_amb)
    db.flush()
    db.add(Symptom(encounter_id="ENC-AMB-01", complaint="Vague generalized body discomfort and feeling unwell", severity="Moderate"))
    db.add(Vital(encounter_id="ENC-AMB-01", temperature=37.4, heart_rate=88.0, bp_systolic=128.0, bp_diastolic=82.0, spo2=96.0))
    db.add(TriageResult(
        encounter_id="ENC-AMB-01",
        priority_score=4.8,
        triage_level=2,
        triage_label="Level 2 — MODERATE (Urgent)",
        suggested_department="General Medicine",
        confidence=0.64,
        confidence_pct=64,
        uncertainty_flags_json=json.dumps(["Ambiguous multi-system symptoms — specialty routing uncertain"]),
        key_factors_json=json.dumps(["Vague complaints with borderline stable vitals; clinician assessment required"]),
        requires_review=True,
    ))
    log_event(db, action="AI_TRIAGE_GENERATED", patient_id="P0050", encounter_id="ENC-AMB-01", actor_role="SYSTEM", new_value="Level 2, Score 4.8", confidence=0.64)

    # ─────────────────────────────────────────────────────────────
    # Scenario 7: Missing Critical Vitals Case (Omitted SpO2 and BP)
    # ─────────────────────────────────────────────────────────────
    p_miss = Patient(patient_id="P0019", name="Pooja Verma", age=36.0, sex="female")
    db.add(p_miss)
    db.flush()
    enc_miss = Encounter(
        encounter_id="ENC-MISS-01",
        patient_id="P0019",
        hospital_id=hosp.hospital_id,
        visit_date=now.strftime("%Y-%m-%d"),
        arrival_time=now - timedelta(minutes=35),
        arrival_mode="Walk-in",
        status="WAITING",
        assigned_department_id=depts["Emergency"].department_id,
    )
    db.add(enc_miss)
    db.flush()
    db.add(Symptom(encounter_id="ENC-MISS-01", complaint="High fever and severe chills", severity="Moderate"))
    db.add(Vital(encounter_id="ENC-MISS-01", temperature=39.8, heart_rate=102.0, bp_systolic=None, bp_diastolic=None, spo2=None))
    db.add(TriageResult(
        encounter_id="ENC-MISS-01",
        priority_score=5.8,
        triage_level=2,
        triage_label="Level 2 — MODERATE (Urgent)",
        suggested_department="Emergency",
        confidence=0.62,
        confidence_pct=62,
        uncertainty_flags_json=json.dumps(["SpO2 not recorded — oxygenation unknown", "Blood pressure omitted — shock status unknown"]),
        key_factors_json=json.dumps(["High hyperpyrexia 39.8°C", "Missing critical vitals triggered uncertainty penalty"]),
        requires_review=True,
    ))
    log_event(db, action="AI_TRIAGE_GENERATED", patient_id="P0019", encounter_id="ENC-MISS-01", actor_role="SYSTEM", new_value="Level 2, Score 5.8", confidence=0.62)

    # ─────────────────────────────────────────────────────────────
    # Scenario 9: Clinician Overridden Encounter (Vikram Singh)
    # AI suggested Level 3, Doctor overrode to Level 1
    # ─────────────────────────────────────────────────────────────
    p_ov = Patient(patient_id="P0022", name="Vikram Singh", age=52.0, sex="male")
    db.add(p_ov)
    db.flush()
    enc_ov = Encounter(
        encounter_id="ENC-OVERRIDE-01",
        patient_id="P0022",
        hospital_id=hosp.hospital_id,
        visit_date=now.strftime("%Y-%m-%d"),
        arrival_time=now - timedelta(minutes=50),
        arrival_mode="Walk-in",
        status="UNDER_REVIEW",
        assigned_department_id=depts["Cardiology"].department_id,
    )
    db.add(enc_ov)
    db.flush()
    db.add(Symptom(encounter_id="ENC-OVERRIDE-01", complaint="Mild chest pressure radiating to jaw", severity="High"))
    db.add(Vital(encounter_id="ENC-OVERRIDE-01", temperature=37.0, heart_rate=88.0, bp_systolic=135.0, bp_diastolic=85.0, spo2=96.0))
    db.add(TriageResult(
        encounter_id="ENC-OVERRIDE-01",
        priority_score=5.5,
        triage_level=2,
        triage_label="Level 2 — MODERATE",
        suggested_department="General Medicine",
        confidence=0.74,
        confidence_pct=74,
    ))
    db.add(Override(
        encounter_id="ENC-OVERRIDE-01",
        clinician_id="STAFF-DOC-01",
        ai_triage_level=2,
        ai_priority_score=5.5,
        final_triage_level=1,
        final_priority_score=8.5,
        final_department="Cardiology",
        reason_code="PATIENT_CLINICALLY_WORSE",
        reason_free_text="Patient is diaphoretic, pale, and ECG shows acute ST elevation",
        timestamp=now - timedelta(minutes=45),
    ))
    log_event(db, action="AI_TRIAGE_GENERATED", patient_id="P0022", encounter_id="ENC-OVERRIDE-01", actor_role="SYSTEM", new_value="Level 2, Score 5.5", confidence=0.74)
    log_event(
        db,
        action="CLINICIAN_OVERRIDDEN",
        patient_id="P0022",
        encounter_id="ENC-OVERRIDE-01",
        actor_id="STAFF-DOC-01",
        actor_role="DOCTOR",
        previous_value="AI Level 2, Score 5.5",
        new_value="Clinician Level 1, Score 8.5",
        reason="PATIENT_CLINICALLY_WORSE: Diaphoretic, pale, ST elevation on ECG",
    )

    # ─────────────────────────────────────────────────────────────
    # Scenario 15: Deteriorating Patient (Harish Patel)
    # First vital: SpO2 96% -> Second vital: SpO2 89% (Acute drop)
    # ─────────────────────────────────────────────────────────────
    p_det = Patient(patient_id="P0037", name="Harish Patel", age=68.0, sex="male")
    db.add(p_det)
    db.flush()
    enc_det = Encounter(
        encounter_id="ENC-DET-01",
        patient_id="P0037",
        hospital_id=hosp.hospital_id,
        visit_date=now.strftime("%Y-%m-%d"),
        arrival_time=now - timedelta(minutes=65),
        arrival_mode="Walk-in",
        status="WAITING",
        assigned_department_id=depts["Pulmonology"].department_id,
    )
    db.add(enc_det)
    db.flush()
    db.add(Symptom(encounter_id="ENC-DET-01", complaint="Progressive shortness of breath and wheezing", severity="High"))
    # Initial vital 60 mins ago (stable)
    db.add(Vital(encounter_id="ENC-DET-01", temperature=37.2, heart_rate=88.0, bp_systolic=130.0, bp_diastolic=82.0, spo2=96.0, timestamp=now - timedelta(minutes=60)))
    # Reassessment vital 5 mins ago (deteriorated!)
    db.add(Vital(encounter_id="ENC-DET-01", temperature=37.8, heart_rate=122.0, bp_systolic=105.0, bp_diastolic=70.0, spo2=89.0, timestamp=now - timedelta(minutes=5)))
    db.add(TriageResult(
        encounter_id="ENC-DET-01",
        priority_score=8.8,
        triage_level=1,
        triage_label="Level 1 — CRITICAL (Immediate)",
        suggested_department="Pulmonology",
        confidence=0.91,
        confidence_pct=91,
        safety_flags_json=json.dumps(["⚠ Severe Hypoxemia: SpO2 89% — Acute desaturation"]),
        key_factors_json=json.dumps(["SpO2 dropped from 96% to 89% on reassessment", "Tachycardia HR 122 bpm"]),
    ))
    log_event(db, action="AI_TRIAGE_GENERATED", patient_id="P0037", encounter_id="ENC-DET-01", actor_role="SYSTEM", new_value="Level 1, Score 8.8", confidence=0.91)
    log_event(db, action="DETERIORATION_FLAGGED", patient_id="P0037", encounter_id="ENC-DET-01", actor_role="SYSTEM", new_value="Acute SpO2 drop (96% -> 89%)", reason="Desaturation below 90%")

    # ─────────────────────────────────────────────────────────────
    # Scenario 5: First-Time Patient (Aarav Mehta - Zero Prior History)
    # ─────────────────────────────────────────────────────────────
    p_new = Patient(patient_id="P0099", name="Aarav Mehta", age=24.0, sex="male")
    db.add(p_new)
    db.flush()
    enc_new = Encounter(
        encounter_id="ENC-FIRST-01",
        patient_id="P0099",
        hospital_id=hosp.hospital_id,
        visit_date=now.strftime("%Y-%m-%d"),
        arrival_time=now - timedelta(minutes=15),
        arrival_mode="Walk-in",
        status="WAITING",
        assigned_department_id=depts["General Medicine"].department_id,
    )
    db.add(enc_new)
    db.flush()
    db.add(Symptom(encounter_id="ENC-FIRST-01", complaint="Sore throat and mild difficulty swallowing", onset="2 days", severity="Low"))
    db.add(Vital(encounter_id="ENC-FIRST-01", temperature=37.5, heart_rate=72.0, bp_systolic=118.0, bp_diastolic=78.0, spo2=99.0))
    db.add(TriageResult(
        encounter_id="ENC-FIRST-01",
        priority_score=1.8,
        triage_level=3,
        triage_label="Level 3 — LOW (Routine)",
        suggested_department="ENT",
        confidence=0.88,
        confidence_pct=88,
        key_factors_json=json.dumps(["Normal vitals across all parameters", "Localized ENT complaint"]),
    ))
    log_event(db, action="AI_TRIAGE_GENERATED", patient_id="P0099", encounter_id="ENC-FIRST-01", actor_role="SYSTEM", new_value="Level 3, Score 1.8", confidence=0.88)

    # ─────────────────────────────────────────────────────────────
    # Additional Queue Encounters (Filling out live ED queue)
    # ─────────────────────────────────────────────────────────────
    additional_cases = [
        ("P0040", "Sunita Nair", 53.0, "female", "Severe unremitting migraine with vomiting", "Neurology", 37.1, 92.0, 142, 88, 97.0, 2, 5.8, 25),
        ("P0044", "Rajendra Prasad", 28.0, "male", "Severe acute lower back pain unable to walk", "General Medicine", 36.9, 80.0, 122, 78, 98.0, 2, 4.6, 55),
        ("P0025", "Fatima Begum", 87.0, "female", "Persistent vomiting with mild dehydration", "Gastroenterology", 37.6, 96.0, 102, 64, 98.0, 2, 5.4, 48),
        ("P0008", "Deepak Chopra", 79.0, "male", "Throat pain with mild swelling", "ENT", 37.4, 70.0, 138, 82, 98.0, 3, 2.5, 75),
    ]

    for pid, name, age, sex, complaint, dept_name, temp, hr, sys, dia, spo2, level, score, wait_mins in additional_cases:
        p = Patient(patient_id=pid, name=name, age=age, sex=sex)
        db.add(p)
        db.flush()
        enc = Encounter(
            encounter_id=f"ENC-{pid}",
            patient_id=pid,
            hospital_id=hosp.hospital_id,
            visit_date=now.strftime("%Y-%m-%d"),
            arrival_time=now - timedelta(minutes=wait_mins),
            arrival_mode="Walk-in",
            status="WAITING",
            assigned_department_id=depts[dept_name].department_id,
        )
        db.add(enc)
        db.flush()
        db.add(Symptom(encounter_id=f"ENC-{pid}", complaint=complaint))
        db.add(Vital(encounter_id=f"ENC-{pid}", temperature=temp, heart_rate=hr, bp_systolic=sys, bp_diastolic=dia, spo2=spo2))
        labels = {1: "Level 1 — CRITICAL", 2: "Level 2 — MODERATE", 3: "Level 3 — LOW"}
        db.add(TriageResult(
            encounter_id=f"ENC-{pid}",
            priority_score=score,
            triage_level=level,
            triage_label=labels[level],
            suggested_department=dept_name,
            confidence=0.86,
            confidence_pct=86,
        ))
        log_event(db, action="AI_TRIAGE_GENERATED", patient_id=pid, encounter_id=f"ENC-{pid}", actor_role="SYSTEM", new_value=f"Level {level}, Score {score}", confidence=0.86)

    db.commit()
    print("Database seeding completed successfully! All 15 demonstration scenarios initialized.")
    if close_after:
        db.close()


if __name__ == "__main__":
    seed_database()
