"""
PatientTriage.ai - Real-Time Clinical AI Inference Engine.

Architecture:
  1. Preprocesses current patient vitals & symptoms (NEVER patient history).
  2. XGBoost Regressor  → Priority Score (0–10).
  3. Safety Rule Engine → Hard clinical floors for life-threatening presentations.
  4. Uncertainty Engine → Confidence score penalized for missing vitals.
  5. Department Classifier → Recommended specialty routing.
  6. Explainability      → Plain-English key clinical factors.

3-Tier Output:
  🔴 Level 1 CRITICAL  — Score >= 7.0
  🟡 Level 2 MODERATE  — Score 4.0–6.9
  🟢 Level 3 LOW       — Score < 4.0
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

from ml.preprocessing import (
    preprocess_dataframe, NUMERICAL_FEATURE_COLS,
    score_to_triage_level, clean_temperature, clean_blood_pressure
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


class TriageInferenceEngine:
    """
    Real-time triage inference combining ML prediction, safety rule enforcement,
    explicit confidence scoring, and plain-English clinical explainability.
    """

    def __init__(self, models_dir: str = MODELS_DIR):
        self.models_dir = models_dir
        self.regressor  = None
        self.classifier = None
        self.label_encoder = None
        self.text_extractor = None
        self.reg_meta  = {}
        self.clf_meta  = {}
        self.is_loaded = False
        self._load_models()

    def _load_models(self) -> bool:
        reg_path = os.path.join(self.models_dir, "triage_regressor.pkl")
        clf_path = os.path.join(self.models_dir, "department_classifier.pkl")
        enc_path = os.path.join(self.models_dir, "label_encoder.pkl")
        txt_path = os.path.join(self.models_dir, "text_extractor.pkl")

        if not all(os.path.exists(p) for p in [reg_path, clf_path, enc_path, txt_path]):
            print("[INFO] ML models not found on disk. Train with ml/train_models.py")
            self.is_loaded = False
            return False

        try:
            with open(reg_path, "rb") as f:
                self.regressor = pickle.load(f)
            with open(clf_path, "rb") as f:
                self.classifier = pickle.load(f)
            with open(enc_path, "rb") as f:
                self.label_encoder = pickle.load(f)
            from ml.embeddings import ClinicalTextExtractor
            self.text_extractor = ClinicalTextExtractor.load(txt_path)

            for meta_path, attr in [
                ("regression_metadata.json", "reg_meta"),
                ("classification_metadata.json", "clf_meta"),
            ]:
                p = os.path.join(self.models_dir, meta_path)
                if os.path.exists(p):
                    with open(p) as f:
                        setattr(self, attr, json.load(f))

            self.is_loaded = True
            print("[SUCCESS] ML models loaded successfully.")
            return True
        except Exception as e:
            print(f"[ERROR] Error loading models: {e}")
            self.is_loaded = False
            return False

    def predict(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run real-time AI triage inference on a single patient.

        Input keys (all optional for graceful degradation):
          age, gender, symptoms, notes, temperature, heart_rate, blood_pressure, spo2

        Returns complete triage output: score, level, confidence, department,
        safety_flags, key_factors, requires_review.
        """
        if not self.is_loaded:
            if not self._load_models():
                return self._unavailable_response()

        # ─── Build single-row DataFrame ───
        row = {
            "age":            patient_data.get("age"),
            "gender":         patient_data.get("gender", "unknown"),
            "symptoms":       patient_data.get("symptoms", ""),
            "notes":          patient_data.get("notes", ""),
            "temperature":    patient_data.get("temperature"),
            "heart_rate":     patient_data.get("heart_rate"),
            "blood_pressure": patient_data.get("blood_pressure", "120/80"),
            "spo2":           patient_data.get("spo2"),
        }
        df = pd.DataFrame([row])
        df_clean = preprocess_dataframe(df, is_training=False)

        # ─── Feature assembly ───
        num_feat  = df_clean[NUMERICAL_FEATURE_COLS].values
        text_feat = self.text_extractor.transform(df_clean["combined_text"])
        X = np.hstack([num_feat, text_feat])

        # ─── 1. Priority Score Regression ───
        raw_score     = float(self.regressor.predict(X)[0])
        priority_score = float(np.clip(raw_score, 0.0, 10.0))

        # ─── 2. Department Classification ───
        probs       = self.classifier.predict_proba(X)[0]
        class_names = self.label_encoder.classes_.tolist()
        dept_probs  = {c: round(float(p), 3) for c, p in zip(class_names, probs)}
        top_idx     = int(np.argmax(probs))
        department  = class_names[top_idx]
        routing_conf = float(probs[top_idx])

        # ─── 3. Extract cleaned vitals for safety checks ───
        spo2_val  = float(df_clean["spo2_clean"].iloc[0])
        hr_val    = float(df_clean["heart_rate_clean"].iloc[0])
        sys_val   = float(df_clean["bp_systolic_clean"].iloc[0])
        dia_val   = float(df_clean["bp_diastolic_clean"].iloc[0])
        temp_val  = float(df_clean["temperature_clean"].iloc[0])
        shock_idx = float(df_clean["shock_index"].iloc[0])

        # ─── 4. Safety Rule Engine (hard clinical floors) ───
        safety_flags: List[str] = []

        if spo2_val < 90.0:
            safety_flags.append(f"⚠ Severe Hypoxemia: SpO₂ {spo2_val:.0f}% — Immediate oxygen required")
            priority_score = max(priority_score, 8.5)
            department = "Emergency"

        if sys_val < 90.0:
            safety_flags.append(f"⚠ Severe Hypotension: BP {sys_val:.0f}/{dia_val:.0f} mmHg — Shock risk")
            priority_score = max(priority_score, 8.0)

        if shock_idx >= 1.0:
            safety_flags.append(f"⚠ Elevated Shock Index {shock_idx:.2f} — Haemodynamic instability")
            priority_score = max(priority_score, 7.5)

        if hr_val > 130.0:
            safety_flags.append(f"⚠ Severe Tachycardia: HR {hr_val:.0f} bpm")
            priority_score = max(priority_score, 7.0)
        elif hr_val < 45.0:
            safety_flags.append(f"⚠ Severe Bradycardia: HR {hr_val:.0f} bpm")
            priority_score = max(priority_score, 7.5)

        if temp_val >= 40.0:
            safety_flags.append(f"⚠ Hyperpyrexia: Temperature {temp_val:.1f}°C")

        priority_score = round(float(np.clip(priority_score, 0.0, 10.0)), 1)

        # ─── 5. 3-Tier Level Assignment ───
        level_int, level_label, level_color = score_to_triage_level(priority_score)

        # ─── 6. Uncertainty / Confidence Engine ───
        missing_count = int(
            df_clean["age_missing"].iloc[0] +
            df_clean["temp_missing"].iloc[0] +
            df_clean["hr_missing"].iloc[0] +
            df_clean["spo2_missing"].iloc[0] +
            df_clean["bp_missing"].iloc[0]
        )
        # Base confidence from routing probability
        base_confidence = routing_conf
        # Penalize each missing critical vital by 8%
        completeness_factor = max(0.50, 1.0 - (missing_count * 0.08))
        overall_confidence  = round(float(base_confidence * completeness_factor), 2)

        # Missing-vital uncertainty warnings
        uncertainty_flags: List[str] = []
        if df_clean["spo2_missing"].iloc[0]:
            uncertainty_flags.append("SpO₂ not recorded — oxygen status unknown")
        if df_clean["hr_missing"].iloc[0]:
            uncertainty_flags.append("Heart rate not recorded — cardiac status unknown")
        if df_clean["bp_missing"].iloc[0]:
            uncertainty_flags.append("Blood pressure not recorded — haemodynamic status unknown")
        if df_clean["temp_missing"].iloc[0]:
            uncertainty_flags.append("Temperature not recorded — fever/hypothermia cannot be assessed")
        if df_clean["age_missing"].iloc[0]:
            uncertainty_flags.append("Patient age unknown — age-adjusted risk cannot be computed")

        # Low confidence → mandatory clinician review
        requires_review = (overall_confidence < 0.72) or bool(safety_flags) or bool(uncertainty_flags)

        # ─── 7. Clinical Explainability ───
        key_factors = self._generate_key_factors(
            patient_data, df_clean, spo2_val, hr_val, sys_val, dia_val, temp_val,
            shock_idx, level_int, safety_flags
        )

        return {
            "available": True,
            # Core triage output
            "priority_score":        priority_score,
            "triage_level":          level_int,
            "triage_label":          level_label,
            "triage_color":          level_color,
            # Department routing
            "recommended_department": department,
            "department_probabilities": dept_probs,
            "routing_confidence":    round(routing_conf, 2),
            # Confidence & uncertainty
            "confidence":            overall_confidence,
            "confidence_pct":        int(overall_confidence * 100),
            "missing_vitals_count":  missing_count,
            "uncertainty_flags":     uncertainty_flags,
            "requires_clinician_review": requires_review,
            # Clinical safety & reasoning
            "safety_flags":          safety_flags,
            "key_factors":           key_factors,
            # Normalized vitals (returned for display)
            "vitals_normalized": {
                "temperature_c":  round(temp_val, 1),
                "heart_rate":     round(hr_val, 0),
                "bp_systolic":    round(sys_val, 0),
                "bp_diastolic":   round(dia_val, 0),
                "spo2":           round(spo2_val, 1),
                "shock_index":    round(shock_idx, 2),
            },
            "model_version": self.reg_meta.get("model_version", "triage-v1.0"),
        }

    def _generate_key_factors(
        self, patient_data, df_clean,
        spo2, hr, sys_bp, dia_bp, temp, shock_idx,
        level_int, safety_flags
    ) -> List[str]:
        """Generates human-readable clinical reasons for the triage recommendation."""
        factors: List[str] = []

        # Safety flags are the highest-priority factors
        if safety_flags:
            factors.extend(safety_flags)

        # Symptom-based clinical rationale
        symptoms = str(patient_data.get("symptoms", "")).lower()
        notes    = str(patient_data.get("notes", "")).lower()
        combined = symptoms + " " + notes

        if any(k in combined for k in ["chest", "cardiac", "myocard"]):
            factors.append("Chest pain / cardiac symptoms — immediate cardiac evaluation required")
        if any(k in combined for k in ["breath", "sob", "dyspnea", "breathless"]):
            factors.append("Respiratory distress — pulmonary/airway assessment required")
        if any(k in combined for k in ["headache", "head", "dizzy", "vertigo", "neuro"]):
            factors.append("Neurological symptoms — neurological evaluation required")
        if any(k in combined for k in ["abdom", "nausea", "vomit", "stomach"]):
            factors.append("Abdominal symptoms — gastroenterology evaluation indicated")
        if any(k in combined for k in ["throat", "ear", "sore throat"]):
            factors.append("ENT symptoms — ear/nose/throat evaluation recommended")

        # Vital sign factors
        if 94.0 <= spo2 < 95.0:
            factors.append(f"Borderline SpO₂ {spo2:.0f}% — monitor closely")
        if hr > 105.0:
            factors.append(f"Tachycardia HR {hr:.0f} bpm — cardiac workload elevated")
        if sys_bp >= 140.0:
            factors.append(f"Hypertension {sys_bp:.0f}/{dia_bp:.0f} mmHg")
        if temp >= 38.5:
            factors.append(f"Fever {temp:.1f}°C — infection workup indicated")

        # Age group factors
        age = patient_data.get("age")
        if age is not None:
            if age < 18:
                factors.append(f"Pediatric patient (age {age:.0f}) — age-adjusted protocols apply")
            elif age >= 65:
                factors.append(f"Geriatric patient (age {age:.0f}) — elevated baseline risk")

        if not factors:
            factors.append(f"Vitals within normal ranges; routine assessment assigned Level {level_int}")

        return factors[:6]  # Return max 6 factors for clear UI display

    @staticmethod
    def _unavailable_response() -> Dict[str, Any]:
        return {
            "available": False,
            "error": "AI models not loaded — run ml/train_models.py first",
            "priority_score": None,
            "triage_level": None,
            "triage_label": "PENDING — Clinician Assessment Required",
            "triage_color": "gray",
            "recommended_department": "General Medicine",
            "confidence": 0.0,
            "confidence_pct": 0,
            "requires_clinician_review": True,
            "safety_flags": ["AI service unavailable — manual triage required"],
            "uncertainty_flags": [],
            "key_factors": ["Automated prediction unavailable. Clinician must triage manually."],
            "model_version": "unavailable",
        }


# Singleton inference engine (loaded once at backend startup)
inference_engine = TriageInferenceEngine()
