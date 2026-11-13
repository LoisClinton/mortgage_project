"""Application workflow and evidence tests for formative feedback."""
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import numpy as np
from src.assessment import APPLICATION_FIELDS, assess_application
from src.decisions import advisory_decision
from src.reporting import save_final_test_evidence

APP = dict(credit_score=680, debt_to_income_ratio=.32, missed_payments_24m=0,
           previous_default_flag=0, loan_to_value_pct=80.)


class AssessmentTests(unittest.TestCase):
    """Tests for the application workflow, including missing and invalid data."""

    def test_complete_application_is_scored_once(self):
        scorer = Mock(return_value=.1)
        result = assess_application(APP, scorer=scorer)
        scorer.assert_called_once_with(APP)
        self.assertEqual(result['outcome'], 'STANDARD_REVIEW')
        self.assertEqual(result['score'], .1)
        self.assertEqual(result['missing_fields'], [])

    def test_every_required_field_and_missing_representation(self):
        for field in APPLICATION_FIELDS:
            for form in ('absent', 'none', 'nan'):
                with self.subTest(field=field, form=form):
                    application = APP.copy()
                    if form == 'absent':
                        application.pop(field)
                    else:
                        application[field] = None if form == 'none' else float('nan')
                    scorer = Mock()
                    result = assess_application(application, scorer=scorer)
                    scorer.assert_not_called()
                    self.assertEqual(result['outcome'], 'INFORMATION_COMPLETION_REVIEW')
                    self.assertEqual(result['missing_fields'], [field])
                    self.assertIsNone(result['score'])
                    self.assertEqual(result['status'], 'HUMAN REVIEW REQUIRED')

    def test_empty_application_lists_all_missing_fields(self):
        scorer = Mock()
        result = assess_application({}, scorer=scorer)
        self.assertEqual(result['missing_fields'], list(APPLICATION_FIELDS))
        self.assertIsNone(result['score'])
        scorer.assert_not_called()

    def test_missing_rule_input_does_not_load_model(self):
        with patch('src.assessment.joblib.load') as loader:
            result = assess_application({**APP, 'loan_to_value_pct': None})
        loader.assert_not_called()
        self.assertIsNone(result['score'])

    def test_multiple_missing_fields_do_not_imply_enhanced_credit_risk(self):
        scorer = Mock()
        result = assess_application({**APP, 'credit_score': None,
                                     'previous_default_flag': None}, scorer=scorer)
        self.assertEqual(result['outcome'], 'INFORMATION_COMPLETION_REVIEW')
        self.assertEqual(result['missing_fields'], ['credit_score', 'previous_default_flag'])
        scorer.assert_not_called()

    def test_missing_information_priority_retains_known_triggers(self):
        scorer = Mock()
        result = assess_application({**APP, 'credit_score': None,
                                     'debt_to_income_ratio': .6,
                                     'loan_to_value_pct': 95.,
                                     'missed_payments_24m': 3}, scorer=scorer)
        self.assertEqual(result['outcome'], 'INFORMATION_COMPLETION_REVIEW')
        self.assertEqual(len(result['reasons']), 4)
        for text in ('DTI exceeds', 'LTV exceeds', 'missed-payment history'):
            self.assertIn(text, result['reason'])
        self.assertNotIn('Model score meets', result['reason'])
        scorer.assert_not_called()

    def test_all_sixteen_risk_condition_combinations(self):
        for dti, ltv, model_risk, missed in itertools.product((False, True), repeat=4):
            with self.subTest(dti=dti, ltv=ltv, model_risk=model_risk, missed=missed):
                application = {**APP, 'debt_to_income_ratio': .6 if dti else .32,
                               'loan_to_value_pct': 95. if ltv else 80.,
                               'missed_payments_24m': 2 if missed else 0}
                result = assess_application(application, scorer=Mock(return_value=.7 if model_risk else .1))
                expected = ('AFFORDABILITY_REVIEW' if dti or ltv else
                            'ENHANCED_RISK_REVIEW' if model_risk or missed else 'STANDARD_REVIEW')
                self.assertEqual(result['outcome'], expected)
                for active, phrase in [(dti, 'DTI exceeds'), (ltv, 'LTV exceeds'),
                                       (model_risk, 'Model score meets'),
                                       (missed, 'missed-payment history')]:
                    self.assertEqual(phrase in result['reason'], active)
                self.assertEqual(len(result['reasons']), max(1, sum((dti, ltv, model_risk, missed))))
                self.assertEqual(result['status'], 'HUMAN REVIEW REQUIRED')

    def test_invalid_supplied_values_are_errors_before_scoring(self):
        cases = {'credit_score': [299, 901, '', '680', True, float('inf')],
                 'debt_to_income_ratio': [-.1, 2.1],
                 'missed_payments_24m': [-1, .5, 25],
                 'previous_default_flag': [-1, 2, .5, False],
                 'loan_to_value_pct': [0, 151]}
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    scorer = Mock()
                    with self.assertRaisesRegex(ValueError, field):
                        assess_application({**APP, field: value}, scorer=scorer)
                    scorer.assert_not_called()

    def test_invalid_value_is_not_hidden_by_other_missing_field(self):
        scorer = Mock()
        with self.assertRaisesRegex(ValueError, 'previous_default_flag'):
            assess_application({**APP, 'credit_score': None, 'previous_default_flag': 2}, scorer=scorer)
        scorer.assert_not_called()

    def test_invalid_model_score_is_rejected(self):
        for score in (-.1, 1.1, None, float('nan'), float('inf'), True):
            with self.subTest(score=score), self.assertRaises(ValueError):
                assess_application(APP, scorer=Mock(return_value=score))

    def test_explicit_threshold_and_invalid_thresholds(self):
        with self.assertRaises(TypeError):
            advisory_decision(.4, APP)
        for threshold in (0, -.1, 1.1, None, True, float('nan')):
            with self.subTest(threshold=threshold):
                scorer = Mock()
                with self.assertRaises(ValueError):
                    assess_application(APP, scorer=scorer, threshold=threshold)
                scorer.assert_not_called()

    def test_selected_threshold_through_application_entry_point(self):
        for score, outcome in [(.249999, 'STANDARD_REVIEW'), (.25, 'ENHANCED_RISK_REVIEW')]:
            with self.subTest(score=score):
                result = assess_application(APP, scorer=Mock(return_value=score))
                self.assertEqual(result['threshold'], .25)
                self.assertEqual(result['outcome'], outcome)


class ReportingTests(unittest.TestCase):
    """Tests for the saved final-test evidence."""

    def test_evidence_uses_supplied_evaluation_matrix(self):
        result = {'accuracy': .75, 'confusion_matrix': np.array([[2, 1], [0, 1]])}
        with tempfile.TemporaryDirectory() as folder:
            metrics, figure = save_final_test_evidence(
                result, features=['credit_score'], threshold=.3, output_dir=folder)
            evidence = json.loads(metrics.read_text())
            self.assertEqual(evidence['sample_count'], 4)
            self.assertEqual(evidence['partition'], 'final_test')
            self.assertEqual(evidence['metrics']['confusion_matrix'], [[2, 1], [0, 1]])
            self.assertEqual(evidence['threshold'], .3)
            self.assertTrue(figure.is_file())

    def test_absent_final_results_are_not_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                save_final_test_evidence(None, features=[], threshold=.25, output_dir=folder)
            self.assertEqual(list(Path(folder).iterdir()), [])
