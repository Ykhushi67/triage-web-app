"""
PatientTriage.ai - SQLAlchemy Database Models.

Schema:
  Hospital → Department → Staff
  Patient  → Encounter  → Symptom / Vital / TriageResult / Override
  AuditLog               (append-only, every AI & clinician action)
  SurgeEvent             (manual + auto-detected surge transitions)

DPDP Design Principles:
  - Patient names stored only in the Patient table (never duplicated in audit logs).
  - Audit logs reference patient_id (pseudonymous, not real name).
  - Staff roles enforced via Role column (ADMIN, DOCTOR, TRIAGE_NURSE).
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey,
    Text, Boolean, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"
    hospital_id = Column(String(50), primary_key=True)
    name        = Column(String(200), nullable=False)
    location    = Column(String(200), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    departments  = relationship("Department", back_populates="hospital")
    staff        = relationship("Staff", back_populates="hospital")
    encounters   = relationship("Encounter", back_populates="hospital")


class Department(Base):
    __tablename__ = "departments"
    department_id = Column(String(50), primary_key=True)
    hospital_id   = Column(String(50), ForeignKey("hospitals.hospital_id"), nullable=True)
    name          = Column(String(100), nullable=False, unique=True)

    hospital    = relationship("Hospital", back_populates="departments")
    encounters  = relationship("Encounter", back_populates="assigned_department")


class Staff(Base):
    __tablename__ = "staff"
    staff_id      = Column(String(50), primary_key=True)
    hospital_id   = Column(String(50), ForeignKey("hospitals.hospital_id"), nullable=True)
    name          = Column(String(150), nullable=False)
    email         = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(50), nullable=False)  # ADMIN | DOCTOR | TRIAGE_NURSE
    created_at    = Column(DateTime, default=datetime.utcnow)

    hospital    = relationship("Hospital", back_populates="staff")
    overrides   = relationship("Override", back_populates="clinician")
    audit_events= relationship("AuditLog", back_populates="actor")


class Patient(Base):
    __tablename__ = "patients"
    patient_id   = Column(String(50), primary_key=True)
    name         = Column(String(150), nullable=False)
    age          = Column(Float, nullable=True)
    sex          = Column(String(20), nullable=True)
    contact_info = Column(String(200), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    encounters = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")


class Encounter(Base):
    __tablename__ = "encounters"
    encounter_id         = Column(String(50), primary_key=True)
    patient_id           = Column(String(50), ForeignKey("patients.patient_id"), nullable=False)
    hospital_id          = Column(String(50), ForeignKey("hospitals.hospital_id"), nullable=True)
    visit_date           = Column(String(20), nullable=False)
    arrival_time         = Column(DateTime, default=datetime.utcnow)
    arrival_mode         = Column(String(50), default="Walk-in")
    # Status: WAITING | UNDER_REVIEW | COMPLETED | ESCALATED | DISCHARGED
    status               = Column(String(50), default="WAITING")
    assigned_department_id = Column(String(50), ForeignKey("departments.department_id"), nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)

    patient              = relationship("Patient", back_populates="encounters")
    hospital             = relationship("Hospital", back_populates="encounters")
    assigned_department  = relationship("Department", back_populates="encounters")
    symptoms             = relationship("Symptom", back_populates="encounter", cascade="all, delete-orphan")
    vitals               = relationship("Vital", back_populates="encounter", cascade="all, delete-orphan",
                                        order_by="Vital.timestamp.desc()")
    triage_results       = relationship("TriageResult", back_populates="encounter", cascade="all, delete-orphan",
                                        order_by="TriageResult.timestamp.desc()")
    overrides            = relationship("Override", back_populates="encounter", cascade="all, delete-orphan",
                                        order_by="Override.timestamp.desc()")
    audit_events         = relationship("AuditLog", back_populates="encounter", cascade="all, delete-orphan")


class Symptom(Base):
    __tablename__ = "symptoms"
    symptom_id   = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(String(50), ForeignKey("encounters.encounter_id"), nullable=False)
    complaint    = Column(String(255), nullable=True)
    onset        = Column(String(100), nullable=True)
    severity     = Column(String(50), nullable=True)
    progression  = Column(String(100), nullable=True)
    free_text    = Column(Text, nullable=True)

    encounter = relationship("Encounter", back_populates="symptoms")


class Vital(Base):
    __tablename__ = "vitals"
    vital_id         = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id     = Column(String(50), ForeignKey("encounters.encounter_id"), nullable=False)
    temperature      = Column(Float, nullable=True)  # Stored in Celsius
    heart_rate       = Column(Float, nullable=True)
    bp_systolic      = Column(Float, nullable=True)
    bp_diastolic     = Column(Float, nullable=True)
    spo2             = Column(Float, nullable=True)
    respiratory_rate = Column(Float, nullable=True)
    timestamp        = Column(DateTime, default=datetime.utcnow)
    recorded_by      = Column(String(50), nullable=True)

    encounter = relationship("Encounter", back_populates="vitals")


class TriageResult(Base):
    __tablename__ = "triage_results"
    result_id            = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id         = Column(String(50), ForeignKey("encounters.encounter_id"), nullable=False)
    priority_score       = Column(Float, nullable=False)
    triage_level         = Column(Integer, nullable=False)   # 1 | 2 | 3
    triage_label         = Column(String(100), nullable=True)
    suggested_department = Column(String(100), nullable=True)
    confidence           = Column(Float, nullable=True)
    confidence_pct       = Column(Integer, nullable=True)
    safety_flags_json    = Column(Text, nullable=True)       # JSON list
    key_factors_json     = Column(Text, nullable=True)       # JSON list
    uncertainty_flags_json = Column(Text, nullable=True)     # JSON list
    requires_review      = Column(Boolean, default=False)
    model_version        = Column(String(50), nullable=True)
    timestamp            = Column(DateTime, default=datetime.utcnow)

    encounter = relationship("Encounter", back_populates="triage_results")


class Override(Base):
    __tablename__ = "overrides"
    override_id         = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id        = Column(String(50), ForeignKey("encounters.encounter_id"), nullable=False)
    clinician_id        = Column(String(50), ForeignKey("staff.staff_id"), nullable=False)
    ai_triage_level     = Column(Integer, nullable=False)       # What AI recommended
    ai_priority_score   = Column(Float, nullable=False)
    final_triage_level  = Column(Integer, nullable=False)       # What clinician decided
    final_priority_score= Column(Float, nullable=False)
    final_department    = Column(String(100), nullable=True)
    # Structured override reasons
    reason_code         = Column(String(100), nullable=False)
    reason_free_text    = Column(Text, nullable=True)
    timestamp           = Column(DateTime, default=datetime.utcnow)

    encounter = relationship("Encounter", back_populates="overrides")
    clinician = relationship("Staff", back_populates="overrides")


class AuditLog(Base):
    """
    Append-only immutable event log.
    Every AI recommendation, clinician action, vital recheck, and surge event is recorded here.
    Uses patient_id (pseudonymous) — never stores patient name directly.
    """
    __tablename__ = "audit_logs"

    audit_id      = Column(Integer, primary_key=True, autoincrement=True)
    timestamp     = Column(DateTime, default=datetime.utcnow, nullable=False)
    encounter_id  = Column(String(50), ForeignKey("encounters.encounter_id"), nullable=True)
    patient_id    = Column(String(50), nullable=False)  # Pseudonymous reference
    actor_id      = Column(String(50), ForeignKey("staff.staff_id"), nullable=True)
    actor_role    = Column(String(50), nullable=True)   # SYSTEM | DOCTOR | TRIAGE_NURSE | ADMIN
    # Action types: AI_TRIAGE_GENERATED | CLINICIAN_ACCEPTED | CLINICIAN_OVERRIDDEN |
    #               VITALS_REASSESSED | DETERIORATION_FLAGGED |
    #               SURGE_AUTO_DETECTED | SURGE_MANUAL_ACTIVATED | SURGE_DEACTIVATED |
    #               PATIENT_REGISTERED | PATIENT_COMPLETED
    action        = Column(String(100), nullable=False)
    previous_value= Column(Text, nullable=True)   # e.g. "Level 2, Score 5.4"
    new_value     = Column(Text, nullable=True)   # e.g. "Level 1, Score 7.8"
    reason        = Column(Text, nullable=True)   # Override/activation reason
    confidence    = Column(Float, nullable=True)  # AI confidence at time of event
    model_version = Column(String(50), nullable=True)
    metadata_json = Column(Text, nullable=True)   # Raw vital snapshot, delta flags etc.

    encounter = relationship("Encounter", back_populates="audit_events")
    actor     = relationship("Staff", back_populates="audit_events")

    __table_args__ = (
        Index("ix_audit_patient", "patient_id"),
        Index("ix_audit_encounter", "encounter_id"),
        Index("ix_audit_timestamp", "timestamp"),
    )


class SurgeEvent(Base):
    """Logs every surge mode activation and deactivation."""
    __tablename__ = "surge_events"

    surge_id       = Column(Integer, primary_key=True, autoincrement=True)
    timestamp      = Column(DateTime, default=datetime.utcnow)
    event_type     = Column(String(50), nullable=False)   # AUTO_DETECTED | MANUAL_ACTIVATED | DEACTIVATED
    activated_by   = Column(String(50), nullable=True)    # staff_id or "SYSTEM"
    reason         = Column(Text, nullable=True)
    queue_size     = Column(Integer, nullable=True)
    critical_count = Column(Integer, nullable=True)
    avg_wait_min   = Column(Float, nullable=True)
    arrival_rate   = Column(Float, nullable=True)
