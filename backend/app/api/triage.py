"""PatientTriage.ai — Triage Accept / Override / Reassessment API"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user, require_roles
from backend.app.models import Staff, Encounter, Override, Vital, TriageResult
from backend.app.schemas import (
    TriagePredictionRequest, TriagePredictionResponse,
    AcceptTriageRequest, OverrideTriageRequest, ReassessmentRequest
)
from backend.app.services.audit_service import log_event
from ml.inference import inference_engine
from ml.preprocessing import clean_blood_pressure

router = APIRouter(prefix="/triage", tags=["Triage & Clinician Decisions"])


@router.post("/predict", response_model=TriagePredictionResponse)
def predict_triage(
    req: TriagePredictionRequest,
    current_user: Staff = Depends(get_current_user),
):
    """Standalone ML inference endpoint (does not save to DB)."""
    result = inference_engine.predict(req.model_dump())
    return TriagePredictionResponse(**result)


@router.post("/accept")
def accept_triage(
    req: AcceptTriageRequest,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Clinician accepts AI triage recommendation — logs acceptance event."""
    enc = db.query(Encounter).filter(Encounter.encounter_id == req.encounter_id).first()
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found")

    latest_triage = enc.triage_results[0] if enc.triage_results else None
    if not latest_triage:
        raise HTTPException(status_code=400, detail="No triage result to accept")

    enc.status = "UNDER_REVIEW"

    log_event(
        db,
        action         = "CLINICIAN_ACCEPTED",
        patient_id     = enc.patient_id,
        encounter_id   = enc.encounter_id,
        actor_id       = current_user.staff_id,
        actor_role     = current_user.role,
        new_value      = f"Level {latest_triage.triage_level}, Score {latest_triage.priority_score}",
        confidence     = latest_triage.confidence,
        model_version  = latest_triage.model_version,
    )
    db.commit()
    return {"message": "AI triage accepted", "encounter_id": req.encounter_id}


@router.post("/override")
def override_triage(
    req: OverrideTriageRequest,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(require_roles("DOCTOR", "ADMIN")),
):
    """
    Clinician overrides AI recommendation.
    Requires structured reason code — immutably logged.
    The clinician's final decision controls the patient's queue position.
    """
    enc = db.query(Encounter).filter(Encounter.encounter_id == req.encounter_id).first()
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found")

    latest_triage = enc.triage_results[0] if enc.triage_results else None
    ai_level  = latest_triage.triage_level  if latest_triage else 2
    ai_score  = latest_triage.priority_score if latest_triage else 4.0

    # Map override level to a representative score mid-point
    final_score_map = {1: 8.5, 2: 5.5, 3: 1.8}
    final_score = final_score_map.get(req.final_triage_level, 4.0)

    override = Override(
        encounter_id        = enc.encounter_id,
        clinician_id        = current_user.staff_id,
        ai_triage_level     = ai_level,
        ai_priority_score   = ai_score,
        final_triage_level  = req.final_triage_level,
        final_priority_score= final_score,
        final_department    = req.final_department,
        reason_code         = req.reason_code,
        reason_free_text    = req.reason_free_text,
        timestamp           = datetime.utcnow(),
    )
    db.add(override)
    enc.status = "UNDER_REVIEW"

    log_event(
        db,
        action         = "CLINICIAN_OVERRIDDEN",
        patient_id     = enc.patient_id,
        encounter_id   = enc.encounter_id,
        actor_id       = current_user.staff_id,
        actor_role     = current_user.role,
        previous_value = f"AI Level {ai_level}, Score {ai_score}",
        new_value      = f"Clinician Level {req.final_triage_level}, Score {final_score}",
        reason         = f"{req.reason_code}: {req.reason_free_text or ''}".strip(": "),
        confidence     = latest_triage.confidence if latest_triage else None,
        model_version  = latest_triage.model_version if latest_triage else None,
    )
    db.commit()
    return {
        "message":       "Override recorded. Clinician decision controls queue.",
        "encounter_id":  req.encounter_id,
        "final_level":   req.final_triage_level,
        "final_score":   final_score,
        "audit_logged":  True,
    }


