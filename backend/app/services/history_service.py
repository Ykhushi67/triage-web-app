"""
PatientTriage.ai — Independent Patient History Lookup Service.

CRITICAL DESIGN PRINCIPLE:
  This service queries previous hospital encounters for display to the clinician ONLY.
  It has ZERO connection to the ML inference engine.
  Patient history is NEVER fed as input to the triage model.
  The ML model evaluates the patient's CURRENT acute presentation independently.

DPDP Note: Returns encounter-level clinical summaries only. No raw PII beyond what
  the treating clinician already has access to.
"""

from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models import Patient, Encounter, Symptom, TriageResult, Department
from backend.app.schemas import PatientHistoryResponse, HistoryVisit


def lookup_patient_history(
    db: Session,
    patient_id: str,
    exclude_encounter_id: Optional[str] = None,
) -> PatientHistoryResponse:
    """
    Performs an independent database lookup of a patient's prior hospital visits.

    Returns a structured history summary for display to the treating clinician.
    This result is NEVER passed to the ML model.

    Args:
        db: Database session.
        patient_id: The patient's unique identifier.
        exclude_encounter_id: If provided, excludes the current encounter from history.

    Returns:
        PatientHistoryResponse with history badge, visit count, and prior visit summaries.
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()

    if patient is None:
        return PatientHistoryResponse(
            patient_id    = patient_id,
            patient_name  = "Unknown",
            has_history   = False,
            total_visits  = 0,
            visits        = [],
            is_returning  = False,
            history_badge = "🟢 First-Time Patient (No Prior Hospital Records)",
        )

    # Query prior encounters (exclude current if provided)
    query = (
        db.query(Encounter)
        .filter(Encounter.patient_id == patient_id)
        .filter(Encounter.status != "WAITING")  # Only completed encounters count as history
    )
    if exclude_encounter_id:
        query = query.filter(Encounter.encounter_id != exclude_encounter_id)

    prior_encounters = query.order_by(Encounter.visit_date.desc()).all()

    if not prior_encounters:
        return PatientHistoryResponse(
            patient_id    = patient_id,
            patient_name  = patient.name,
            has_history   = False,
            total_visits  = 0,
            visits        = [],
            is_returning  = False,
            history_badge = "🟢 First-Time Patient (No Prior Hospital Records)",
        )

    # Build summary of each prior visit
    visits = []
    for enc in prior_encounters:
        # Get chief complaint
        symptom = enc.symptoms[0] if enc.symptoms else None
        complaint = symptom.complaint if symptom else None

        # Get triage level from most recent triage result
        triage = enc.triage_results[0] if enc.triage_results else None
        t_level = triage.triage_level if triage else None
        t_label = triage.triage_label if triage else None

        # Department name
        dept_name = None
        if enc.assigned_department:
            dept_name = enc.assigned_department.name

        visits.append(HistoryVisit(
            encounter_id   = enc.encounter_id,
            visit_date     = enc.visit_date,
            department     = dept_name,
            chief_complaint= complaint,
            triage_level   = t_level,
            triage_label   = t_label,
            arrival_mode   = enc.arrival_mode,
        ))

    n = len(visits)
    history_badge = f"🔵 Returning Patient — {n} Previous Visit{'s' if n != 1 else ''} Found"

    return PatientHistoryResponse(
        patient_id    = patient_id,
        patient_name  = patient.name,
        has_history   = True,
        total_visits  = n,
        visits        = visits,
        is_returning  = True,
        history_badge = history_badge,
    )
