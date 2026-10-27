"""Run the supplied baseline only; assessed advisory rules are NOT provided."""
from src.data import load_data, print_audit
from src.model import BASELINE_FEATURES, MODEL_FILE, run_baseline

# Helper function to print evaluation metrics and confusion matrix for a model run.
def report(name, result):
    print(f'\n{name}')
    for metric in ('accuracy', 'precision_1', 'recall_1', 'f1_1', 'roc_auc'):
        print(f'{metric}: {result[metric]:.3f}')
    print('Confusion matrix \n[actual rows 0,1; predicted columns 0,1]:')
    print(result['confusion_matrix'])

# Entry point for running the model and reporting results.
def main():
    df = load_data()
    print_audit(df)
    reference_results, baseline_results = run_baseline(df)
    print('\nTutor-selected baseline features:', BASELINE_FEATURES)
    report('\n## Majority-class reference:', reference_results)
    report('\n## Two-feature logistic-regression baseline:', baseline_results)
    print(f'\n ~~ Trained baseline saved: ~~\n {MODEL_FILE}')


if __name__ == '__main__':
    main()
