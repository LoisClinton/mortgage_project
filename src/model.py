"""Build and evaluate comparable mortgage feature-set experiments."""
from pathlib import Path
import joblib
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, precision_score, recall_score,
    f1_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src.data import TARGET

BASELINE_FEATURES = ['credit_score', 'debt_to_income_ratio',]
EXTENDED_FEATURES = BASELINE_FEATURES + ['missed_payments_24m']

MODEL_FILE = Path(__file__).resolve().parents[1] / 'models' / 'baseline_model.joblib'

# three-way split: 64% training + 16% validation + 20% final test.
TRAIN_SIZE = 0.64
VALIDATION_SIZE = 0.16
FINAL_TEST_SIZE = 0.20

# fixed seed makes random partitions repeatable.
RANDOM_STATE = 42


def build_pipeline():
    """Create, but do not fit, the preprocessing and model pipeline."""
    return make_pipeline(
        SimpleImputer(strategy='median'), # calculate each feature's median and use it to replace missing values.
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=RANDOM_STATE), # logistic regression learns the relationship between the features and the binary target (produces classes and class-1 scores).
    )


def evaluate(model, X_test, y_test):
    """Calculate classification metrics for data not used to fit ``model``."""
    # convert scores into class labels using the model's default classification threshold.
    predicted = model.predict(X_test)
    # return one column per class.
    scores = model.predict_proba(X_test)[:, 1]
    return {
        'accuracy': accuracy_score(y_test, predicted), # proportion of all predictions that are correct.
        'precision_1': precision_score(y_test, predicted, zero_division=0), # proportion of predicted class-1 that are correct.
        'recall_1': recall_score(y_test, predicted, zero_division=0), # proportion of actual class-1 that are found.
        'f1_1': f1_score(y_test, predicted, zero_division=0), # combines precision and recall into one measure.
        'roc_auc': roc_auc_score(y_test, scores), # assesses ranking across possible thresholds rather than only the default threshold used by predict().
        'confusion_matrix': confusion_matrix(y_test, predicted, labels=[0, 1]), # rows are actual classes [0, 1] columns are predicted classes [0, 1].
    }

def split_data_three_way(df, features=BASELINE_FEATURES):
    """Create reproducible 64% training, 16% validation and 20% test sets."""
    # fail if configured proportions are changed incorrectly.
    if not abs(TRAIN_SIZE + VALIDATION_SIZE + FINAL_TEST_SIZE - 1.0) < 1e-12:
        raise ValueError('Split proportions must sum to 1.0')

    X = df[features].copy() # contains only the requested model inputs.
    y = df[TARGET] # contains the future outcome the model is trying to predict.

    # reserve the final test set.
    X_train_and_validation, X_final_test, y_train_and_validation, y_final_test = (
        train_test_split(
            X,
            y,
            test_size=FINAL_TEST_SIZE,
            stratify=y,
            random_state=RANDOM_STATE,
        )
    )

    # first split leaves 80% for training plus validation. make validation equal to 16% of the full dataset 16/80 = 20%.
    validation_share = VALIDATION_SIZE / (TRAIN_SIZE + VALIDATION_SIZE)

    # split remaining records into the final training and validation sets. stratify keeps the class-0/class-1 balance similar in each partition.
    X_train, X_validation, y_train, y_validation = train_test_split(
        X_train_and_validation,
        y_train_and_validation,
        test_size=validation_share,
        stratify=y_train_and_validation,
        random_state=RANDOM_STATE,
    )

    return (
        X_train,
        X_validation,
        X_final_test,
        y_train,
        y_validation,
        y_final_test,
    )


def run_model(df, features, model_file=None):
    """Fit one feature set and evaluate it on validation and final-test data.

    The same split proportions and random state are used for every feature set,
    allowing a controlled comparison between the baseline and an extension.
    """
    # for 800 records these partitions contain 512, 128 and 160 rows.
    (
        X_train,
        X_validation,
        X_final_test,
        y_train,
        y_validation,
        y_final_test,
    ) = split_data_three_way(df, features)

    # reference always predicts the most common class.
    reference = DummyClassifier(strategy='most_frequent')
    reference.fit(X_train, y_train)

    # build and fit the complete imputation -> scaling -> logistic regression workflow using training records only.
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_FILE) # save the fitted pipeline so applicant_example.py can use the same preprocessing and model.

    # validation results
    validation_reference_results = evaluate(reference, X_validation, y_validation) # Dummy classifier
    validation_results = evaluate(pipeline, X_validation, y_validation) # Logistic regression pipeline

    # final test is evaluated after model choices.
    final_reference_results = evaluate(reference, X_final_test, y_final_test) # Dummy classifier
    final_results = evaluate(pipeline, X_final_test, y_final_test) # Logistic regression pipeline

    return {
        'features': features,
        'validation_reference': validation_reference_results,
        'validation': validation_results,
        'final_reference': final_reference_results,
        'final': final_results,
    }


def run_baseline(df):
    """Run the baseline experiment and save its fitted pipeline."""
    results = run_model(df, BASELINE_FEATURES, MODEL_FILE)
    return (
        results['final_reference'],
        results['validation_reference'],
        results['validation'],
        results['final'],
    )