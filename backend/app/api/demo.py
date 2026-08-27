"""
PatientTriage.ai — Demo & Scenario Simulator API.

Provides one-click triggers for all 15 Hackathon Demonstration Scenarios:
  1.  Normal Case (Level 2 Moderate)
  2.  Ambiguous Presentation (Low Confidence < 70%)
  3.  Pediatric Case (< 18 yrs, Stridor & Fever)
  4.  Geriatric Case (82 yrs, Hypotension & Confusion)
  5.  First-Time Patient (Zero Prior History)
  6.  Returning Patient (Rich Past Encounters Card)
  7.  Missing Critical Vitals (Confidence Penalty & Safety Caution)
  8.  Explicit Uncertainty Breakdown
  9.  Clinician Override Demonstration
  10. Audit Trail Inspection
  11. Simulated 3× Surge Influx
  12. Manual Surge Mode Trigger
  13. Auto-detected Surge Simulation
  14. Continuous Monitoring & Wait Timers
  15. Acute Deterioration Alert (SpO2 96% ➔ 89%)
"""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models import Staff, Patient, Encounter, Vital, Symptom, TriageResult, Override, Hospital
from backend.app.services.audit_service import log_event
from backend.app.services.surge_service import activate_surge, deactivate_surge
from backend.seed import seed_database

router = APIRouter(prefix="/demo", tags=["Demo & Scenarios Simulator"])


@router.post("/reset")
def reset_demo_database(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Resets and re-seeds database with all 22 rich scenario records and restores Normal Mode."""
    seed_database(db)
    deactivate_surge(
        db,
        deactivated_by=current_user.staff_id,
        reason="Demo reset to normal baseline",
    )
    return {"message": "Database reset to normal baseline and populated with all 15 hackathon demonstration scenarios."}


@router.post("/trigger-deterioration")
def trigger_deterioration_scenario(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Scenario 15: Injects an acute SpO2 drop (96% -> 88%) on an active waiting patient
    to immediately demonstrate the automated deterioration alert.
    """
    enc = db.query(Encounter).filter(Encounter.status == "WAITING").first()
    if not enc:
        return {"error": "No active waiting encounter found to deteriorate."}

    new_vital = Vital(
        encounter_id=enc.encounter_id,
        temperature=38.4,
        heart_rate=128.0,
        bp_systolic=95.0,
        bp_diastolic=60.0,
        spo2=88.0,  # Acute SpO2 drop below 90%
        respiratory_rate=28.0,
        recorded_by=current_user.staff_id,
    )
    db.add(new_vital)
    
    # Escalate score
    triage = enc.triage_results[0] if enc.triage_results else None
    if triage:
        triage.priority_score = 9.0
        triage.triage_level = 1
        triage.triage_label = "Level 1 — CRITICAL (Immediate)"

    log_event(
        db,
        action="DETERIORATION_FLAGGED",
        patient_id=enc.patient_id,
        encounter_id=enc.encounter_id,
        actor_role="SYSTEM",
        new_value="Acute SpO2 drop (96% -> 88%)",
        reason="Oxygen desaturation below 90%",
    )
    db.commit()
    return {
        "message": f"Acute deterioration triggered on Patient {enc.patient.name} ({enc.patient_id})",
        "encounter_id": enc.encounter_id,
        "spo2_current": 88.0,
    }


@router.post("/trigger-surge-influx")
def trigger_surge_influx(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Scenario 11 & 13: Injects a batch of 8 urgent incoming patients to simulate a 3× volume surge
    and trigger the auto-surge detection banner.
    """
    hospital = db.query(Hospital).first()
    h_id = hospital.hospital_id if hospital else "HOSP-001"

    surge_batch = [
        ("Simulated Surge Patient A", 45, "male", "Acute crushing chest pain", 37.1, 120.0, 150, 95, 93.0, 1, 8.8),
        ("Simulated Surge Patient B", 68, "female", "Sudden breathlessness", 38.0, 115.0, 135, 85, 89.0, 1, 9.2),
        ("Simulated Surge Patient C", 32, "male", "Severe abdominal trauma", 36.8, 108.0, 110, 70, 97.0, 1, 7.5),
        ("Simulated Surge Patient D", 54, "female", "High fever with altered consciousness", 39.8, 125.0, 92, 58, 91.0, 1, 8.4),
        ("Simulated Surge Patient E", 29, "male", "Fracture left arm with deformity", 37.0, 90.0, 130, 80, 98.0, 2, 5.0),
        ("Simulated Surge Patient F", 71, "male", "Severe dizziness & syncope", 36.5, 52.0, 88, 55, 95.0, 1, 7.8),
        ("Simulated Surge Patient G", 19, "female", "Acute asthma exacerbation", 37.2, 118.0, 125, 80, 90.0, 1, 8.0),
        ("Simulated Surge Patient H", 60, "female", "Unresponsive post-fall", 36.9, 100.0, 140, 85, 94.0, 1, 8.2),
    ]

    for name, age, sex, complaint, temp, hr, sys, dia, spo2, level, score in surge_batch:
        p = Patient(
            patient_id=f"PID-SRG{uuid.uuid4().hex[:5].upper()}",
            name=name,
            age=age,
            sex=sex,
        )
        db.add(p)
        db.flush()

        enc = Encounter(
            encounter_id=f"ENC-SRG{uuid.uuid4().hex[:5].upper()}",
            patient_id=p.patient_id,
            hospital_id=h_id,
            visit_date=datetime.utcnow().strftime("%Y-%m-%d"),
            arrival_time=datetime.utcnow() - timedelta(minutes=15),
            arrival_mode="Ambulance",
            status="WAITING",
        )
        db.add(enc)
        db.flush()

        db.add(Symptom(encounter_id=enc.encounter_id, complaint=complaint))
        db.add(Vital(
            encounter_id=enc.encounter_id,
            temperature=temp,
            heart_rate=hr,
            bp_systolic=sys,
            bp_diastolic=dia,
            spo2=spo2,
        ))
        db.add(TriageResult(
            encounter_id=enc.encounter_id,
            priority_score=score,
            triage_level=level,
            triage_label="Level 1 — CRITICAL" if level == 1 else "Level 2 — MODERATE",
            suggested_department="Emergency",
            confidence=0.91,
            confidence_pct=91,
            model_version="triage-v1.0",
        ))

    db.commit()
    activate_surge(db, activated_by="AUTO_DETECTION", reason="Sudden 3x patient influx detected (Mass casualty wave)", event_type="AUTO_DETECTED")
    return {"message": "Surge wave injected! 8 critical/urgent patients added. Surge mode recommended."}
