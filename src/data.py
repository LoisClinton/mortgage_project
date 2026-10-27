"""Read the synthetic mortgage data and print an explicit preparation audit."""
from pathlib import Path
import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[1] / 'data' / 'mortgage_data.csv'
TARGET = 'repayment_difficulty_12m'


def load_data(path=DATA_FILE):
    """Load records and reject an invalid or incomplete observed target."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Mortgage dataset not found: {path}')
    df = pd.read_csv(path)
    missing = {'application_id', TARGET} - set(df.columns)
    if missing:
        raise ValueError(f'Required columns missing: {sorted(missing)}')
    if df[TARGET].isna().any() or not set(df[TARGET].unique()).issubset({0, 1}):
        raise ValueError('Expected a complete binary repayment_difficulty_12m target')
    return df


def print_audit(df):
    print('\n ------------ START OF AUDIT ------------')
    print('Rows and columns:', df.shape)
    print('\nData types:\n', df.dtypes.to_string())
    print('\nMissing values:\n', df.isna().sum().to_string())
    print('\nTarget distribution:\n', df[TARGET].value_counts().sort_index().to_string())
    print('\nTarget percentages:\n', (df[TARGET].value_counts(normalize=True).sort_index() * 100).round(1).to_string())
    print('\nDuplicate application IDs:', df['application_id'].duplicated().sum())
    print('Duplicate entire records:', df.duplicated().sum())
    print('\nSelected numeric ranges:')
    for field in ('credit_score', 'debt_to_income_ratio', 'loan_to_value_pct', 'missed_payments_24m'):
        print(f'  {field}: min={df[field].min()}, max={df[field].max()}')
    print('\n ------------ END OF AUDIT ------------')


if __name__ == '__main__':
    print_audit(load_data())