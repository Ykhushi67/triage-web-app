"""
PatientTriage.ai — FastAPI Application Entrypoint.

Safety-first clinical decision-support and emergency department triage system.
Compliant with Digital Personal Data Protection (DPDP) Act 2023 design principles.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import init_db, SessionLocal
from backend.app.api import auth, patients, triage, queue, surge, audit, analytics, demo
from backend.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 60)
    print("Starting PatientTriage.ai Clinical Backend...")
    print("=" * 60)
    init_db()
    db = SessionLocal()
    try:
        from backend.app.models import Staff
        if not db.query(Staff).first():
            print("Initial hospital database empty. Seeding demo clinical scenarios...")
            seed_database(db)
        else:
            print("Hospital database ready.")
    finally:
        db.close()
    yield
    print("Shutting down PatientTriage.ai Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    ## PatientTriage.ai — Safety-First Emergency Department Triage Decision Support System
    
    * **ML Priority Regressor & 3-Tier Classification** (Level 1 Critical / Level 2 Moderate / Level 3 Low)
    * **Explicit Uncertainty & Confidence Engine** (Penalizes missing critical vitals)
    * **Independent Patient History Lookup** (Never fed to ML model to prevent bias)
    * **Dynamic Queue Prioritization & Continuous Deterioration Tracking**
    * **Normal vs. Surge Operational Modes** (Auto-detection at 3× arrival rate)
    * **Clinician Accept / Override Workflow** (Mandatory structured reason logging)
    * **Persistent Append-Only Audit Trail** (DPDP 2023 aligned)
    """,
    lifespan=lifespan,
)

# CORS Middleware (supports local React / Vite frontend development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(triage.router, prefix="/api")
app.include_router(queue.router, prefix="/api")
app.include_router(surge.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(demo.router, prefix="/api")


@app.get("/")
def root():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "operating_mode": "DECISION_SUPPORT_SYSTEM",
        "triage_system": "3-Tier (Level 1 Critical, Level 2 Moderate, Level 3 Low)",
        "regulatory_alignment": "Digital Personal Data Protection (DPDP) Act 2023 design baseline",
        "documentation": "/docs",
    }
