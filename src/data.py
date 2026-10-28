"""Read the synthetic mortgage data and print an explicit preparation audit."""
from pathlib import Path
import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[1] / 'data' / 'mortgage_data.csv'
TARGET = 'repayment_difficulty_12m'


def load_data(path=DATA_FILE):
    path = Path(path)

    # Ensure the file exists before attempting to read it.
    if not path.is_file():
        raise FileNotFoundError(f'Mortgage dataset not found: {path}')

    # Read the CSV file into a DataFrame.
    df = pd.read_csv(path)

    # Ensure required columns are present and the TARGET is valid.
    missing = {'application_id', TARGET} - set(df.columns)
    if missing:
        raise ValueError(f'Required columns missing: {sorted(missing)}')
    if df[TARGET].isna().any() or not set(df[TARGET].unique()).issubset({0, 1}):
        raise ValueError('Expected a complete binary repayment_difficulty_12m target')
    return df


def print_audit(df):
    # Create a copy of the DataFrame to perform checks without modifying the original.
    checks = df.copy()

    # Count total unique applications.
    total_applications = checks['application_id'].nunique()

    # Summarize missing values for each column.
    missing_summary = pd.DataFrame({
    "Missing Count": checks.isna().sum(),
    "Missing %": (checks.isna().mean() * 100).round(1),
    })
    missing_summary = missing_summary[missing_summary["Missing Count"] > 0]

    # Count total missing cells and applications with missing values.
    missing_cell_count = int(checks.isna().sum().sum())
    applications_with_missing = int(checks.loc[checks.isna().any(axis=1), 'application_id'].nunique())

    # Calculate the percentage of applications with missing values.
    missing_application_pct = applications_with_missing / total_applications * 100

    # Compare requested loan with property value minus deposit.
    checks["expected_loan_gbp"] = (
        checks["property_value_gbp"] - checks["deposit_gbp"]
    )
    checks["loan_difference_gbp"] = (
        checks["requested_loan_gbp"] - checks["expected_loan_gbp"]
    )
    # Allow £1 for rounding or recording precision.
    loan_mismatches = checks.loc[
        checks["loan_difference_gbp"].abs() > 1.0,
        [
            "application_id",
            "requested_loan_gbp",
            "property_value_gbp",
            "deposit_gbp",
            "expected_loan_gbp",
            "loan_difference_gbp",
        ],
    ]

    # Compare recorded LTV with LTV calculated from loan and property value.
    valid_property_value = checks["property_value_gbp"] > 0
    checks["calculated_ltv_pct"] = float("nan")
    checks.loc[valid_property_value, "calculated_ltv_pct"] = (
        checks.loc[valid_property_value, "requested_loan_gbp"]
        / checks.loc[valid_property_value, "property_value_gbp"]
        * 100
    )
    checks["ltv_difference_percentage_points"] = (
        checks["loan_to_value_pct"] - checks["calculated_ltv_pct"]
    )
    # Allow a small difference for rounding (tolerance is in percentage points).
    ltv_mismatches = checks.loc[
        checks["ltv_difference_percentage_points"].abs() > 0.02,
        [
            "application_id",
            "loan_to_value_pct",
            "calculated_ltv_pct",
            "ltv_difference_percentage_points",
        ]
    ]

    # Print the audit.
    print('\n ------------ START OF AUDIT ------------')
    print('Rows and columns:', checks.shape)
    print('TOTAL UNIQUE APPLICATIONS:', total_applications)
    print('\nDATA TYPES:\n', checks.dtypes.to_string())
    print('\nMISSING VALUES:\n', checks.isna().sum().to_string())
    print('\nMISSING VALUES SUMMARY:\n', missing_summary.to_string())
    print(f'\nTotal missing cells: {missing_cell_count} across {applications_with_missing} distinct applications ({missing_application_pct:.1f}%)')
    print('\nTARGET DISTRIBUTION AND PERCENTAGES:')
    print('\nTarget distribution:\n', checks[TARGET].value_counts().sort_index().to_string())
    print('Target percentages:\n', (checks[TARGET].value_counts(normalize=True).sort_index() * 100).round(1).to_string())
    print('\nDuplicate application IDs:', checks['application_id'].duplicated().sum())
    print('Duplicate entire records:', checks.duplicated().sum())
    print('\nSelected numeric ranges:')
    for field in ('credit_score', 'debt_to_income_ratio', 'loan_to_value_pct', 'missed_payments_24m'):
        print(f'  {field}: min={checks[field].min()}, max={checks[field].max()}')
    print('\nCHECK FOR INCONSISTENCIES OR CONTRADICTIONS')
    print("\nLoan / property / deposit inconsistencies (> £1):")
    print(loan_mismatches.to_string(index=False))
    print("\nRecorded / calculated LTV inconsistencies (> 0.02 percentage points):")
    print(ltv_mismatches.to_string(index=False))
    print('\n ------------ END OF AUDIT ------------')


if __name__ == '__main__':
    print_audit(load_data())