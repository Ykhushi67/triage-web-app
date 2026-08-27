"""
PatientTriage.ai — Persistent Audit & Event Logging Service.

Append-only: audit events are NEVER updated or deleted.
Every AI prediction, clinician action, vital recheck, deterioration alert,
and surge event is immutably recorded with full context.

DPDP Note: patient_id stored (pseudonymous), NOT patient name.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models import AuditLog, SurgeEvent


def log_event(
    db: Session,
    *,
    action: str,
    patient_id: str,
    encounter_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    actor_role: Optional[str] = "SYSTEM",
    previous_value: Optional[str] = None,
    new_value: Optional[str] = None,
    reason: Optional[str] = None,
    confidence: Optional[float] = None,
    model_version: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Appends an immutable event to the audit_logs table.

    Action types:
      AI_TRIAGE_GENERATED    — New AI prediction created
      CLINICIAN_ACCEPTED     — Clinician accepted AI recommendation
      CLINICIAN_OVERRIDDEN   — Clinician overrode AI recommendation (requires reason)
      VITALS_REASSESSED      — New vitals recorded for waiting patient
      DETERIORATION_FLAGGED  — Automated deterioration alert triggered
      SURGE_AUTO_DETECTED    — System detected surge conditions
      SURGE_MANUAL_ACTIVATED — Staff manually activated surge mode
      SURGE_DEACTIVATED      — Surge mode deactivated
      PATIENT_REGISTERED     — New patient registered at ED
      PATIENT_COMPLETED      — Encounter marked completed/discharged
    """
    entry = AuditLog(
        timestamp      = datetime.utcnow(),
        encounter_id   = encounter_id,
        patient_id     = patient_id,
        actor_id       = actor_id,
        actor_role     = actor_role,
        action         = action,
        previous_value = previous_value,
        new_value      = new_value,
        reason         = reason,
        confidence     = confidence,
        model_version  = model_version,
        metadata_json  = json.dumps(metadata) if metadata else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def log_surge_event(
    db: Session,
    *,
    event_type: str,
    activated_by: Optional[str] = "SYSTEM",
    reason: Optional[str] = None,
    queue_size: Optional[int] = None,
    critical_count: Optional[int] = None,
    avg_wait_min: Optional[float] = None,
    arrival_rate: Optional[float] = None,
) -> SurgeEvent:
    """Records a surge mode transition event."""
    entry = SurgeEvent(
        timestamp     = datetime.utcnow(),
        event_type    = event_type,
        activated_by  = activated_by,
        reason        = reason,
        queue_size    = queue_size,
        critical_count= critical_count,
        avg_wait_min  = avg_wait_min,
        arrival_rate  = arrival_rate,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_patient_audit_timeline(
    db: Session,
    patient_id: str,
    limit: int = 50,
) -> list:
    """Returns chronological audit timeline for a specific patient."""
    return (
        db.query(AuditLog)
        .filter(AuditLog.patient_id == patient_id)
        .order_by(AuditLog.timestamp.asc())
        .limit(limit)
        .all()
    )


def get_recent_audit_log(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    action_filter: Optional[str] = None,
) -> list:
    """Returns paginated recent audit log entries."""
    q = db.query(AuditLog)
    if action_filter:
        q = q.filter(AuditLog.action == action_filter)
    return q.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
