"""Demonstrate the complete application workflow and missing-information route."""
from src.assessment import assess_application, score_application

EXAMPLE_APPLICATION = {
    "credit_score": 680,
    "debt_to_income_ratio": 0.32,
    "missed_payments_24m": 0,
    "previous_default_flag": 0,
    "loan_to_value_pct": 80.0,
}

# Keep the earlier example name for callers that only want a score.
score_example = score_application


def main():
    """Assess an example complete application and an incomplete one."""
    print("\n______MORTGAGE APPLICATION ASSESSMENT EXAMPLES______")
    examples = {
        "Complete applicant": EXAMPLE_APPLICATION,
        "Missing credit score with observed affordability concern": {
            **EXAMPLE_APPLICATION, "credit_score": None, "debt_to_income_ratio": 0.6,
        },
    }
    for label, application in examples.items():
        decision = assess_application(application)
        print("\n______DECISION______")
        print(f"\n{label}")
        print(f"Applicant: {application}")
        score = decision['score']
        print("Model score: " + ('NOT SCORED' if score is None else f'{score:.3f}'))
        print(f"Threshold: {decision['threshold']:.2f}")
        print(f"Advisory outcome: {decision['outcome']}")
        print(f"Reason: {decision['reason']}")
        print(f"Status: {decision['status']}")
        print("\n______END OF DECISION______\n")


if __name__ == "__main__":
    main()
