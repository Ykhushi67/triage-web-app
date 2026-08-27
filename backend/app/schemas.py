"""
PatientTriage.ai - Pydantic v2 API Schemas.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str

class StaffInfo(BaseModel):
    staff_id: str
    name: str
    email: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: StaffInfo


# ─────────────────────────────────────────────
# Patient & History
# ─────────────────────────────────────────────
class PatientCreate(BaseModel):
    name: str
    age: Optional[float] = None
    gender: Optional[str] = None
    contact_info: Optional[str] = None

class PatientOut(BaseModel):
    patient_id: str
    name: str
    age: Optional[float]
    sex: Optional[str]
    contact_info: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class HistoryVisit(BaseModel):
    encounter_id: str
    visit_date: str
    department: Optional[str]
    chief_complaint: Optional[str]
    triage_level: Optional[int]
    triage_label: Optional[str]
    arrival_mode: str

class PatientHistoryResponse(BaseModel):
    patient_id: str
    patient_name: str
    has_history: bool
    total_visits: int
    visits: List[HistoryVisit]
    is_returning: bool
    # Displayed on UI as badge
    history_badge: str  # e.g. "Returning Patient — 3 Previous Visits" or "First-Time Patient"


# ─────────────────────────────────────────────
# Patient Intake (Full Registration)
# ─────────────────────────────────────────────
class SymptomInput(BaseModel):
    complaint: Optional[str] = None
    onset: Optional[str] = None
    severity: Optional[str] = None
    progression: Optional[str] = None
    free_text: Optional[str] = None

class VitalInput(BaseModel):
    temperature: Optional[float] = None   # °C preferred; system handles °F
    heart_rate: Optional[float] = None
    bp_systolic: Optional[float] = None
    bp_diastolic: Optional[float] = None
    blood_pressure_raw: Optional[str] = None  # Alternative: "120/80" or "140 over 90"
    spo2: Optional[float] = None
    respiratory_rate: Optional[float] = None

class PatientIntakeRequest(BaseModel):
    # Patient fields
    name: str
    age: Optional[float] = None
    gender: Optional[str] = None
    contact_info: Optional[str] = None
    arrival_mode: str = "Walk-in"
    # Symptoms
    symptoms: SymptomInput
    # Current vitals
    vitals: VitalInput
    # For ML inference (concatenated text from symptoms + notes)
    notes: Optional[str] = None

class PatientIntakeResponse(BaseModel):
    encounter_id: str
    patient_id: str
    patient_name: str
    history: PatientHistoryResponse
    triage_result: TriagePredictionResponse
    message: str


# ─────────────────────────────────────────────
# Triage / ML Inference
# ─────────────────────────────────────────────
class TriagePredictionRequest(BaseModel):
    age: Optional[float] = None
    gender: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    temperature: Optional[Any] = None    # Accepts float or string like "37.8C"
    heart_rate: Optional[float] = None
    blood_pressure: Optional[str] = None # "120/80" or "140 over 90"
    spo2: Optional[float] = None

class VitalsNormalized(BaseModel):
    temperature_c: float
    heart_rate: float
    bp_systolic: float
    bp_diastolic: float
    spo2: float
    shock_index: float

class TriagePredictionResponse(BaseModel):
    available: bool
    priority_score: Optional[float]
    triage_level: Optional[int]           # 1 | 2 | 3
    triage_label: Optional[str]           # "Level 1 — CRITICAL (Immediate)"
    triage_color: Optional[str]           # "red" | "yellow" | "green"
    recommended_department: Optional[str]
    department_probabilities: Optional[Dict[str, float]] = {}
    routing_confidence: Optional[float]
    confidence: Optional[float]
    confidence_pct: Optional[int]
    missing_vitals_count: Optional[int] = 0
    uncertainty_flags: List[str] = []
    requires_clinician_review: bool = False
    safety_flags: List[str] = []
    key_factors: List[str] = []
    vitals_normalized: Optional[VitalsNormalized] = None
    model_version: Optional[str] = None
    error: Optional[str] = None


# ─────────────────────────────────────────────
# Clinician Accept / Override
# ─────────────────────────────────────────────
class AcceptTriageRequest(BaseModel):
    encounter_id: str

class OverrideTriageRequest(BaseModel):
    encounter_id: str
    final_triage_level: int = Field(..., ge=1, le=3)   # 1 | 2 | 3
    final_department: Optional[str] = None
    # Structured reason (required for traceability)
    reason_code: str = Field(..., description=(
        "One of: PATIENT_CLINICALLY_WORSE | ADDITIONAL_INFO_AVAILABLE | "
        "AI_UNSUITABLE | LOCAL_CLINICAL_JUDGEMENT | OTHER"
    ))
    reason_free_text: Optional[str] = None

    @field_validator("reason_code")
    @classmethod
    def validate_reason(cls, v):
        valid = {
            "PATIENT_CLINICALLY_WORSE",
            "ADDITIONAL_INFO_AVAILABLE",
            "AI_UNSUITABLE",
            "LOCAL_CLINICAL_JUDGEMENT",
            "OTHER"
        }
        if v not in valid:
            raise ValueError(f"reason_code must be one of {valid}")
        return v


# ─────────────────────────────────────────────
# Reassessment
# ─────────────────────────────────────────────
class ReassessmentRequest(BaseModel):
    encounter_id: str
    vitals: VitalInput
    notes: Optional[str] = None


# ─────────────────────────────────────────────
# Live Queue
# ─────────────────────────────────────────────
class QueuePatient(BaseModel):
    encounter_id: str
    patient_id: str           # Pseudonymous: shown as PID-***** in UI if needed
    patient_name: str
    age: Optional[float]
    sex: Optional[str]
    triage_level: int
    triage_label: str
    triage_color: str
    priority_score: float
    department: Optional[str]
    chief_complaint: Optional[str]
    arrival_mode: str
    waiting_minutes: int
    status: str
    is_overridden: bool
    has_safety_flags: bool
    safety_flags: List[str]
    requires_reassessment: bool
    reassessment_due_in_min: Optional[int]
    is_deteriorating: bool
    confidence_pct: Optional[int]
    history_badge: Optional[str]  # "Returning" or "First-Time"

class QueueSummary(BaseModel):
    total_waiting: int
    critical_count: int       # Level 1
    moderate_count: int       # Level 2
    low_count: int            # Level 3
    overdue_reassessment: int
    avg_wait_min: float
    operating_mode: str

class QueueResponse(BaseModel):
    queue: List[QueuePatient]
    summary: QueueSummary
    operating_mode: str
    surge_recommended: bool
    surge_reason: Optional[str] = None


# ─────────────────────────────────────────────
# Surge Mode
# ─────────────────────────────────────────────
class SurgeActivateRequest(BaseModel):
    reason: str
    reason_detail: Optional[str] = None

class SurgeDeactivateRequest(BaseModel):
    reason: Optional[str] = None

class SurgeStatusResponse(BaseModel):
    operating_mode: str
    is_surge: bool
    surge_since: Optional[datetime]
    queue_size: int
    critical_count: int
    avg_wait_min: float
    surge_reason: Optional[str]
    actions_required: List[Dict[str, Any]] = []


# ─────────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────────
class AuditLogEntry(BaseModel):
    audit_id: int
    timestamp: datetime
    encounter_id: Optional[str]
    patient_id: str
    actor_role: Optional[str]
    action: str
    previous_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    confidence: Optional[float]
    model_version: Optional[str]

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    logs: List[AuditLogEntry]
    total: int
