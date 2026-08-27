"""
PatientTriage.ai — Standalone Test Runner.
Executes all verification tests for ML inference, independent history lookup,
clinician override logging, live queue sorting, and surge mode.
"""

import os
import sys

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.test_triage_backend import (
    setup_test_environment,
    test_root_health,
    test_auth_login,
    test_ml_inference_cardiac_emergency,
    test_ml_inference_missing_vitals_uncertainty,
    test_ml_safety_rule_hypoxemia_floor,
    test_independent_patient_history_lookup,
    test_live_queue_and_override,
    test_surge_mode_and_actions,
)


def run_all_tests():
    print("=" * 65)
    print("PatientTriage.ai -- Automated Verification Test Suite")
    print("=" * 65)

    setup_test_environment()
    tests = [
        ("Root Health & DPDP Compliance Endpoint", test_root_health),
        ("Role-Based Auth (Doctor & Triage Nurse)", test_auth_login),
        ("ML Inference — High-Risk Cardiac Presentation", test_ml_inference_cardiac_emergency),
        ("ML Uncertainty Engine — Missing Vitals Penalty", test_ml_inference_missing_vitals_uncertainty),
        ("ML Safety Rule Engine — Hypoxemia Floor (SpO2 < 90%)", test_ml_safety_rule_hypoxemia_floor),
        ("Independent History Lookup (Zero ML Bias)", test_independent_patient_history_lookup),
        ("Live Queue Sorting & Clinician Override Logging", test_live_queue_and_override),
        ("Surge Mode Operations & Actionable Alerts", test_surge_mode_and_actions),
    ]

    passed = 0
    for name, test_fn in tests:
        try:
            print(f"\n[RUNNING] {name}...")
            test_fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 65)
    print(f"Test Suite Summary: {passed}/{len(tests)} Passed")
    print("=" * 65 + "\n")
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
