"""Input validation and advisory rules; no lending decisions."""
import math
from numbers import Real

MAX_STANDARD_DTI = 0.45
MAX_STANDARD_LTV_PCT = 90.0
MISSED_PAYMENT_REVIEW_COUNT = 2
REQUIRED_FIELDS = (
    'credit_score', 'debt_to_income_ratio',
    'missed_payments_24m', 'loan_to_value_pct',
)


def is_missing(value):
    """Treat None and numeric NaN as missing."""
    return value is None or (isinstance(value, Real) and math.isnan(value))


def missing_application_fields(application, required_fields):
    """List the required fields that are missing from an application."""
    return [field for field in required_fields if is_missing(application.get(field))]


def validate_application_fields(application, required_fields):
    """Strict validation for supplied numeric fields, including their domains."""
    invalid = []
    for field in required_fields:
        value = application.get(field)
        if (isinstance(value, bool) or not isinstance(value, Real)
                or not math.isfinite(value)):
            invalid.append(field)
            continue
        if field == 'credit_score' and not 300 <= value <= 900:
            invalid.append(field)
        elif field == 'debt_to_income_ratio' and not 0 <= value <= 2:
            invalid.append(field)
        elif field == 'missed_payments_24m' and (
                value < 0 or value > 24 or int(value) != value):
            invalid.append(field)
        elif field == 'previous_default_flag' and value not in (0, 1):
            invalid.append(field)
        elif field == 'loan_to_value_pct' and not 0 < value <= 150:
            invalid.append(field)
    if invalid:
        raise ValueError(f'Missing or invalid fields: {invalid}')
    return True


def validate_score(score):
    """Check that a model score is numeric and between 0 and 1."""
    if isinstance(score, bool) or not isinstance(score, Real):
        raise ValueError('Model score must be numeric')
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError('Model score must be finite and between 0 and 1')
    return float(score)


def validate_threshold(threshold):
    """Check that a threshold is a valid score greater than zero."""
    threshold = validate_score(threshold)
    if threshold == 0:
        raise ValueError('Threshold must be greater than zero')
    return threshold


def collect_rule_reasons(application, *, score, threshold):
    """Collect all triggers from already validated, available inputs."""
    affordability = []
    risk = []
    dti = application.get('debt_to_income_ratio')
    ltv = application.get('loan_to_value_pct')
    missed = application.get('missed_payments_24m')
    if not is_missing(dti) and dti > MAX_STANDARD_DTI:
        affordability.append('DTI exceeds illustrative affordability review boundary')
    if not is_missing(ltv) and ltv > MAX_STANDARD_LTV_PCT:
        affordability.append('LTV exceeds illustrative affordability review boundary')
    if score is not None and score >= threshold:
        risk.append('Model score meets selected risk-review threshold')
    if not is_missing(missed) and missed >= MISSED_PAYMENT_REVIEW_COUNT:
        risk.append('Recent missed-payment history warrants investigation')
    return affordability, risk


def review_result(outcome, reasons, *, score, threshold, missing_fields=()):
    """Build the advisory result, which always requires human review."""
    return {
        'outcome': outcome,
        'reason': '; '.join(reasons),
        'reasons': reasons,
        'score': score,
        'threshold': threshold,
        'missing_fields': list(missing_fields),
        'status': 'HUMAN REVIEW REQUIRED',
    }


def advisory_decision(score, application, *, threshold):
    """Route a complete scored application using an explicit threshold."""
    score = validate_score(score)
    threshold = validate_threshold(threshold)
    validate_application_fields(application, REQUIRED_FIELDS)
    affordability, risk = collect_rule_reasons(
        application, score=score, threshold=threshold
    )
    if affordability:
        outcome = 'AFFORDABILITY_REVIEW'
    elif risk:
        outcome = 'ENHANCED_RISK_REVIEW'
    else:
        outcome = 'STANDARD_REVIEW'
    reasons = affordability + risk or ['No configured escalation condition triggered']
    return review_result(outcome, reasons, score=score, threshold=threshold)
