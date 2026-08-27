"""
PatientTriage.ai — Surge Mode Detection & Management Service.

Two surge activation mechanisms:
  A. MANUAL: Medical staff activates surge via the UI with a reason.
  B. AUTO:   System continuously monitors load metrics and recommends surge activation.

Clinical principle: Surge mode changes operational VIEW and alerting only.
  It NEVER reduces clinical urgency scores of individual patients.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Encounter
from backend.app.services.audit_service import log_surge_event

# ─── In-memory surge state (sufficient for prototype) ───
_surge_state = {
    "mode": settings.INITIAL_OPERATING_MODE,   # "NORMAL" | "SURGE"
    "activated_at": None,
    "activated_by": None,
    "reason": None,
}


def get_operating_mode() -> str:
    return _surge_state["mode"]


def get_surge_state() -> Dict[str, Any]:
    return dict(_surge_state)


def activate_surge(
    db: Session,
    *,
    activated_by: str,
    reason: str,
    queue_size: int = 0,
    critical_count: int = 0,
    avg_wait_min: float = 0.0,
    event_type: str = "MANUAL_ACTIVATED",
) -> Dict[str, Any]:
    """Activates surge mode and logs the event."""
    global _surge_state
    _surge_state.update({
        "mode": "SURGE",
        "activated_at": datetime.utcnow(),
        "activated_by": activated_by,
        "reason": reason,
    })
    log_surge_event(
        db,
        event_type    = event_type,
        activated_by  = activated_by,
        reason        = reason,
        queue_size    = queue_size,
        critical_count= critical_count,
        avg_wait_min  = avg_wait_min,
    )
    return get_surge_state()


def deactivate_surge(
    db: Session,
    *,
    deactivated_by: str,
    reason: Optional[str] = None,
    queue_size: int = 0,
) -> Dict[str, Any]:
    """Deactivates surge mode and logs the event."""
    global _surge_state
    _surge_state.update({
        "mode": "NORMAL",
        "activated_at": None,
        "activated_by": None,
        "reason": None,
    })
    log_surge_event(
        db,
        event_type   = "DEACTIVATED",
        activated_by = deactivated_by,
        reason       = reason,
        queue_size   = queue_size,
    )
    return get_surge_state()


def evaluate_surge_conditions(db: Session) -> Dict[str, Any]:
    """
    Continuously evaluates operational indicators to detect surge conditions.
    Returns whether surge is recommended and the reasons.

    Trigger thresholds (configurable):
      - Queue size            > SURGE_QUEUE_THRESHOLD (default: 10)
      - Average wait time     > SURGE_WAIT_THRESHOLD_MIN (default: 40 min)
      - Critical patients     >= SURGE_CRITICAL_THRESHOLD (default: 4)
    """
    waiting_encounters = db.query(Encounter).filter(
        Encounter.status.in_(["WAITING", "UNDER_REVIEW", "ESCALATED"])
    ).all()

    now = datetime.utcnow()
    queue_size = len(waiting_encounters)

    # Count Level 1 (critical) patients
    critical_count = 0
    wait_times = []
    for enc in waiting_encounters:
        # Calculate wait time
        wait_min = int((now - enc.arrival_time).total_seconds() / 60)
        wait_times.append(wait_min)
        # Check if critical
        if enc.triage_results:
            latest = enc.triage_results[0]
            if latest.triage_level == 1:
                critical_count += 1

    avg_wait = round(sum(wait_times) / len(wait_times), 1) if wait_times else 0.0

    surge_reasons: List[str] = []
    if queue_size >= settings.SURGE_QUEUE_THRESHOLD:
        surge_reasons.append(f"Queue size {queue_size} exceeds threshold ({settings.SURGE_QUEUE_THRESHOLD})")
    if avg_wait >= settings.SURGE_WAIT_THRESHOLD_MIN:
        surge_reasons.append(f"Average wait {avg_wait:.0f} min exceeds threshold ({settings.SURGE_WAIT_THRESHOLD_MIN} min)")
    if critical_count >= settings.SURGE_CRITICAL_THRESHOLD:
        surge_reasons.append(f"{critical_count} CRITICAL patients in queue (threshold: {settings.SURGE_CRITICAL_THRESHOLD})")

    surge_recommended = bool(surge_reasons)

    return {
        "queue_size":       queue_size,
        "critical_count":   critical_count,
        "avg_wait_min":     avg_wait,
        "surge_recommended": surge_recommended,
        "surge_reasons":    surge_reasons,
        "operating_mode":   get_operating_mode(),
    }
