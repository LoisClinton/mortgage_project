# Mortgage decision-support prototype · DN6MD001 Assignment 2

Python proof of concept combining logistic regression with explicit advisory rules. It uses the supplied **synthetic** historical mortgage dataset to estimate repayment difficulty within 12 months. Every advisory outcome requires human review; the system does not approve or decline mortgages.

Repository: https://github.com/LoisClinton/mortgage_project

## Run in VS Code

Open this project folder (the folder containing `requirements.txt`). Verification used Python 3.12.14 and scikit-learn 1.8.0. Install the declared dependencies in an isolated environment and select that environment as the VS Code Python interpreter.

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.data
python -m src.main
python -m src.threshold_analysis
python -m src.select_model
python -m src.applicant_example
python -m unittest discover -s tests -v
```

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.data
.\.venv\Scripts\python.exe -m src.main
.\.venv\Scripts\python.exe -m src.threshold_analysis
.\.venv\Scripts\python.exe -m src.select_model
.\.venv\Scripts\python.exe -m src.applicant_example
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`select_model` prints the feature configuration and threshold selected on validation data. The verified winner matches the frozen `SELECTED_FEATURES` and `SELECTED_THRESHOLD` constants in `src/model.py`; it does not rewrite those constants. `main` trains and saves that frozen configuration, reports candidate validation metrics and evaluates only the selected model on the final test. `threshold_analysis` creates validation comparisons. `applicant_example` demonstrates complete and incomplete applications using the selected model. Regenerate the model locally before scoring; serialized models can be dependency-version sensitive.

## Design and structure

- `src/data.py`: dataset loading and exploratory quality audit.
- `src/model.py`: reproducible stratified splits, training-only median imputation/scaling, logistic regression and metrics.
- `src/select_model.py`: validation-based feature and threshold selection.
- `src/assessment.py`: application validation, missing-information routing and scoring integration.
- `src/decisions.py`: explicit advisory rules and reason collection.
- `src/reporting.py`: final-test metrics and confusion-matrix evidence.
- `src/threshold_analysis.py`: validation plots and threshold comparisons.
- `tests/`: 36 unittest methods, including parameterised risk combinations and missing-field cases.
- `DECISION_LOGIC.md`: design rationale and final implemented rules.
- `DEVELOPMENT_LOG.md`: development history.

Required live fields are `credit_score`, `debt_to_income_ratio`, `missed_payments_24m`, `previous_default_flag` and `loan_to_value_pct`. The first four are model predictors; LTV additionally informs the rules.

Invalid supplied values raise `ValueError`, including when another field is missing. Absent, None or numeric NaN required values route to `INFORMATION_COMPLETION_REVIEW`, with no model loading/scoring and `score=None`. Available risk reasons remain visible. Complete applications use this priority:

1. DTI > 0.45 or LTV > 90: `AFFORDABILITY_REVIEW`.
2. Otherwise score >= selected threshold (0.25) or missed payments >= 2: `ENHANCED_RISK_REVIEW`.
3. Otherwise: `STANDARD_REVIEW`.

All applicable reasons are retained. Several missing fields use the same information-completion route. Every advisory result includes `HUMAN REVIEW REQUIRED`. These boundaries are illustrative project rules, not verified lender policy. Historical training/evaluation uses imputation; incomplete live applications instead request information.

## Evaluation and evidence

The 800 records are split into 512 training, 128 validation and 160 final-test cases. Three feature configurations share the same split and pipeline. Selection uses the highest tested threshold meeting validation recall >= 0.60 for each candidate, then the highest average precision (ties favour fewer features). Four predictors and threshold 0.25 are selected. Final-test results are not used to retune that choice.

| Selected model    | Validation | Final test |
| ----------------- | ---------: | ---------: |
| Accuracy          |      0.734 |      0.681 |
| Precision         |      0.432 |      0.357 |
| Recall            |      0.679 |      0.571 |
| F1                |      0.528 |      0.440 |
| ROC-AUC           |      0.775 |      0.716 |
| Average precision |      0.583 |      0.431 |

Final-test confusion matrix: `[[89, 36], [15, 20]]` (rows actual 0/1; columns predicted 0/1). The model identifies 20 of 35 difficulty cases. Recall falls below the provisional 60% objective. These metrics describe the model flag, not the full advisory workflow, and do not establish calibration, fairness or real-world lending suitability.

Generated evidence:

- `reports/selected_model_final_test_metrics.json`
- `reports/figures/selected_model_final_test_confusion_matrix.png` (160 final-test cases)
- `reports/figures/validation_confusion_matrices.png` (128 validation cases per candidate)
- Other validation figures in `reports/figures/`
- `reports/verification/`: captured test, selection, model, graph and applicant execution logs from 13 November 2026.

All 36 tests passed in verification. Tests cover rule boundaries and priority, all 16 risk combinations, absent/None/NaN inputs, invalid inputs, no scoring of incomplete records, data partitions, model saving and report generation.

## Version Control

### Automatic development logging

The repository includes a versioned `post-commit` hook that records each completed commit in `DEVELOPMENT_LOG.md`. Enable it once from this folder:

```bash
git config core.hooksPath .githooks
```

After a commit, review the new log row and commit that generated log update **_with_** the next change. The hook records the commit subject, changed files, remote commit link, and the result of the documented validation command. It does not amend commits automatically.
