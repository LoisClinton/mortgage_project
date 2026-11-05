import joblib
import pandas as pd

from src.model import MODEL_FILE, SELECTED_FEATURES, SELECTED_THRESHOLD
from src.decisions import validate_application_fields, validate_score, advisory_decision

EXAMPLE_APPLICATION = {
    "credit_score": 680,
    "debt_to_income_ratio": 0.32,
    "missed_payments_24m": 0,
    "previous_default_flag": 0,
    "loan_to_value_pct": 80.0,
}


def score_example(application):
    validate_application_fields(application, SELECTED_FEATURES)
    row = pd.DataFrame([application], columns=SELECTED_FEATURES)
    if not MODEL_FILE.is_file():
        raise FileNotFoundError(
            "No trained model: first run python -m src.main"
        )
    
    # Load the locally generated model artefact.
    model = joblib.load(MODEL_FILE)
    score = model.predict_proba(row)[0, 1]
    return validate_score(float(score))


def main():
    score = score_example(EXAMPLE_APPLICATION)
    print("\n______MORTGAGE APPLICATION ASSESSMENT______")
    print("Applicant details:")
    print(f"credit_score={EXAMPLE_APPLICATION['credit_score']}")
    print(f"debt_to_income_ratio={EXAMPLE_APPLICATION['debt_to_income_ratio']:.2f}")
    print(f"missed_payments_24m={EXAMPLE_APPLICATION['missed_payments_24m']}")
    print(f"previous_default_flag={EXAMPLE_APPLICATION['previous_default_flag']}")
    print(f"loan_to_value_pct={EXAMPLE_APPLICATION['loan_to_value_pct']:.1f}")
    print(f"Repayment-difficulty class-1 score: {score:.3f}")
    print("\n______DECISION______")
    decision = advisory_decision(
        score,
        EXAMPLE_APPLICATION,
        threshold=SELECTED_THRESHOLD,
    )
    print(f"Model Classification Threshold: {decision['threshold']:.3f}")
    print(f"Model Score: {decision['score']:.3f}")
    print(f"Advisory outcome: {decision['outcome']}")
    print(f"Reason: {decision['reason']}")
    print(f"Status: {decision['status']}")
    print("\n______END OF DECISION______\n")


if __name__ == "__main__":
    main()
