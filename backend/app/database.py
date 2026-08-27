"""
PatientTriage.ai - Database Engine & Session Configuration.

Tables:
  - Normalized relational schema (Hospital, Patient, Encounter, Vital, Symptom, TriageResult, Override)
  - audit_logs        : Append-only event log (AI predictions, clinician actions, surge events)
  - surge_events      : Manual and auto-detected surge log
  - ml_training_export: SQL view for future model retraining (excludes PII identifiers)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Creates all tables and SQL views."""
    from backend.app import models  # noqa: F401 — registers all models
    Base.metadata.create_all(bind=engine)
    _create_views()


def _create_views():
    """Creates the ml_training_export SQL view (excludes PII / identifiers)."""
    view_sql = """
    CREATE VIEW IF NOT EXISTS ml_training_export AS
    SELECT
        p.age                    AS age,
        p.sex                    AS gender,
        s.complaint              AS symptoms,
        s.free_text              AS notes,
        v.temperature            AS temperature,
        v.heart_rate             AS heart_rate,
        (CAST(v.bp_systolic AS TEXT) || '/' || CAST(v.bp_diastolic AS TEXT)) AS blood_pressure,
        v.spo2                   AS spo2,
        d.name                   AS department,
        CASE
            WHEN tr.priority_score >= 7.0 THEN 'High'
            WHEN tr.priority_score >= 4.0 THEN 'Medium'
            ELSE 'Low'
        END AS urgency_level
    FROM encounters e
    JOIN patients p      ON e.patient_id = p.patient_id
    LEFT JOIN symptoms s ON s.encounter_id = e.encounter_id
    LEFT JOIN departments d ON d.department_id = e.assigned_department_id
    LEFT JOIN (
        SELECT v1.* FROM vitals v1
        INNER JOIN (
            SELECT encounter_id, MAX(timestamp) as mx FROM vitals GROUP BY encounter_id
        ) v2 ON v1.encounter_id = v2.encounter_id AND v1.timestamp = v2.mx
    ) v ON v.encounter_id = e.encounter_id
    LEFT JOIN (
        SELECT tr1.* FROM triage_results tr1
        INNER JOIN (
            SELECT encounter_id, MAX(timestamp) as mx FROM triage_results GROUP BY encounter_id
        ) tr2 ON tr1.encounter_id = tr2.encounter_id AND tr1.timestamp = tr2.mx
    ) tr ON tr.encounter_id = e.encounter_id;
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(view_sql))
            conn.commit()
    except Exception as e:
        print(f"Note (view creation): {e}")
