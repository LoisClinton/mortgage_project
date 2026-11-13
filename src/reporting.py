"""Save final-test evidence from the selected model's evaluation result."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

REPORTS_DIR = Path(__file__).resolve().parents[1] / 'reports'


def save_final_test_evidence(result, *, features, threshold, output_dir=REPORTS_DIR):
    if result is None:
        raise ValueError('Final-test evaluation must be enabled before reporting')
    output_dir = Path(output_dir)
    figure_file = output_dir / 'figures' / 'selected_model_final_test_confusion_matrix.png'
    metrics_file = output_dir / 'selected_model_final_test_metrics.json'
    figure_file.parent.mkdir(parents=True, exist_ok=True)
    matrix = result['confusion_matrix']
    evidence = {
        'partition': 'final_test', 'sample_count': int(matrix.sum()),
        'features': list(features), 'threshold': float(threshold),
        'metrics': {key: value.tolist() if key == 'confusion_matrix' else float(value)
                    for key, value in result.items()},
    }
    metrics_file.write_text(json.dumps(evidence, indent=2) + '\n')
    figure, axis = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay(
        matrix, display_labels=['No difficulty (0)', 'Difficulty (1)']
    ).plot(ax=axis, cmap='Blues', colorbar=False, values_format='d')
    axis.set_title(
        f'Selected model — final test (n={matrix.sum()})\nThreshold {threshold:.2f}'
    )
    figure.tight_layout()
    figure.savefig(figure_file, dpi=180)
    plt.close(figure)
    return metrics_file, figure_file
