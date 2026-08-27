# PatientTriage.ai — Emergency Department AI Triage & Clinical Decision Support System

> **A Safety-First, Human-in-the-Loop Clinical Decision Support System**  
> Designed for Emergency Departments, with explicit uncertainty scoring, physiological risk stratification, real-time vital deterioration tracking, and DPDP Act 2023 regulatory compliance baselines.

---

## Table of Contents

- [1. Project Name & Introduction](#1-project-name--introduction)
- [2. System Architecture & Core Philosophy](#2-system-architecture--core-philosophy)
- [3. Requirements](#3-requirements)
- [4. Recommended Modules & Technology Stack](#4-recommended-modules--technology-stack)
- [5. Installation](#5-installation)
- [6. Configuration](#6-configuration)
- [7. Demonstration Scenarios & Judge Quick-Start](#7-demonstration-scenarios--judge-quick-start)
- [8. Troubleshooting & FAQ](#8-troubleshooting--faq)
- [9. Maintainers & Governance](#9-maintainers--governance)

---

## 1. Project Name & Introduction

**PatientTriage.ai** is an emergency department clinical decision-support application built to tackle overcrowding, patient waiting bottlenecks, and sudden deterioration risks during simultaneous multi-patient arrivals.

### The Problem
During peak hours and emergency surges, clinical staff must rapidly identify:
- Which patients require immediate resuscitation?
- Who is at risk of silent physiological collapse or hypoxia?
- What does the machine learning model suggest, and **why**?
- How much confidence does the system have in the recommendation?
- How does the system safely handle clinician disagreement?

### The Solution & Core Principle
```
AI Recommends ➔ Clinician Reviews ➔ Clinician Decides ➔ System Monitors ➔ System Alerts ➔ Immutable Log
```
PatientTriage.ai **does not replace doctors or nurses**. It serves as an assistive copilot that evaluates current acute vital signs, applies hard clinical safety floors (such as hypoxemia and haemodynamic shock indices), and continuously monitors queue stability.

---

## 2. System Architecture & Core Philosophy

### Zero-Bias History Isolation Principle
- **History Lookup:** Retrieved independently for clinician awareness only (`[RETURNING PATIENT]` vs. `[FIRST-TIME PATIENT]`).
- **ML Inference:** Consumes **strictly acute vital signs and current presentation**. Historical records are physically isolated from the feature matrix to eliminate diagnostic bias.

### Safety Rule Hard Floors
- **SpO₂ Hypoxemia Floor:** Any patient with $\text{SpO}_2 < 90\%$ is forced into **Level 1 Critical** ($\text{Score} \ge 8.5$) with mandatory emergency escalation regardless of raw ML model scores.
- **Haemodynamic Shock Floor:** $\text{Shock Index} = \frac{\text{Heart Rate}}{\text{Systolic BP}} \ge 1.0$ triggers immediate **Level 1 Critical** ($\text{Score} \ge 7.5$).

### Explicit Uncertainty Engine
- Missing vitals decrease confidence by **-8% per missing parameter**.
- Confidence $< 72\%$ or $\ge 3$ missing vitals flags a visible **"High Uncertainty — Clinician Review Required"** alert.

---

## 3. Requirements

### System & Environment
- **Operating System:** Windows 10/11, macOS (12+), or Ubuntu (20.04+)
- **Python:** Python 3.10 to 3.14 (64-bit)
- **Node.js:** Node.js v18.0.0+ and npm 9.0.0+
- **Memory:** 4 GB RAM minimum (8 GB recommended)
- **Disk Space:** 500 MB free space

---

## 4. Recommended Modules & Technology Stack

### Backend Stack
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (High-performance async REST API)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
- **Machine Learning:** [XGBoost](https://xgboost.readthedocs.io/), [Scikit-Learn](https://scikit-learn.org/), [NumPy](https://numpy.org/), [Pandas](https://pandas.pydata.org/)
- **Database & ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (SQLite zero-configuration default; PostgreSQL production-ready)
- **Authentication & Security:** JWT (via `python-jose`) and password hashing (via `passlib` & `bcrypt`)
- **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/)

### Frontend Stack
- **UI Framework:** [React 18](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Routing:** [React Router v6](https://reactrouter.com/)
- **Design System:** Vanilla CSS with custom clinical tokens and [Google Fonts Roboto](https://fonts.google.com/specimen/Roboto)
- **Icons:** [Lucide React](https://lucide.dev/)
- **HTTP Client:** [Axios](https://axios-http.com/)

---

## 5. Installation

### Step 1: Open the `triage-web-app` Directory
```bash
cd triage-web-app
```

### Step 2: Set Up Python Backend Dependencies
```bash
# Install required Python packages
python -m pip install -r backend/requirements.txt
```

### Step 3: Train Models & Seed Database
```bash
# Train ML XGBoost regressor & department classifier on clinical presentation dataset
python -m ml.train_models

# Seed the hospital database with the 22 canonical clinical scenarios
python -m backend.seed
```

### Step 4: Install Frontend Node Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 5: Start the Development Servers

#### Terminal 1 — Start the FastAPI Backend Server (Port 8000):
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2 — Start the React/Vite Frontend Server (Port 5173):
```bash
cd frontend
npm run dev
```

Open your browser and visit: **`http://localhost:5173`**

---

## 6. Configuration

Environment variables can be customized in a `.env` file in `triage-web-app/` or via standard system environment variables:

| Variable | Default Value | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./patient_triage.db` | Database connection string (SQLite or PostgreSQL) |
| `SECRET_KEY` | `patient-triage-ai-hackathon-secret-key-2026` | JWT signature key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 hours) | Session authentication duration |
| `CONFIDENCE_REVIEW_THRESHOLD` | `0.72` (72%) | Confidence threshold below which clinician review is mandatory |
| `INITIAL_OPERATING_MODE` | `NORMAL` | Initial emergency department operating mode (`NORMAL` / `SURGE`) |
| `SURGE_QUEUE_THRESHOLD` | `10` | Waiting patients count that triggers auto-surge advisory |
| `SURGE_WAIT_THRESHOLD_MIN` | `40` | Average wait time (minutes) that triggers auto-surge advisory |
| `SURGE_CRITICAL_THRESHOLD` | `4` | Count of Level 1 Critical cases that triggers auto-surge advisory |
| `REASSESS_CRITICAL_MIN` | `15` | Level 1 Critical vital signs reassessment interval (minutes) |
| `REASSESS_MODERATE_MIN` | `30` | Level 2 Moderate vital signs reassessment interval (minutes) |
| `REASSESS_LOW_MIN` | `60` | Level 3 Low vital signs reassessment interval (minutes) |

---

## 7. Demonstration Scenarios & Judge Quick-Start

### Pre-Configured Demo Credentials

| Role | Email | Password | Allowed Clinical Capabilities |
|---|---|---|---|
| **Doctor** | `doctor@hospital.org` | `doctor123` | Full clinical override, triage acceptance, reassessments, discharge, surge control |
| **Triage Nurse** | `nurse@hospital.org` | `nurse123` | Patient intake, recording vitals, triggering ML triage, surge control |
| **Admin** | `admin@hospital.org` | `admin123` | Governance, surge mode management |

### 60-Second Demo Walkthrough
1. **Explore Live Priority Queue (`/queue`):**
   - Use the **Department Filter Dropdown** (`Cardiology`, `Pulmonology`, `Emergency`, `General Medicine`, etc.) to filter patients by specific specialty wards.
   - Use the **Priority Tabs** (`Critical Level 1`, `Moderate Level 2`, `Low Level 3`, `Deteriorating`, `Reassessment Due`).
2. **Test Returning Patient Zero-Bias Lookup (`/new-patient`):**
   - Enter Patient ID `P0011` (Ramesh Sharma) ➔ Step 2 displays prior hospital encounter records.
3. **Test Hard Safety Floor (`/new-patient`):**
   - Enter $\text{SpO}_2 = 88\%$ ➔ System enforces mandatory Level 1 Critical escalation.
4. **Test Clinician Override:**
   - Click *Override Recommendation* ➔ Select final urgency with structured clinical reason code (`PATIENT_CLINICALLY_WORSE`).
5. **Test Deterioration Alert:**
   - On the top toolbar, click **`⚠ Deterioration Alert`** ➔ Simulates acute SpO₂ desaturation with automatic visual alert.
6. **Test Surge Mode & One-Click Return:**
   - Click **`🚨 3× Surge Wave`** ➔ Simulates sudden ambulance influx.
   - Click **`✓ Return to Normal Mode`** or **`🔄 Reset 22 Cases`** to return to normal baseline.

---

## 8. Troubleshooting & FAQ

### Q: Why is my browser unable to connect to the backend?
**A:** Ensure Uvicorn is running on port 8000 (`python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`). The Vite frontend proxy redirects all `/api` calls directly to `http://localhost:8000`.

### Q: Why do I see a 401 Unauthorized error?
**A:** Click the quick login button on the `/login` page or log in with `doctor@hospital.org` / `doctor123`.

### Q: How do I reset the demo data if I make changes?
**A:** Click the **`🔄 Reset 22 Cases (Normal Mode)`** button in the dashboard toolbar or execute:
```bash
python -m backend.seed
```

---

## 9. Maintainers & Governance

- **Lead Developer & System Architect:** PatientTriage.ai Team
- **Clinical Governance:** Designed according to Emergency Severity Index (ESI) principles and Indian DPDP Act 2023 privacy guidelines.
- **License:** Open Prototype / Hackathon Evaluation License.

---

*PatientTriage.ai is an assistive clinical decision-support tool. All triage suggestions require validation by qualified medical professionals.*
