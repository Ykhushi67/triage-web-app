"""PatientTriage.ai — Surge Mode API"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user, require_roles
from backend.app.models import Staff
from backend.app.schemas import SurgeActivateRequest, SurgeDeactivateRequest, SurgeStatusResponse
from backend.app.services.surge_service import (
    get_operating_mode, get_surge_state, activate_surge, deactivate_surge, evaluate_surge_conditions
)
from backend.app.services.queue_service import build_queue

router = APIRouter(prefix="/surge", tags=["Surge Operations"])


@router.get("/status", response_model=SurgeStatusResponse)
def get_surge_status(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Returns current surge status, load metrics, and prioritized surge actions
    answering 'What requires attention right now?'.
    """
    state = get_surge_state()
    queue_resp = build_queue(db)
    summary = queue_resp.summary

    # Compile actionable emergency items during surge
    actions_required = []
    for item in queue_resp.queue:
        if item.is_deteriorating:
            actions_required.append({
                "type": "ACUTE_DETERIORATION",
                "encounter_id": item.encounter_id,
                "patient_name": item.patient_name,
                "message": f"Vitals deteriorating (SpO2/HR/BP delta) — immediate review required",
                "priority": "HIGH",
                "action_label": "VIEW PATIENT"
            })
        elif item.confidence_pct and item.confidence_pct < 72:
            actions_required.append({
                "type": "LOW_CONFIDENCE",
                "encounter_id": item.encounter_id,
                "patient_name": item.patient_name,
                "message": f"Low AI confidence ({item.confidence_pct}%) — clinician review required",
                "priority": "HIGH",
                "action_label": "REVIEW NOW"
            })
        elif item.requires_reassessment:
            actions_required.append({
                "type": "REASSESSMENT_OVERDUE",
                "encounter_id": item.encounter_id,
                "patient_name": item.patient_name,
                "message": f"Waiting {item.waiting_minutes}m — reassessment deadline exceeded",
                "priority": "MEDIUM",
                "action_label": "REASSESS"
            })

    return SurgeStatusResponse(
        operating_mode=state["mode"],
        is_surge=(state["mode"] == "SURGE"),
        surge_since=state["activated_at"],
        queue_size=summary.total_waiting,
        critical_count=summary.critical_count,
        avg_wait_min=summary.avg_wait_min,
        surge_reason=state["reason"],
        actions_required=actions_required[:10]  # Top actionable items
    )


@router.post("/activate", response_model=SurgeStatusResponse)
def activate_surge_mode(
    req: SurgeActivateRequest,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(require_roles("DOCTOR", "ADMIN")),
):
    """
    Manually activates Surge Mode. Requires clinical justification / reason.
    Logs immutable surge event.
    """
    queue_resp = build_queue(db)
    reason_full = f"{req.reason}: {req.reason_detail or ''}".strip(": ")
    
    activate_surge(
        db,
        activated_by=current_user.staff_id,
        reason=reason_full,
        queue_size=queue_resp.summary.total_waiting,
        critical_count=queue_resp.summary.critical_count,
        avg_wait_min=queue_resp.summary.avg_wait_min,
        event_type="MANUAL_ACTIVATED",
    )
    return get_surge_status(db, current_user)


@router.post("/deactivate", response_model=SurgeStatusResponse)
def deactivate_surge_mode(
    req: SurgeDeactivateRequest,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(require_roles("DOCTOR", "ADMIN", "TRIAGE_NURSE")),
):
    """Deactivates Surge Mode and returns to Normal operations."""
    queue_resp = build_queue(db)
    deactivate_surge(
        db,
        deactivated_by=current_user.staff_id,
        reason=req.reason or "Normal load restored",
        queue_size=queue_resp.summary.total_waiting,
    )
    return get_surge_status(db, current_user)
