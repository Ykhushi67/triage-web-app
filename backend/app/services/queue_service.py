"""
PatientTriage.ai — Live Queue Management & Deterioration Detection Service.

Responsibilities:
  1. Build live ED queue sorted by triage priority (Level 1 first, then elapsed wait).
  2. Track reassessment deadlines per triage level.
  3. Detect multi-vital deterioration between sequential vital recordings.
  4. Surface "Reassessment Overdue" and "Deteriorating" flags in the queue.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models import Encounter, Vital, TriageResult, Override
from backend.app.schemas import QueuePatient, QueueResponse, QueueSummary
from backend.app.config import settings
from backend.app.services.surge_service import get_operating_mode, evaluate_surge_conditions

# Reassessment intervals by triage level
REASSESSMENT_INTERVALS = {
    1: settings.REASSESS_CRITICAL_MIN,   # 15 min
    2: settings.REASSESS_MODERATE_MIN,   # 30 min
    3: settings.REASSESS_LOW_MIN,        # 60 min
}


def check_deterioration(vitals: List[Vital]) -> bool:
    """
    Compares latest two vital recordings to detect acute clinical deterioration.

    Criteria (any one triggers):
      - SpO2 drops >= 4% between readings OR crosses below 90%
      - Heart rate spikes >= 25 bpm between readings OR exceeds 130 bpm
      - Systolic BP drops >= 25 mmHg between readings OR crosses below 90 mmHg
    """
    if len(vitals) < 2:
        return False

    latest   = vitals[0]  # Ordered DESC, so index 0 = newest
    previous = vitals[1]

    # SpO2 deterioration
    if latest.spo2 and previous.spo2:
        if (previous.spo2 - latest.spo2) >= 4.0:
            return True
        if latest.spo2 < 90.0 and previous.spo2 >= 90.0:
            return True

    # HR deterioration
    if latest.heart_rate and previous.heart_rate:
        if (latest.heart_rate - previous.heart_rate) >= 25.0:
            return True
        if latest.heart_rate > 130.0 and previous.heart_rate <= 130.0:
            return True

    # BP deterioration
    if latest.bp_systolic and previous.bp_systolic:
        if (previous.bp_systolic - latest.bp_systolic) >= 25.0:
            return True
        if latest.bp_systolic < 90.0 and previous.bp_systolic >= 90.0:
            return True

    return False


def build_queue(db: Session) -> QueueResponse:
    """
    Builds the live ED queue with full triage, wait-time, and deterioration information.
    Sorted by: triage_level ASC, then priority_score DESC, then arrival_time ASC.
    """
    active_encounters = db.query(Encounter).filter(
        Encounter.status.in_(["WAITING", "UNDER_REVIEW", "ESCALATED"])
    ).all()

    now = datetime.utcnow()
    queue_items: List[QueuePatient] = []

    critical_count = moderate_count = low_count = 0
    overdue_count  = 0
    wait_times: List[float] = []

    for enc in active_encounters:
        patient = enc.patient

        # Effective triage (override takes priority over AI result)
        latest_override = enc.overrides[0] if enc.overrides else None
        latest_triage   = enc.triage_results[0] if enc.triage_results else None

        if latest_override:
            t_level = latest_override.final_triage_level
            score   = latest_override.final_priority_score
            dept    = latest_override.final_department
            is_overridden = True
        elif latest_triage:
            t_level = latest_triage.triage_level
            score   = latest_triage.priority_score
            dept    = latest_triage.suggested_department
            is_overridden = False
        else:
            # Untriaged patient — assign holding values
            t_level = 2  # Treat as moderate pending assessment
            score   = 4.0
            dept    = "General Medicine"
            is_overridden = False

        # Triage label & color
        level_labels = {1: "Level 1 — CRITICAL", 2: "Level 2 — MODERATE", 3: "Level 3 — LOW"}
        level_colors = {1: "red", 2: "yellow", 3: "green"}
        t_label = level_labels.get(t_level, "Unknown")
        t_color = level_colors.get(t_level, "gray")

        # Wait time
        wait_min = int((now - enc.arrival_time).total_seconds() / 60)
        wait_times.append(float(wait_min))

        # Reassessment tracking
        reassess_interval = REASSESSMENT_INTERVALS.get(t_level, 60)
        last_vital_time   = enc.vitals[0].timestamp if enc.vitals else enc.arrival_time
        time_since_last   = int((now - last_vital_time).total_seconds() / 60)
        due_in_min        = max(0, reassess_interval - time_since_last)
        needs_reassess    = (time_since_last >= reassess_interval)

        if needs_reassess:
            overdue_count += 1

        # Deterioration check
        is_deteriorating = check_deterioration(enc.vitals)

        # Safety flags
        safety_flags: List[str] = []
        has_flags = False
        if latest_triage and latest_triage.safety_flags_json:
            try:
                safety_flags = json.loads(latest_triage.safety_flags_json)
                has_flags = bool(safety_flags)
            except Exception:
                pass

        # Confidence
        conf_pct = latest_triage.confidence_pct if latest_triage else None

        # History badge (quick lookup: returning vs first-time)
        prior_count = db.query(Encounter).filter(
            Encounter.patient_id == enc.patient_id,
            Encounter.encounter_id != enc.encounter_id,
            Encounter.status == "COMPLETED",
        ).count()
        history_badge = (
            f"🔵 Returning ({prior_count} prior)" if prior_count > 0
            else "🟢 First-Time"
        )

        # Chief complaint
        symptom = enc.symptoms[0] if enc.symptoms else None
        complaint = symptom.complaint if symptom else None

        # Count by level
        if t_level == 1:
            critical_count += 1
        elif t_level == 2:
            moderate_count += 1
        else:
            low_count += 1

        queue_items.append(QueuePatient(
            encounter_id         = enc.encounter_id,
            patient_id           = enc.patient_id,
            patient_name         = patient.name,
            age                  = patient.age,
            sex                  = patient.sex,
            triage_level         = t_level,
            triage_label         = t_label,
            triage_color         = t_color,
            priority_score       = round(score, 1),
            department           = dept,
            chief_complaint      = complaint,
            arrival_mode         = enc.arrival_mode,
            waiting_minutes      = wait_min,
            status               = enc.status,
            is_overridden        = is_overridden,
            has_safety_flags     = has_flags,
            safety_flags         = safety_flags,
            requires_reassessment= needs_reassess,
            reassessment_due_in_min = due_in_min,
            is_deteriorating     = is_deteriorating,
            confidence_pct       = conf_pct,
            history_badge        = history_badge,
        ))

    # Sort: Level ASC, Score DESC, Wait DESC
    queue_items.sort(key=lambda p: (p.triage_level, -p.priority_score, -p.waiting_minutes))

    avg_wait = round(sum(wait_times) / len(wait_times), 1) if wait_times else 0.0
    mode = get_operating_mode()

    # Surge recommendation check
    surge_eval = evaluate_surge_conditions(db)

    summary = QueueSummary(
        total_waiting       = len(queue_items),
        critical_count      = critical_count,
        moderate_count      = moderate_count,
        low_count           = low_count,
        overdue_reassessment= overdue_count,
        avg_wait_min        = avg_wait,
        operating_mode      = mode,
    )

    return QueueResponse(
        queue              = queue_items,
        summary            = summary,
        operating_mode     = mode,
        surge_recommended  = surge_eval["surge_recommended"],
        surge_reason       = "; ".join(surge_eval["surge_reasons"]) if surge_eval["surge_reasons"] else None,
    )
