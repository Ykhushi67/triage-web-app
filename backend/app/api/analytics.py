"""PatientTriage.ai — Analytics & Model Telemetry API"""

import os
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models import Staff, Encounter, Override, TriageResult, AuditLog
from backend.app.config import settings

router = APIRouter(prefix="/analytics", tags=["Analytics & Model Telemetry"])


@router.get("/overview")
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user),
):
    """Returns clinical governance, triage distributions, and model performance metrics."""
    total_encounters = db.query(Encounter).count()
    total_overrides = db.query(Override).count()
    total_ai_predictions = db.query(TriageResult).count()
    override_rate = round((total_overrides / max(1, total_ai_predictions)) * 100, 1)

    # 3-tier distribution
    tier_counts = {1: 0, 2: 0, 3: 0}
    for tr in db.query(TriageResult).all():
        if tr.triage_level in tier_counts:
            tier_counts[tr.triage_level] += 1

    # Override reasons breakdown
    override_reasons = {}
    for ov in db.query(Override).all():
        override_reasons[ov.reason_code] = override_reasons.get(ov.reason_code, 0) + 1

    # Load ML evaluation metadata
    reg_meta = {}
    clf_meta = {}
    reg_meta_path = os.path.join(settings.MODELS_DIR, "regression_metadata.json")
    clf_meta_path = os.path.join(settings.MODELS_DIR, "classification_metadata.json")
    
    if os.path.exists(reg_meta_path):
        with open(reg_meta_path) as f:
            reg_meta = json.load(f)
    if os.path.exists(clf_meta_path):
        with open(clf_meta_path) as f:
            clf_meta = json.load(f)

    return {
        "hospital_metrics": {
            "total_encounters": total_encounters,
            "total_ai_predictions": total_ai_predictions,
            "total_overrides": total_overrides,
            "override_rate_pct": override_rate,
            "triage_distribution": {
                "Level 1 (Critical)": tier_counts[1],
                "Level 2 (Moderate)": tier_counts[2],
                "Level 3 (Low)": tier_counts[3],
            },
            "override_reasons": override_reasons,
        },
        "model_telemetry": {
            "regressor": reg_meta,
            "classifier": clf_meta,
            "safety_framework": "Enforced (SpO2 < 90%, Shock Index >= 1.0, BP sys < 90)",
            "uncertainty_scoring": "Active (Penalizes missing vitals & ambiguous text)",
            "compliance_standard": "Digital Personal Data Protection (DPDP) Act 2023 design baseline",
        }
    }
