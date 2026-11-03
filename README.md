# Mortgage decision-support starter · DN6MD001 Assignment 2

This is a **working, deliberately limited tutor-provided ML baseline**; it is **not a finished Assignment 2 solution**. Read `../START_HERE.md`, `../CODE_WALKTHROUGH.md`, `../DATA_DICTIONARY.md` and the approved brief in the parent folder.

## Quick start

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.data
python -m src.main
python -m src.applicant_example
python -m unittest discover -s tests -v
```

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.data
.\.venv\Scripts\python.exe -m src.main
.\.venv\Scripts\python.exe -m src.applicant_example
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The supplied dataset is already in `data/mortgage_data.csv`. The program uses only **synthetic data**. Do not use real applicant details.

### Automatic development logging

The repository includes a versioned `post-commit` hook that records each completed commit in `DEVELOPMENT_LOG.md`. Enable it once from this folder:

```bash
git config core.hooksPath .githooks
```

After a commit, review the new log row and commit that generated log update **_with_** the next change. The hook records the commit subject, changed files, remote commit link, and the result of the documented validation command. It does not amend commits automatically.

### What is working?

- Data audit (`src/data.py`)
- A reusable Logistic Regression experiment with training-only imputation/scaling, a majority-class reference, and reproducible 64% training, 16% validation and 20% final-test evaluation. It compares the two-feature baseline with justified extensions (`src/model.py`, `src/main.py`)
- Validation threshold analysis with a saved precision/recall graph (`src/threshold_analysis.py`, `reports/figures/threshold_precision_recall.png`)
- Saved model and sample applicant **scoring** (not decision-making) (`src/applicant_example.py`)
- Four generic validation tests (`tests/test_validation.py`)

### What is your independent assignment work?

Develop, justify and test your own logical decision rules and their integration with the model; make evidence-informed modelling/evaluation decisions, carry out meaningful improvement and retesting, document decisions and sources, and maintain Git/GitHub version history. The intentionally incomplete `advisory_decision()` in `src/decisions.py` is not an error in the supplied training/scoring example.

**Version-control and data note:** Synthetic CSV data and generated `.joblib` model files are excluded from Git by default. The tutor has provided the dataset in the assignment pack; explain how to obtain it in your README. Seek permission before putting data into a public repository. Never commit real personal or confidential data or credentials. A reviewer must be able to run the project using the supplied dataset and the documented commands.

**Academic integrity:** Acknowledge module-provided code and any permitted AI assistance under the approved brief. Keep the final report and project evidence consistent.
