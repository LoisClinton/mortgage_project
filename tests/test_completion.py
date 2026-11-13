"""Tests for rule boundaries, rule priority and explicit final-test evaluation."""
import unittest
from src.decisions import advisory_decision, validate_application_fields
from src.model import run_model, SELECTED_FEATURES, SELECTED_THRESHOLD
from src.data import load_data

APP = {
    "credit_score": 680,
    "debt_to_income_ratio": 0.32,
    "missed_payments_24m": 0,
    "previous_default_flag": 0,
    "loan_to_value_pct": 80.0,
}


class CompletionTests(unittest.TestCase):
    """Boundary, priority and final-test behaviour of the advisory rules."""

    def decide(self, score=0.1, **changes):
        """Run advisory_decision on the example application with some fields changed."""
        application = {**APP, **changes}
        return advisory_decision(score, application, threshold=SELECTED_THRESHOLD)

    def test_selected_threshold_boundary(self):
        cases = [
            (0.249999, 'STANDARD_REVIEW'),
            (0.25, 'ENHANCED_RISK_REVIEW'),
            (0.250001, 'ENHANCED_RISK_REVIEW'),
        ]
        for score, expected in cases:
            with self.subTest(score=score):
                self.assertEqual(self.decide(score)['outcome'], expected)

    def test_affordability_boundaries(self):
        cases = [
            (0.45, 90, "STANDARD_REVIEW"),
            (0.450001, 90, "AFFORDABILITY_REVIEW"),
            (0.45, 90.000001, "AFFORDABILITY_REVIEW"),
        ]
        for dti, ltv, expected in cases:
            with self.subTest(dti=dti, ltv=ltv):
                result = self.decide(
                    debt_to_income_ratio=dti, loan_to_value_pct=ltv
                )
                self.assertEqual(result['outcome'], expected)

    def test_missed_payment_boundary(self):
        one_missed = self.decide(missed_payments_24m=1)
        two_missed = self.decide(missed_payments_24m=2)
        self.assertEqual(one_missed['outcome'], 'STANDARD_REVIEW')
        self.assertEqual(two_missed['outcome'], 'ENHANCED_RISK_REVIEW')

    def test_affordability_priority(self):
        result = self.decide(
            0.9, debt_to_income_ratio=0.6, missed_payments_24m=3
        )
        self.assertEqual(result['outcome'], 'AFFORDABILITY_REVIEW')
        self.assertEqual(result['status'], 'HUMAN REVIEW REQUIRED')

    def test_default_flag_domain(self):
        for value in [-1, 2, 0.5, True, float('nan')]:
            application = {**APP, 'previous_default_flag': value}
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_application_fields(application, SELECTED_FEATURES)

    def test_final_evaluation_is_explicit(self):
        df = load_data()
        # The final test stays unused unless it is requested.
        self.assertIsNone(run_model(df, SELECTED_FEATURES)['final'])
        result = run_model(df, SELECTED_FEATURES, evaluate_final=True)['final']
        self.assertEqual(result['confusion_matrix'].sum(), 160)
        self.assertEqual(result['confusion_matrix'].tolist(), [[89, 36], [15, 20]])
