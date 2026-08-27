"""PatientTriage.ai — Live Queue API"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models import Staff
from backend.app.schemas import QueueResponse
from backend.app.services.queue_service import build_queue

router = APIRouter(prefix="/queue", tags=["Live Queue"])


@router.get("", response_model=QueueResponse)
def get_live_queue(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Returns the live ED queue sorted by:
    1. Triage Level ASC (Level 1 Critical first)
    2. Priority Score DESC (higher score = more urgent within same level)
    3. Waiting time DESC (longest waiter first within same level+score)

    Includes per-patient: deterioration flag, reassessment deadline, history badge,
    safety flags, and surge recommendation.
    """
    return build_queue(db)


@router.post("/{encounter_id}/complete")
def complete_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Mark an encounter as completed / discharged."""
    from backend.app.models import Encounter
    from backend.app.services.audit_service import log_event

    enc = db.query(Encounter).filter(Encounter.encounter_id == encounter_id).first()
    if not enc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Encounter not found")

    enc.status = "COMPLETED"
    log_event(
        db,
        action       = "PATIENT_COMPLETED",
        patient_id   = enc.patient_id,
        encounter_id = enc.encounter_id,
        actor_id     = current_user.staff_id,
        actor_role   = current_user.role,
        new_value    = "COMPLETED",
    )
    db.commit()
    return {"message": "Encounter completed", "encounter_id": encounter_id}
