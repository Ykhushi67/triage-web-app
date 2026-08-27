"""
PatientTriage.ai - ML Model Training Pipeline.

Trains two models from raw_patient_visits.csv:
  1. XGBoost Regressor   → Triage Priority Score (0–10 continuous)
  2. XGBoost Classifier  → Department Recommendation (7-class)

Both models consume ONLY current patient vitals + symptoms.
Patient history (patient_id, visit_date, waiting_time_min) is NEVER used.
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, mean_absolute_error, mean_squared_error, r2_score
)
import xgboost as xgb

from ml.preprocessing import preprocess_dataframe, NUMERICAL_FEATURE_COLS, score_to_triage_level
from ml.embeddings import ClinicalTextExtractor

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def train_all_models(
    csv_path: str = None,
    output_dir: str = MODELS_DIR,
    random_state: int = 42
):
    """
    Trains the XGBoost Regressor and Department Classifier.
    Saves models, encoders, and evaluation metadata to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Resolve CSV path relative to project root
    if csv_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, "..", "..", "raw_patient_visits.csv")
    csv_path = os.path.abspath(csv_path)

    print(f"\n{'-'*50}")
    print("PatientTriage.ai -- Model Training Pipeline")
    print(f"{'-'*50}")
    print(f"Loading dataset: {csv_path}")

    raw_df = pd.read_csv(csv_path)
    print(f"Records loaded: {len(raw_df)}")

    # Preprocess
    df = preprocess_dataframe(raw_df, is_training=True)
    print(f"Records after preprocessing: {len(df)}")

    # ─────────────────────────────────────────────
    # Shared text extraction (fit once, use for both models)
    # ─────────────────────────────────────────────
    text_extractor = ClinicalTextExtractor(max_features=64)
    text_features = text_extractor.fit_transform(df["combined_text"])
    num_features = df[NUMERICAL_FEATURE_COLS].values
    X = np.hstack([num_features, text_features])
    feature_names = NUMERICAL_FEATURE_COLS + text_extractor.get_feature_names()

    print(f"Total feature dimensions: {X.shape[1]}")

    # Save shared text extractor
    text_extractor.save(os.path.join(output_dir, "text_extractor.pkl"))
    print("Text extractor saved.")

    # ─────────────────────────────────────────────
    # 1. REGRESSION MODEL — Triage Priority Score (0–10)
    # ─────────────────────────────────────────────
    print(f"\n{'-'*50}")
    print("Training Triage Priority Score Regressor (XGBoost)...")

    y_reg = df["triage_priority_score"].values

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y_reg, test_size=0.30, random_state=random_state
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=random_state
    )

    regressor = xgb.XGBRegressor(
        n_estimators=350,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.5,
        random_state=random_state,
        tree_method="hist",
        verbosity=0,
    )
    regressor.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    y_pred_reg = regressor.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred_reg)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_reg))
    r2   = r2_score(y_test, y_pred_reg)

    print(f"  Regressor — MAE: {mae:.4f} | RMSE: {rmse:.4f} | R²: {r2:.4f}")

    with open(os.path.join(output_dir, "triage_regressor.pkl"), "wb") as f:
        pickle.dump(regressor, f)

    reg_meta = {
        "model_name": "Triage Priority Score Regressor",
        "model_version": "triage-v1.0",
        "algorithm": "XGBoost Regressor",
        "target": "triage_priority_score [0-10]",
        "feature_count": X.shape[1],
        "feature_names": feature_names[:30],  # First 30 for readability
        "training_records": len(X_train),
        "test_metrics": {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 4)},
        "triage_tiers": {
            "Level 1 CRITICAL": "Score >= 7.0",
            "Level 2 MODERATE": "Score 4.0 – 6.9",
            "Level 3 LOW": "Score < 4.0"
        }
    }
    with open(os.path.join(output_dir, "regression_metadata.json"), "w") as f:
        json.dump(reg_meta, f, indent=2)

    # ─────────────────────────────────────────────
    # 2. CLASSIFICATION MODEL — Department Routing
    # ─────────────────────────────────────────────
    print(f"\n{'-'*50}")
    print("Training Department Recommendation Classifier (XGBoost)...")

    valid_mask = df["department_canonical"].notna()
    df_clf = df[valid_mask].copy()
    X_clf = np.hstack([
        df_clf[NUMERICAL_FEATURE_COLS].values,
        text_extractor.transform(df_clf["combined_text"])
    ])

    label_encoder = LabelEncoder()
    y_clf = label_encoder.fit_transform(df_clf["department_canonical"])
    class_names = label_encoder.classes_.tolist()
    print(f"  Departments: {class_names}")

    # Class weights to handle imbalance
    from sklearn.utils.class_weight import compute_sample_weight
    sample_weights = compute_sample_weight("balanced", y_clf)

    X_tr, X_tmp, y_tr, y_tmp, sw_tr, _ = train_test_split(
        X_clf, y_clf, sample_weights,
        test_size=0.30, random_state=random_state, stratify=y_clf
    )
    X_v, X_te, y_v, y_te = train_test_split(
        X_tmp, y_tmp, test_size=0.50, random_state=random_state, stratify=y_tmp
    )

    classifier = xgb.XGBClassifier(
        n_estimators=350,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.5,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=random_state,
        tree_method="hist",
        verbosity=0,
        num_class=len(class_names),
    )
    classifier.fit(
        X_tr, y_tr,
        sample_weight=sw_tr,
        eval_set=[(X_v, y_v)],
        verbose=False,
    )

    y_pred_clf = classifier.predict(X_te)
    acc  = accuracy_score(y_te, y_pred_clf)
    f1   = f1_score(y_te, y_pred_clf, average="weighted")

    print(f"  Classifier — Accuracy: {acc:.4f} | Weighted F1: {f1:.4f}")
    print(classification_report(y_te, y_pred_clf, target_names=class_names))

    with open(os.path.join(output_dir, "department_classifier.pkl"), "wb") as f:
        pickle.dump(classifier, f)
    with open(os.path.join(output_dir, "label_encoder.pkl"), "wb") as f:
        pickle.dump(label_encoder, f)

    clf_meta = {
        "model_name": "Department Recommendation Classifier",
        "model_version": "dept-v1.0",
        "algorithm": "XGBoost Classifier",
        "target": "canonical_department",
        "classes": class_names,
        "training_records": len(X_tr),
        "test_metrics": {"accuracy": round(acc, 4), "weighted_f1": round(f1, 4)},
    }
    with open(os.path.join(output_dir, "classification_metadata.json"), "w") as f:
        json.dump(clf_meta, f, indent=2)

    print(f"\n{'='*60}")
    print("Training Complete. All models saved to:", output_dir)
    print(f"{'='*60}\n")

    return {
        "regressor_mae": round(mae, 4),
        "regressor_r2": round(r2, 4),
        "classifier_accuracy": round(acc, 4),
        "classifier_f1": round(f1, 4),
    }


if __name__ == "__main__":
    train_all_models()
