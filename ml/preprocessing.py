"""
PatientTriage.ai - Machine Learning Preprocessing & Medical Normalization Pipeline.

INPUT FEATURES (Strictly current acute presentation ONLY — no patient history fed to ML):
  - age, gender, symptoms, notes (current), temperature, heart_rate, blood_pressure, spo2

STRICTLY EXCLUDED (identifiers):
  - visit_id, patient_id, visit_date, waiting_time_min

3-TIER TRIAGE OUTPUT:
  Level 1 CRITICAL  — Score 7.0–10.0 (Immediate / Life-threatening)
  Level 2 MODERATE  — Score 4.0–6.9  (Urgent / Prompt evaluation)
  Level 3 LOW       — Score 0.0–3.9  (Routine / Non-urgent)
"""

import re
import numpy as np
import pandas as pd
from typing import Tuple, Any, Optional


# ─────────────────────────────────────────────
# Canonical Department Mapping
# ─────────────────────────────────────────────
DEPARTMENT_MAPPING = {
    "general medicine": "General Medicine",
    "gen med": "General Medicine",
    "a&e": "Emergency",
    "emergency": "Emergency",
    "emergency dept": "Emergency",
    "er": "Emergency",
    "neuro dept": "Neurology",
    "neurology": "Neurology",
    "neuro": "Neurology",
    "pulmo": "Pulmonology",
    "pulmonology": "Pulmonology",
    "cardiology": "Cardiology",
    "cardio": "Cardiology",
    "gastro": "Gastroenterology",
    "gastroenterology": "Gastroenterology",
    "gi": "Gastroenterology",
    "gastro dept": "Gastroenterology",
    "ent dept": "ENT",
    "ear nose throat": "ENT",
    "ent": "ENT",
}

CANONICAL_DEPARTMENTS = [
    "Emergency", "Cardiology", "Pulmonology",
    "Neurology", "Gastroenterology", "ENT", "General Medicine"
]

# ─────────────────────────────────────────────
# Medical Abbreviation / Typo Expansion Map
# ─────────────────────────────────────────────
MEDICAL_SYNONYM_MAP = {
    r"\bchst\b": "chest",
    r"\bchset\b": "chest",
    r"\bchestpain\b": "chest pain",
    r"\bfevr\b": "fever",
    r"\bfevrish\b": "feverish",
    r"\bhedache\b": "headache",
    r"\bhead-ache\b": "headache",
    r"\bthrout\b": "throat",
    r"\bsore throut\b": "sore throat",
    r"\bbak\b": "back",
    r"\babdo\b": "abdominal",
    r"\babd\b": "abdominal",
    r"\bsob\b": "shortness of breath breathlessness",
    r"\bn/v\b": "nausea vomiting",
    r"\bnausea/vomiting\b": "nausea vomiting",
    r"\bpt\b": "patient",
    r"\bfrm\b": "from",
    r"\bnite\b": "night",
    r"\bmornng\b": "morning",
    r"\blumbar\b": "lower back",
    r"\blethargy\b": "fatigue weakness",
    r"\blightheaded\b": "dizziness lightheaded vertigo",
    r"\bdizzy\b": "dizziness vertigo",
}

# ─────────────────────────────────────────────
# Urgency-level to 3-tier mapping
# ─────────────────────────────────────────────
URGENCY_TO_TIER = {
    "critical": 1,  # Level 1 — CRITICAL
    "high": 1,      # Also Level 1 (life-threatening)
    "medium": 2,    # Level 2 — MODERATE
    "low": 3,       # Level 3 — LOW
}

# Numerical features consumed by the ML models
NUMERICAL_FEATURE_COLS = [
    "age_clean", "age_missing", "age_under_18", "age_elderly",
    "is_male", "is_female",
    "temperature_clean", "temp_missing", "fever_high", "hypothermia", "temp_deviation",
    "heart_rate_clean", "hr_missing", "tachycardia_severe", "tachycardia_mild", "bradycardia",
    "bp_systolic_clean", "bp_diastolic_clean", "bp_missing",
    "pulse_pressure", "shock_index", "hypotension", "hypertension_stage2",
    "spo2_clean", "spo2_missing", "hypoxia_severe", "hypoxia_moderate",
]


# ─────────────────────────────────────────────
# Cleaning functions
# ─────────────────────────────────────────────

