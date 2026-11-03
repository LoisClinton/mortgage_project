import math
from numbers import Real

MAX_STANDARD_DTI = 0.45
MAX_STANDARD_LTV_PCT = 90.0
MISSED_PAYMENT_REVIEW_COUNT = 2
LOWER_REVIEW_THRESHOLD = 0.25
HIGHER_REVIEW_THRESHOLD = 0.50
REQUIRED_FIELDS = (
    'credit_score', 'debt_to_income_ratio',
    'missed_payments_24m', 'loan_to_value_pct',
)

def validate_application_fields(application, required_fields):
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
            value < 0 or value > 24 or int(value) != value
        ):
            invalid.append(field)
        elif field == 'loan_to_value_pct' and not 0 < value <= 150:
            invalid.append(field)
    if invalid:
        raise ValueError(f'Missing or invalid fields: {invalid}')
    return True

def validate_score(score):
    if isinstance(score, bool) or not isinstance(score, Real):
        raise ValueError('Model score must be numeric')
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError('Model score must be finite and between 0 and 1')
    return float(score)

def advisory_decision(score, application, threshold=HIGHER_REVIEW_THRESHOLD):
    score = validate_score(score)
    threshold = validate_score(threshold)
    if not 0 < threshold <= 1:
        raise ValueError('Threshold must be greater than zero')
    validate_application_fields(application, REQUIRED_FIELDS)

    reasons = []
    if application['debt_to_income_ratio'] > MAX_STANDARD_DTI:
        reasons.append('DTI exceeds illustrative affordability review boundary')
    if application['loan_to_value_pct'] > MAX_STANDARD_LTV_PCT:
        reasons.append('LTV exceeds illustrative affordability review boundary')

    if reasons:
        outcome = 'AFFORDABILITY_REVIEW'
    else:
        if score >= threshold:
            reasons.append('Model score meets selected risk-review threshold')
        if application['missed_payments_24m'] >= MISSED_PAYMENT_REVIEW_COUNT:
            reasons.append('Recent missed-payment history warrants investigation')
        outcome = 'ENHANCED_RISK_REVIEW' if reasons else 'STANDARD_REVIEW'
    if not reasons:
        reasons.append('No configured escalation condition triggered')
    return {
        'outcome': outcome, 
        'reason': '; '.join(reasons),
        'reasons': reasons, 
        'score': score, 
        'threshold': threshold,
        'status': 'HUMAN REVIEW REQUIRED',
    }