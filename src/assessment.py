"""Application-level checks before model loading or scoring."""
import joblib
import pandas as pd

from src.model import MODEL_FILE, SELECTED_FEATURES, SELECTED_THRESHOLD
from src.decisions import (
    REQUIRED_FIELDS, advisory_decision, collect_rule_reasons,
    missing_application_fields, review_result, validate_application_fields,
    validate_score, validate_threshold,
)

APPLICATION_FIELDS = tuple(dict.fromkeys([*SELECTED_FEATURES, *REQUIRED_FIELDS]))


def score_application(application):
    """Return the score for a complete application; use assess_application for the full workflow."""
    validate_application_fields(application, SELECTED_FEATURES)
    if not MODEL_FILE.is_file():
        raise FileNotFoundError('No trained model: first run python -m src.main')
    model = joblib.load(MODEL_FILE)
    row = pd.DataFrame([application], columns=SELECTED_FEATURES)
    return validate_score(float(model.predict_proba(row)[0, 1]))


def assess_application(application, *, scorer=None, threshold=SELECTED_THRESHOLD):
    """Assess one application, sending incomplete ones to information-completion review."""
    # The scorer can be replaced in tests so no model file is needed.
    threshold = validate_threshold(threshold)
    missing = missing_application_fields(application, APPLICATION_FIELDS)
    present = [field for field in APPLICATION_FIELDS if field not in missing]
    # Invalid supplied data is an error even when another field is missing.
    validate_application_fields(application, present)
    if missing:
        affordability, risk = collect_rule_reasons(
            application, score=None, threshold=threshold
        )
        reasons = [f'Required information missing: {", ".join(missing)}']
        return review_result(
            'INFORMATION_COMPLETION_REVIEW', reasons + affordability + risk,
            score=None, threshold=threshold, missing_fields=missing,
        )
    score = (score_application if scorer is None else scorer)(application)
    return advisory_decision(score, application, threshold=threshold)
