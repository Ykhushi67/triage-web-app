"""PatientTriage.ai — Persistent Audit Log & Patient Timeline API"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models import Staff, AuditLog
from backend.app.schemas import AuditLogResponse, AuditLogEntry
from backend.app.services.audit_service import get_recent_audit_log, get_patient_audit_timeline

router = APIRouter(prefix="/audit", tags=["Audit & Governance"])


@router.get("", response_model=AuditLogResponse)
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Returns paginated immutable audit logs for regulatory traceability and clinical governance.
    DPDP principle: Uses pseudonymous patient_id reference, never raw patient name.
    """
    logs = get_recent_audit_log(db, skip=skip, limit=limit, action_filter=action)
    total = db.query(AuditLog).count()
    return AuditLogResponse(logs=[AuditLogEntry.model_validate(l) for l in logs], total=total)


@router.get("/patient/{patient_id}", response_model=List[AuditLogEntry])
def get_patient_timeline(
    patient_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """
    Returns full chronological event timeline for a specific patient
    (Arrival -> AI Prediction -> Clinician Decision -> Reassessment -> Outcome).
    """
    logs = get_patient_audit_timeline(db, patient_id=patient_id, limit=limit)
    return [AuditLogEntry.model_validate(l) for l in logs]
