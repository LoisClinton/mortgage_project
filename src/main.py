from src.data import load_data, print_audit
from src.model import (
    BASELINE_FEATURES,
    EXTENDED_FEATURES,
    FINAL_TEST_SIZE,
    MODEL_FILE,
    TRAIN_SIZE,
    VALIDATION_SIZE,
    run_model,
)

# print evaluation metrics and confusion matrix for model run.
def report(name, result):
    print(f'\n{name}')
    for metric in (
        'accuracy',
        'precision_1',
        'recall_1',
        'f1_1',
        'roc_auc',
        'average_precision',
    ):
        print(f'{metric}: {result[metric]:.3f}')
    print('Confusion matrix \n[actual rows 0,1; predicted columns 0,1]:')
    print(result['confusion_matrix'])

# entry point for running the model and reporting results.
def main():
    df = load_data() 
    print_audit(df) # print dataset audit

    baseline_results = run_model(df, BASELINE_FEATURES, MODEL_FILE)
    extended_results = run_model(df, EXTENDED_FEATURES)
    print('\nSelected baseline features:', BASELINE_FEATURES)
    print('Extended features:', EXTENDED_FEATURES)
    print(
        '\nThree-way split: '
        f'training={TRAIN_SIZE:.0%}, '
        f'validation={VALIDATION_SIZE:.0%}, '
        f'final test={FINAL_TEST_SIZE:.0%}'
    )
    
    report('\n## Majority-class reference on validation:', baseline_results['validation_reference'])
    report('\n## Two-feature baseline on validation:', baseline_results['validation'])
    report('\n## Extended model on validation:', extended_results['validation'])
    # report('\n## Two-feature baseline on final test:', baseline_results['final'])
    # report('\n## Extended model on final test:', extended_results['final'])
    print(f'\n ~~ Trained baseline saved: ~~\n {MODEL_FILE}')


if __name__ == '__main__':
    main()
