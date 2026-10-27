"""Generic validation examples; no mortgage advisory policy is supplied."""
import math
from numbers import Real

# Temporary thresholds for triggering different levels of review based on model score.
LOWER_REVIEW_THRESHOLD = 0.25
HIGHER_REVIEW_THRESHOLD = 0.50


def validate_application_fields(application, required_fields):
    """Reject absent, blank or non-finite values in the selected fields."""
    invalid = []
    for field in required_fields:
        value = application.get(field)
        if (value is None or
            (isinstance(value, str) and not value.strip()) or
            (isinstance(value, Real) and not math.isfinite(value))):
            invalid.append(field)
    if invalid:
        raise ValueError(f'Missing or invalid fields: {invalid}')
    # LEARNER: add field-specific ranges and consistency rules.
    return True


def validate_score(score):
    """Check that a binary classifier's reported score is in the interval [0, 1]."""
    if isinstance(score, bool) or not isinstance(score, Real):
        raise ValueError('Model score must be numeric')
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError('Model score must be finite and between 0 and 1')
    return float(score)

# Temporary advisory decision logic.
# Determine the advisory decision based on the model score and application fields.
def advisory_decision(score, application):
    score = validate_score(score)
    validate_application_fields(
        application,
        ["credit_score", "debt_to_income_ratio"],
    )

    if score >= HIGHER_REVIEW_THRESHOLD:
        outcome = "ENHANCED REVIEW"
        reason = "The model score is in the higher review band."
    elif score >= LOWER_REVIEW_THRESHOLD:
        outcome = "STANDARD REVIEW"
        reason = "The model score is in the middle review band."
    else:
        outcome = "STANDARD REVIEW"
        reason = "The model score is in the lower review band."

    return {
        "outcome": outcome,
        "reason": reason,
        "status": "HUMAN REVIEW REQUIRED",
    }
