"""Run the supplied baseline only; assessed advisory rules are NOT provided."""
from src.data import load_data, print_audit
from src.model import (
    BASELINE_FEATURES,
    FINAL_TEST_SIZE,
    MODEL_FILE,
    TRAIN_SIZE,
    VALIDATION_SIZE,
    run_baseline,
)

# print evaluation metrics and confusion matrix for model run.
def report(name, result):
    print(f'\n{name}')
    for metric in ('accuracy', 'precision_1', 'recall_1', 'f1_1', 'roc_auc'):
        print(f'{metric}: {result[metric]:.3f}')
    print('Confusion matrix \n[actual rows 0,1; predicted columns 0,1]:')
    print(result['confusion_matrix'])

# entry point for running the model and reporting results.
def main():
    df = load_data() 
    print_audit(df) # print dataset audit

    final_reference_results, validation_reference_results, validation_results, final_results = run_baseline(df)
    print('\nSelected baseline features:', BASELINE_FEATURES)
    print(
        '\nThree-way split: '
        f'training={TRAIN_SIZE:.0%}, '
        f'validation={VALIDATION_SIZE:.0%}, '
        f'final test={FINAL_TEST_SIZE:.0%}'
    )
    
    report('\n## Majority-class reference on validation:', validation_reference_results)
    report('\n## Two-feature baseline on validation:', validation_results)
    # report('\n## Majority-class reference on final test:', final_reference_results)
    # report('\n# Two-feature baseline on final test:', final_results)
    print(f'\n ~~ Trained baseline saved: ~~\n {MODEL_FILE}')


if __name__ == '__main__':
    main()