@router.post("/reassess")
def reassess_patient(
    req: ReassessmentRequest,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Records new vitals for a waiting patient, re-runs triage inference,
    checks for deterioration, and updates audit log.
    """
    enc = db.query(Encounter).filter(Encounter.encounter_id == req.encounter_id).first()
    if not enc:
        raise HTTPException(status_code=404, detail="Encounter not found")

    v = req.vitals
    bp_sys, bp_dia = v.bp_systolic, v.bp_diastolic
    if v.blood_pressure_raw and (bp_sys is None or bp_dia is None):
        bp_sys, bp_dia, _ = clean_blood_pressure(v.blood_pressure_raw)

    new_vital = Vital(
        encounter_id     = enc.encounter_id,
        temperature      = v.temperature,
        heart_rate       = v.heart_rate,
        bp_systolic      = bp_sys,
        bp_diastolic     = bp_dia,
        spo2             = v.spo2,
        respiratory_rate = v.respiratory_rate,
        recorded_by      = current_user.staff_id,
    )
    db.add(new_vital)
    db.flush()

    # Refresh vitals to detect deterioration
    db.refresh(enc)
    from backend.app.services.queue_service import check_deterioration
    is_deteriorating = check_deterioration(enc.vitals)

    # Re-run ML triage with new vitals
    patient = enc.patient
    symptom = enc.symptoms[0] if enc.symptoms else None
    bp_str  = f"{bp_sys}/{bp_dia}" if (bp_sys and bp_dia) else v.blood_pressure_raw

    prediction = inference_engine.predict({
        "age":            patient.age,
        "gender":         patient.sex,
        "symptoms":       symptom.complaint if symptom else "",
        "notes":          req.notes or (symptom.free_text if symptom else ""),
        "temperature":    v.temperature,
        "heart_rate":     v.heart_rate,
        "blood_pressure": bp_str,
        "spo2":           v.spo2,
    })

    # Save new triage result
    new_triage = TriageResult(
        encounter_id         = enc.encounter_id,
        priority_score       = prediction.get("priority_score") or 4.0,
        triage_level         = prediction.get("triage_level") or 2,
        triage_label         = prediction.get("triage_label"),
        suggested_department = prediction.get("recommended_department"),
        confidence           = prediction.get("confidence"),
        confidence_pct       = prediction.get("confidence_pct"),
        safety_flags_json    = json.dumps(prediction.get("safety_flags", [])),
        key_factors_json     = json.dumps(prediction.get("key_factors", [])),
        uncertainty_flags_json = json.dumps(prediction.get("uncertainty_flags", [])),
        requires_review      = prediction.get("requires_clinician_review", False),
        model_version        = prediction.get("model_version"),
    )
    db.add(new_triage)

    old_triage = enc.triage_results[1] if len(enc.triage_results) > 1 else None

    log_event(
        db,
        action         = "VITALS_REASSESSED",
        patient_id     = enc.patient_id,
        encounter_id   = enc.encounter_id,
        actor_id       = current_user.staff_id,
        actor_role     = current_user.role,
        previous_value = f"Level {old_triage.triage_level if old_triage else '?'}",
        new_value      = f"Level {prediction.get('triage_level')}, Score {prediction.get('priority_score')}",
        confidence     = prediction.get("confidence"),
        model_version  = prediction.get("model_version"),
    )

    if is_deteriorating:
        log_event(
            db,
            action       = "DETERIORATION_FLAGGED",
            patient_id   = enc.patient_id,
            encounter_id = enc.encounter_id,
            actor_role   = "SYSTEM",
            new_value    = "Acute vital deterioration detected",
        )

    db.commit()
    return {
        "encounter_id":    enc.encounter_id,
        "triage_result":   prediction,
        "is_deteriorating": is_deteriorating,
        "deterioration_alert": (
            "⚠ ACUTE DETERIORATION DETECTED — Immediate reassessment required"
            if is_deteriorating else None
        ),
        "audit_logged": True,
    }
