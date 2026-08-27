"""PatientTriage.ai — Patient Registration & Independent History Lookup API"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models import Staff, Patient, Encounter, Department, Symptom, Vital, Hospital
from backend.app.schemas import (
    PatientCreate, PatientOut, PatientHistoryResponse,
    PatientIntakeRequest, PatientIntakeResponse
)
from backend.app.services.history_service import lookup_patient_history
from backend.app.services.audit_service import log_event
from ml.inference import inference_engine

router = APIRouter(prefix="/patients", tags=["Patients & History"])


@router.get("/{patient_id}/history", response_model=PatientHistoryResponse)
def get_patient_history(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    INDEPENDENT patient history lookup. Returns past visits for clinician context ONLY.
    This result is NEVER fed to the ML model.
    """
    return lookup_patient_history(db, patient_id)


@router.post("/intake", response_model=PatientIntakeResponse)
def patient_intake(
    req: PatientIntakeRequest,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Full patient intake:
    1. Register or retrieve patient in database.
    2. Create new encounter.
    3. Look up patient history (INDEPENDENTLY from ML).
    4. Run ML triage inference on current vitals/symptoms only.
    5. Save triage result and log audit event.
    """
    import json
    from datetime import datetime
    from backend.app.models import TriageResult

    # ── 1. Find or create patient ──
    patient = db.query(Patient).filter(Patient.name == req.name).first()
    if not patient:
        patient = Patient(
            patient_id   = f"PID-{uuid.uuid4().hex[:8].upper()}",
            name         = req.name,
            age          = req.age,
            sex          = req.gender,
            contact_info = req.contact_info,
        )
        db.add(patient)
        db.flush()

    # ── 2. Get default hospital & department ──
    hospital = db.query(Hospital).first()
    hospital_id = hospital.hospital_id if hospital else None

    # ── 3. Create encounter ──
    encounter_id = f"ENC-{uuid.uuid4().hex[:8].upper()}"
    today        = datetime.utcnow().strftime("%Y-%m-%d")
    encounter = Encounter(
        encounter_id   = encounter_id,
        patient_id     = patient.patient_id,
        hospital_id    = hospital_id,
        visit_date     = today,
        arrival_time   = datetime.utcnow(),
        arrival_mode   = req.arrival_mode,
        status         = "WAITING",
    )
    db.add(encounter)
    db.flush()

    # ── 4. Record symptoms ──
    symptom = Symptom(
        encounter_id = encounter_id,
        complaint    = req.symptoms.complaint,
        onset        = req.symptoms.onset,
        severity     = req.symptoms.severity,
        progression  = req.symptoms.progression,
        free_text    = req.symptoms.free_text,
    )
    db.add(symptom)

    # ── 5. Record vitals ──
    v = req.vitals
    # Parse BP string if provided instead of numeric fields
    bp_sys, bp_dia = v.bp_systolic, v.bp_diastolic
    if v.blood_pressure_raw and (bp_sys is None or bp_dia is None):
        from ml.preprocessing import clean_blood_pressure
        bp_sys, bp_dia, _ = clean_blood_pressure(v.blood_pressure_raw)

    vital = Vital(
        encounter_id     = encounter_id,
        temperature      = v.temperature,
        heart_rate       = v.heart_rate,
        bp_systolic      = bp_sys,
        bp_diastolic     = bp_dia,
        spo2             = v.spo2,
        respiratory_rate = v.respiratory_rate,
        recorded_by      = current_user.staff_id,
    )
    db.add(vital)

    # ── 6. Independent history lookup (SEPARATE from ML) ──
    history = lookup_patient_history(db, patient.patient_id, exclude_encounter_id=encounter_id)

    # ── 7. ML Triage Inference (current presentation ONLY) ──
    bp_str = f"{bp_sys}/{bp_dia}" if (bp_sys and bp_dia) else v.blood_pressure_raw
    prediction_input = {
        "age":            patient.age,
        "gender":         patient.sex,
        "symptoms":       req.symptoms.complaint,
        "notes":          req.symptoms.free_text or req.notes,
        "temperature":    v.temperature,
        "heart_rate":     v.heart_rate,
        "blood_pressure": bp_str,
        "spo2":           v.spo2,
    }
    triage_result_data = inference_engine.predict(prediction_input)

    # ── 8. Persist triage result ──
    triage_db = TriageResult(
        encounter_id         = encounter_id,
        priority_score       = triage_result_data.get("priority_score") or 4.0,
        triage_level         = triage_result_data.get("triage_level") or 2,
        triage_label         = triage_result_data.get("triage_label"),
        suggested_department = triage_result_data.get("recommended_department"),
        confidence           = triage_result_data.get("confidence"),
        confidence_pct       = triage_result_data.get("confidence_pct"),
        safety_flags_json    = json.dumps(triage_result_data.get("safety_flags", [])),
        key_factors_json     = json.dumps(triage_result_data.get("key_factors", [])),
        uncertainty_flags_json = json.dumps(triage_result_data.get("uncertainty_flags", [])),
        requires_review      = triage_result_data.get("requires_clinician_review", False),
        model_version        = triage_result_data.get("model_version"),
    )
    db.add(triage_db)

    # ── 9. Log audit event ──
    log_event(
        db,
        action         = "AI_TRIAGE_GENERATED",
        patient_id     = patient.patient_id,
        encounter_id   = encounter_id,
        actor_id       = current_user.staff_id,
        actor_role     = current_user.role,
        new_value      = f"Level {triage_result_data.get('triage_level')}, Score {triage_result_data.get('priority_score')}",
        confidence     = triage_result_data.get("confidence"),
        model_version  = triage_result_data.get("model_version"),
        metadata       = {"history_badge": history.history_badge},
    )

    log_event(
        db,
        action       = "PATIENT_REGISTERED",
        patient_id   = patient.patient_id,
        encounter_id = encounter_id,
        actor_id     = current_user.staff_id,
        actor_role   = current_user.role,
        new_value    = req.arrival_mode,
    )

    db.commit()

    from backend.app.schemas import TriagePredictionResponse
    triage_resp = TriagePredictionResponse(**triage_result_data)

    return PatientIntakeResponse(
        encounter_id = encounter_id,
        patient_id   = patient.patient_id,
        patient_name = patient.name,
        history      = history,
        triage_result= triage_resp,
        message      = "Patient registered and triaged successfully.",
    )
