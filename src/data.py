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
    # Count total unique applications.
    total_applications = df['application_id'].nunique()

    # Summarize missing values for each column.
    missing_summary = pd.DataFrame({
    "Missing Count": df.isna().sum(),
    "Missing %": (df.isna().mean() * 100).round(1),
    })
    missing_summary = missing_summary[missing_summary["Missing Count"] > 0]

    # Count total missing cells and applications with missing values.
    missing_cell_count = int(df.isna().sum().sum())
    applications_with_missing = int(df.loc[df.isna().any(axis=1), 'application_id'].nunique())

    # Calculate the percentage of applications with missing values.
    missing_application_pct = applications_with_missing / total_applications * 100

    # Print the audit.
    print('\n ------------ START OF AUDIT ------------')
    print('Rows and columns:', df.shape)
    print('TOTAL UNIQUE APPLICATIONS:', total_applications)
    print('\nDATA TYPES:\n', df.dtypes.to_string())
    print('\nMISSING VALUES:\n', df.isna().sum().to_string())
    print('\nMISSING VALUES SUMMARY:\n', missing_summary.to_string())
    print(f'\nTotal missing cells: {missing_cell_count} across {applications_with_missing} distinct applications ({missing_application_pct:.1f}%)')
    print('\nTARGET DISTRIBUTION AND PERCENTAGES:')
    print('\nTarget distribution:\n', df[TARGET].value_counts().sort_index().to_string())
    print('Target percentages:\n', (df[TARGET].value_counts(normalize=True).sort_index() * 100).round(1).to_string())
    print('\nDuplicate application IDs:', df['application_id'].duplicated().sum())
    print('Duplicate entire records:', df.duplicated().sum())
    print('\nSelected numeric ranges:')
    for field in ('credit_score', 'debt_to_income_ratio', 'loan_to_value_pct', 'missed_payments_24m'):
        print(f'  {field}: min={df[field].min()}, max={df[field].max()}')
    print('\n ------------ END OF AUDIT ------------')


if __name__ == '__main__':
    print_audit(load_data())