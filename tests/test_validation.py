"""Tests for validation helpers and provisional advisory rules."""
import unittest
from pathlib import Path
import pandas as pd
from src.decisions import (
    HIGHER_REVIEW_THRESHOLD,
    LOWER_REVIEW_THRESHOLD,
    advisory_decision,
    validate_application_fields,
    validate_score,
)
from src.model import (
    BASELINE_FEATURES,
    EXTENDED_FEATURES,
    run_model,
    split_data_three_way,
)


VALID_APPLICATION = {
    'credit_score': 680,
    'debt_to_income_ratio': 0.32,
}

class GenericValidationTests(unittest.TestCase):
    def test_valid_score(self):
        self.assertEqual(validate_score(0.4), 0.4)

    def test_score_outside_range(self):
        with self.assertRaises(ValueError):
            validate_score(1.5)

    def test_required_value_present(self):
        self.assertTrue(validate_application_fields({'credit_score': 680}, ['credit_score']))

    def test_required_value_missing(self):
        with self.assertRaises(ValueError):
            validate_application_fields({}, ['credit_score'])


class AdvisoryDecisionTests(unittest.TestCase):
    def test_score_below_lower_threshold_gets_standard_review(self):
        decision = advisory_decision(LOWER_REVIEW_THRESHOLD - 0.01, VALID_APPLICATION)

        self.assertEqual(decision['outcome'], 'STANDARD REVIEW')
        self.assertEqual(decision['reason'], 'The model score is in the lower review band.')
        self.assertEqual(decision['status'], 'HUMAN REVIEW REQUIRED')

    def test_lower_threshold_gets_middle_band(self):
        decision = advisory_decision(LOWER_REVIEW_THRESHOLD, VALID_APPLICATION)

        self.assertEqual(decision['outcome'], 'STANDARD REVIEW')
        self.assertEqual(decision['reason'], 'The model score is in the middle review band.')

    def test_score_just_below_higher_threshold_gets_standard_review(self):
        decision = advisory_decision(HIGHER_REVIEW_THRESHOLD - 0.01, VALID_APPLICATION)

        self.assertEqual(decision['outcome'], 'STANDARD REVIEW')
        self.assertEqual(decision['reason'], 'The model score is in the middle review band.')

    def test_higher_threshold_gets_enhanced_review(self):
        decision = advisory_decision(HIGHER_REVIEW_THRESHOLD, VALID_APPLICATION)

        self.assertEqual(decision['outcome'], 'ENHANCED REVIEW')
        self.assertEqual(decision['reason'], 'The model score is in the higher review band.')
        self.assertEqual(decision['status'], 'HUMAN REVIEW REQUIRED')

    def test_score_above_higher_threshold_gets_enhanced_review(self):
        decision = advisory_decision(HIGHER_REVIEW_THRESHOLD + 0.01, VALID_APPLICATION)

        self.assertEqual(decision['outcome'], 'ENHANCED REVIEW')

    def test_invalid_score_is_rejected(self):
        for score in (-0.01, 1.01, float('nan'), '0.4'):
            with self.subTest(score=score):
                with self.assertRaises(ValueError):
                    advisory_decision(score, VALID_APPLICATION)

    def test_missing_required_application_field_is_rejected(self):
        application = {'credit_score': 680}

        with self.assertRaisesRegex(ValueError, 'debt_to_income_ratio'):
            advisory_decision(0.4, application)


class ModelSplitTests(unittest.TestCase):
    def test_three_way_split_is_disjoint_and_has_expected_sizes(self):
        frame = pd.DataFrame({
            'credit_score': range(600, 700),
            'debt_to_income_ratio': [0.2 + (index % 10) / 100 for index in range(100)],
            'repayment_difficulty_12m': [index % 2 for index in range(100)],
        })

        X_train, X_validation, X_final_test, y_train, y_validation, y_final_test = (
            split_data_three_way(frame)
        )

        self.assertEqual(len(X_train), 64)
        self.assertEqual(len(X_validation), 16)
        self.assertEqual(len(X_final_test), 20)
        self.assertEqual(len(y_train), 64)
        self.assertEqual(len(y_validation), 16)
        self.assertEqual(len(y_final_test), 20)
        self.assertFalse(set(X_train.index) & set(X_validation.index))
        self.assertFalse(set(X_train.index) & set(X_final_test.index))
        self.assertFalse(set(X_validation.index) & set(X_final_test.index))
        self.assertEqual(
            set(X_train.index) | set(X_validation.index) | set(X_final_test.index),
            set(frame.index),
        )

    def test_extended_feature_set_adds_missed_payments(self):
        self.assertEqual(
            EXTENDED_FEATURES,
            BASELINE_FEATURES + ['missed_payments_24m'],
        )

    def test_reusable_model_runner_returns_all_evaluation_partitions(self):
        frame = pd.DataFrame({
            'credit_score': range(600, 700),
            'debt_to_income_ratio': [0.2 + (index % 10) / 100 for index in range(100)],
            'missed_payments_24m': [index % 3 for index in range(100)],
            'repayment_difficulty_12m': [index % 2 for index in range(100)],
        })

        results = run_model(frame, EXTENDED_FEATURES)

        self.assertEqual(results['features'], EXTENDED_FEATURES)
        self.assertIn('validation', results)
        self.assertIn('final', results)
        self.assertIn('confusion_matrix', results['validation'])

    def test_comparison_without_model_file_does_not_overwrite_saved_model(self):
        frame = pd.DataFrame({
            'credit_score': range(600, 700),
            'debt_to_income_ratio': [0.2 + (index % 10) / 100 for index in range(100)],
            'missed_payments_24m': [index % 3 for index in range(100)],
            'repayment_difficulty_12m': [index % 2 for index in range(100)],
        })
        model_file = Path('/tmp/mortgage-baseline-test.joblib')

        run_model(frame, BASELINE_FEATURES, model_file)
        run_model(frame, EXTENDED_FEATURES)

        import joblib
        saved_model = joblib.load(model_file)
        self.assertEqual(
            list(saved_model.feature_names_in_),
            BASELINE_FEATURES,
        )
        model_file.unlink()


if __name__ == '__main__':
    unittest.main()