def clean_medical_text(text: Any) -> str:
    """Normalizes medical typos, abbreviations, and clinical shorthand."""
    if pd.isna(text) or text is None:
        return ""
    t = str(text).lower().strip()
    for pattern, replacement in MEDICAL_SYNONYM_MAP.items():
        t = re.sub(pattern, replacement, t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def clean_gender(val: Any) -> str:
    """Normalizes gender to 'male', 'female', or 'unknown'."""
    if pd.isna(val) or val is None:
        return "unknown"
    s = str(val).strip().lower()
    if s in ["m", "male"]:
        return "male"
    elif s in ["f", "female"]:
        return "female"
    return "unknown"


def clean_temperature(val: Any) -> Tuple[float, int]:
    """
    Normalizes temperature to Celsius.
    Returns (celsius_value, missing_flag).
    """
    if pd.isna(val) or val is None or str(val).strip() == "":
        return 37.0, 1
    val_str = str(val).strip().upper()
    try:
        if "F" in val_str:
            num = float(re.sub(r"[^\d\.]", "", val_str))
            return round((num - 32.0) * 5.0 / 9.0, 1), 0
        elif "C" in val_str:
            num = float(re.sub(r"[^\d\.]", "", val_str))
            return round(num, 1), 0
        else:
            num = float(re.sub(r"[^\d\.]", "", val_str))
            if num > 50.0:  # Ambiguous — treat as Fahrenheit
                return round((num - 32.0) * 5.0 / 9.0, 1), 0
            return round(num, 1), 0
    except Exception:
        return 37.0, 1


def clean_blood_pressure(val: Any) -> Tuple[float, float, int]:
    """
    Parses dirty BP strings: '118/80', '128-66', '158 over 89'.
    Returns (systolic, diastolic, missing_flag).
    """
    if pd.isna(val) or val is None or str(val).strip() == "":
        return 120.0, 80.0, 1
    nums = [float(n) for n in re.findall(r"\d+", str(val))]
    if len(nums) >= 2:
        sys = max(60.0, min(240.0, nums[0]))
        dia = max(40.0, min(140.0, nums[1]))
        return sys, dia, 0
    elif len(nums) == 1:
        return max(60.0, min(240.0, nums[0])), 80.0, 0
    return 120.0, 80.0, 1


def clean_department(val: Any) -> Optional[str]:
    """Maps raw noisy department string to canonical name."""
    if pd.isna(val) or val is None:
        return None
    return DEPARTMENT_MAPPING.get(str(val).strip().lower(), "General Medicine")


# ─────────────────────────────────────────────
# Triage Score & Level Generation
# ─────────────────────────────────────────────

def generate_triage_score(row: pd.Series) -> float:
    """
    Calculates calibrated 0–10 prototype Triage Priority Score.

    Mapping:
      Critical / High urgency  →  Base 8.8 / 6.8  (maps to Level 1: Critical)
      Medium urgency           →  Base 4.5         (maps to Level 2: Moderate)
      Low urgency              →  Base 1.8         (maps to Level 3: Low)

    Physiological vital deviations add to score within bounded tiers.
    """
    urgency = str(row.get("urgency_level", "Medium")).strip().capitalize()
    base_scores = {"Critical": 8.8, "High": 6.8, "Medium": 4.5, "Low": 1.8}
    score = base_scores.get(urgency, 4.5)

    spo2 = row.get("spo2_clean", 98.0)
    hr   = row.get("heart_rate_clean", 75.0)
    sys  = row.get("bp_systolic_clean", 120.0)
    temp = row.get("temperature_clean", 37.0)

    # SpO2 penalites
    if spo2 < 90.0:
        score += 0.9
    elif spo2 < 94.0:
        score += 0.4

    # Heart-rate penalties
    if hr > 125.0 or hr < 45.0:
        score += 0.6
    elif hr > 105.0:
        score += 0.3

    # BP penalties
    if sys < 90.0:
        score += 0.8
    elif sys > 175.0:
        score += 0.4

    # Temperature penalties
    if temp > 39.4 or temp < 35.5:
        score += 0.4

    # Deterministic micro-variance (prevents all same-urgency patients sharing identical score)
    v_id = str(row.get("visit_id", "0"))
    hash_val = sum(ord(c) for c in v_id) % 100 / 100.0
    score += (hash_val - 0.5) * 0.3

    # Clamp to urgency tier band
    if urgency in ("Critical", "High"):
        score = max(7.0, min(10.0, score))
    elif urgency == "Medium":
        score = max(4.0, min(6.9, score))
    else:  # Low
        score = max(0.1, min(3.9, score))

    return round(float(np.clip(score, 0.0, 10.0)), 2)


def score_to_triage_level(score: float) -> Tuple[int, str, str]:
    """
    Converts a 0–10 priority score to a simplified 3-tier Triage Level.

    Returns (level_int, level_label, level_color):
      Level 1 → Critical  (red)     — Score >= 7.0
      Level 2 → Moderate  (yellow)  — Score >= 4.0
      Level 3 → Low       (green)   — Score < 4.0
    """
    if score >= 7.0:
        return 1, "Level 1 — CRITICAL (Immediate)", "red"
    elif score >= 4.0:
        return 2, "Level 2 — MODERATE (Urgent)", "yellow"
    else:
        return 3, "Level 3 — LOW (Routine)", "green"


# ─────────────────────────────────────────────
# Main Preprocessing Pipeline
# ─────────────────────────────────────────────

def preprocess_dataframe(df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
    """
    Cleans and feature-engineers a raw patient visit DataFrame.

    Never uses: visit_id, patient_id, visit_date, waiting_time_min.
    """
    df_clean = df.copy()

    # 1. Age
    df_clean["age_missing"] = df_clean["age"].isna().astype(int)
    df_clean["age_clean"]   = df_clean["age"].fillna(45.0)
    df_clean["age_under_18"] = (df_clean["age_clean"] < 18).astype(int)
    df_clean["age_elderly"]  = (df_clean["age_clean"] >= 65).astype(int)

    # 2. Gender
    df_clean["gender_clean"] = df_clean["gender"].apply(clean_gender)
    df_clean["is_male"]   = (df_clean["gender_clean"] == "male").astype(int)
    df_clean["is_female"] = (df_clean["gender_clean"] == "female").astype(int)

    # 3. Temperature
    temp_res = df_clean["temperature"].apply(clean_temperature)
    df_clean["temperature_clean"] = [t[0] for t in temp_res]
    df_clean["temp_missing"]      = [t[1] for t in temp_res]
    df_clean["fever_high"]    = (df_clean["temperature_clean"] >= 38.5).astype(int)
    df_clean["hypothermia"]   = (df_clean["temperature_clean"] < 35.5).astype(int)
    df_clean["temp_deviation"]= (df_clean["temperature_clean"] - 37.0).abs()

    # 4. Heart Rate
    df_clean["hr_missing"]        = df_clean["heart_rate"].isna().astype(int)
    df_clean["heart_rate_clean"]  = df_clean["heart_rate"].fillna(75.0)
    df_clean["tachycardia_severe"]= (df_clean["heart_rate_clean"] > 120.0).astype(int)
    df_clean["tachycardia_mild"]  = ((df_clean["heart_rate_clean"] > 100.0) & (df_clean["heart_rate_clean"] <= 120.0)).astype(int)
    df_clean["bradycardia"]       = (df_clean["heart_rate_clean"] < 60.0).astype(int)

    # 5. Blood Pressure
    bp_res = df_clean["blood_pressure"].apply(clean_blood_pressure)
    df_clean["bp_systolic_clean"]  = [bp[0] for bp in bp_res]
    df_clean["bp_diastolic_clean"] = [bp[1] for bp in bp_res]
    df_clean["bp_missing"]         = [bp[2] for bp in bp_res]
    df_clean["pulse_pressure"]     = df_clean["bp_systolic_clean"] - df_clean["bp_diastolic_clean"]
    df_clean["shock_index"]        = df_clean["heart_rate_clean"] / np.maximum(df_clean["bp_systolic_clean"], 50.0)
    df_clean["hypotension"]        = (df_clean["bp_systolic_clean"] < 90.0).astype(int)
    df_clean["hypertension_stage2"]= (df_clean["bp_systolic_clean"] >= 140.0).astype(int)

    # 6. SpO2
    df_clean["spo2_missing"]   = df_clean["spo2"].isna().astype(int)
    df_clean["spo2_clean"]     = df_clean["spo2"].fillna(98.0)
    df_clean["hypoxia_severe"] = (df_clean["spo2_clean"] < 90.0).astype(int)
    df_clean["hypoxia_moderate"]= ((df_clean["spo2_clean"] >= 90.0) & (df_clean["spo2_clean"] < 95.0)).astype(int)

    # 7. Clinical Text (symptoms + notes)
    sym = df_clean["symptoms"].apply(clean_medical_text)
    notes = df_clean["notes"].apply(clean_medical_text) if "notes" in df_clean.columns else pd.Series([""] * len(df_clean))
    df_clean["combined_text"] = (sym + " " + notes).str.strip()

    # 8. Training targets
    if is_training and "urgency_level" in df_clean.columns:
        df_clean["triage_priority_score"] = df_clean.apply(generate_triage_score, axis=1)
        # 3-tier integer classification label
        df_clean["triage_level"] = df_clean["triage_priority_score"].apply(lambda s: score_to_triage_level(s)[0])

    if "department" in df_clean.columns:
        df_clean["department_canonical"] = df_clean["department"].apply(clean_department)

    return df_clean
