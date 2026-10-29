"""Read the synthetic mortgage data and print an explicit preparation audit."""
from pathlib import Path
import pandas as pd
import numpy as np

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

# Identify statistically unusual numeric predictor values using the IQR method.
def iqr_outlier_summary(df): 
    excluded = {"application_id", TARGET}
    numeric_columns = [
        column
        for column in df.select_dtypes(include="number").columns
        if column not in excluded
        and df[column].nunique(dropna=True) > 2
    ]

    findings = []

    for column in numeric_columns:
        values = df[column].dropna()
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr

        flagged = df.loc[
            (df[column] < lower_fence) | (df[column] > upper_fence),
            ["application_id", column],
        ]

        findings.append({
            "field": column,
            "q1": q1,
            "q3": q3,
            "lower_fence": lower_fence,
            "upper_fence": upper_fence,
            "flagged_count": len(flagged),
        })

    return pd.DataFrame(findings)

# Identify domain validation issues for numeric and binary fields.
def domain_validation_summary(df):
    findings = []

    non_negative_fields = [
        "annual_income_gbp",
        "property_value_gbp",
        "deposit_gbp",
        "requested_loan_gbp",
        "monthly_debt_commitments_gbp",
        "savings_gbp",
        "employment_years",
        "missed_payments_24m",
        "interest_rate_pct",
    ]

    for field in non_negative_fields:
        invalid_count = int((df[field] < 0).sum())
        findings.append({
            "field": field,
            "rule": "value must be >= 0",
            "invalid_count": invalid_count,
        })

    bounded_fields = {
        "loan_to_value_pct": (0, 100),
        "credit_utilisation_pct": (0, 100),
    }

    for field, (lower, upper) in bounded_fields.items():
        invalid_count = int(
            ((df[field] < lower) | (df[field] > upper)).sum()
        )
        findings.append({
            "field": field,
            "rule": f"value must be between {lower} and {upper}",
            "invalid_count": invalid_count,
        })

    binary_fields = [
        "previous_default_flag",
        "repayment_difficulty_12m",
    ]

    for field in binary_fields:
        invalid_count = int(
            (~df[field].isin([0, 1])).sum()
        )
        findings.append({
            "field": field,
            "rule": "value must be 0 or 1",
            "invalid_count": invalid_count,
        })

    return pd.DataFrame(findings)

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

    # Check DTI calculation possibilities
    monthly_income = checks["annual_income_gbp"] / 12
    monthly_debt = checks["monthly_debt_commitments_gbp"]
    loan = checks["requested_loan_gbp"]

    # Hypothesis A: Each applicant's recorded interest rate
    variable_rate_dti = (
        monthly_debt
        + loan * (checks["interest_rate_pct"] / 100) / 12
    ) / monthly_income

    # Hypothesis B: Fixed 4.5% rate
    fixed_4_5_rate_dti = (
        monthly_debt
        + loan * 0.045 / 12
    ) / monthly_income

    # Hypothesis C: Fixed 5% rate
    fixed_5_rate_dti = (
        monthly_debt
        + loan * 0.05 / 12
    ) / monthly_income

    # Hypothesis D: Fixed 5.5% rate
    fixed_5_5_rate_dti = (
        monthly_debt
        + loan * 0.055 / 12
    ) / monthly_income

    # Hypothesis E: Fixed 6% rate
    fixed_6_rate_dti = (
        monthly_debt
        + loan * 0.06 / 12
    ) / monthly_income

    actual = checks["debt_to_income_ratio"]
    dti_tolerance = 0.01
    dti_candidates = {
        "Variable rate": variable_rate_dti,
        "Fixed 4.5% rate": fixed_4_5_rate_dti,
        "Fixed 5% rate": fixed_5_rate_dti,
        "Fixed 5.5% rate": fixed_5_5_rate_dti,
        "Fixed 6% rate": fixed_6_rate_dti,
    }
    dti_comparison = {
        name: {
            "mismatches": int(
                ((candidate - actual).abs() > dti_tolerance).sum()
            ),
            "median_absolute_difference": float(
                (candidate - actual).abs().median()
            ),
        }
        for name, candidate in dti_candidates.items()
    }
    most_likely_dti = min(
        dti_comparison,
        key=lambda name: (
            dti_comparison[name]["mismatches"],
            dti_comparison[name]["median_absolute_difference"],
        ),
    )

    # Check correlations excluding the identifier and outcome
    corr_checks = df.copy() # Different copy of df so that values in 'checks' arent evaluated in correlation analysis
    numeric_features = corr_checks.drop(
        columns=["application_id", "repayment_difficulty_12m"]
    ).select_dtypes(include="number")

    correlation_matrix = numeric_features.corr()

    # Extract each pair only once to avoid duplicate correlation entries
    upper_triangle = correlation_matrix.where(
        np.triu(
            np.ones(correlation_matrix.shape),
            k=1
        ).astype(bool)
    )
    pairs = upper_triangle.stack()

    # Strongest absolute correlations first
    pairs = pairs.sort_values(
        key=lambda values: values.abs(),
        ascending=False
    )

    iqr_checks = df.copy() # Different copy of df for IQR outlier analysis
    iqr_summary = iqr_outlier_summary(iqr_checks) 

    # Perform domain validation on the checks DataFrame
    domain_checks = df.copy() # Different copy of df for domain validation
    validation_summary = domain_validation_summary(domain_checks)


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
    print("\nDTI Hypothesis A (Variable rate) mismatches:")
    print(
        dti_comparison["Variable rate"]["mismatches"],
        f"mismatches (absolute difference > {dti_tolerance})",
    )
    print("\nDTI Hypothesis B (Fixed 4.5% rate) mismatches:")
    print(
        dti_comparison["Fixed 4.5% rate"]["mismatches"],
        f"mismatches (absolute difference > {dti_tolerance})",
    )
    print("\nDTI Hypothesis C (Fixed 5% rate) mismatches:")
    print(
        dti_comparison["Fixed 5% rate"]["mismatches"],
        f"mismatches (absolute difference > {dti_tolerance})",
    )
    print("\nDTI Hypothesis D (Fixed 5.5% rate) mismatches:")
    print(
        dti_comparison["Fixed 5.5% rate"]["mismatches"],
        f"mismatches (absolute difference > {dti_tolerance})",
    )
    print("\nDTI Hypothesis E (Fixed 6% rate) mismatches:")
    print(
        dti_comparison["Fixed 6% rate"]["mismatches"],
        f"mismatches (absolute difference > {dti_tolerance})",
    )
    print("\nMost likely DTI calculation:")
    print(f"- {most_likely_dti}")
    print(
        f"- {dti_comparison[most_likely_dti]['mismatches']} mismatches "
        f"(absolute difference > {dti_tolerance})"
    )
    print(
        "- Median absolute difference: "
        f"{dti_comparison[most_likely_dti]['median_absolute_difference']:.3f}"
    )
    print(
        "CLOSEST tested hypothesis, NOT a confirmed definition of the recorded DTI."
    )
    print('\nCHECK FOR STRONG CORRELATIONs:')
    print('\nTop 20 strongest absolute correlations:')
    print(pairs.head(20))
    print("\nIQR SCREENING:")
    print(iqr_summary.to_string(index=False))
    print("\nDOMAIN VALIDATION:")
    print(
        validation_summary[
            validation_summary["invalid_count"] > 0
        ].to_string(index=False)
    )

    if validation_summary["invalid_count"].sum() == 0:
        print("No domain-invalid values found.")
    print('\n ------------ END OF AUDIT ------------')


if __name__ == '__main__':
    print_audit(load_data())