"""Explore classification thresholds using validation data."""

from pathlib import Path

import matplotlib.pyplot as plt

from src.data import load_data
from src.model import (
    BASELINE_FEATURES,
    EXTENDED_FEATURES,
    build_pipeline,
    split_data_three_way,
    threshold_analysis,
)


FIGURE_FILE = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "figures"
    / "threshold_precision_recall.png"
)


def plot_threshold_metrics(results_by_model):
    """Save validation precision and recall against each tested threshold."""
    FIGURE_FILE.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(8, 5))
    for label, records in results_by_model.items():
        thresholds = [item["threshold"] for item in records]
        precision = [item["precision"] for item in records]
        recall = [item["recall"] for item in records]
        axis.plot(thresholds, precision, marker="o", label=f"{label} precision")
        axis.plot(thresholds, recall, marker="s", linestyle="--", label=f"{label} recall")

    axis.set(
        title="Validation precision and recall by threshold",
        xlabel="Classification threshold",
        ylabel="Score",
        ylim=(0, 1.05),
    )
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(FIGURE_FILE, dpi=150)
    plt.close(figure)


def main():
    df = load_data()
    results_by_model = {}

    for label, features in (
        ("Two-feature baseline", BASELINE_FEATURES),
        ("Three-feature Extended ver 1", EXTENDED_FEATURES),
    ):
        (
            X_train,
            X_validation,
            _,
            y_train,
            y_validation,
            _,
        ) = split_data_three_way(df, features)

        model = build_pipeline()
        model.fit(X_train, y_train)

        print(f"\n{label} (validation data)")
        print("cutoff   recall  precision   F1    TP   FP   FN   TN")

        results_by_model[label] = threshold_analysis(
            model, X_validation, y_validation
        )

        for item in results_by_model[label]:
            print(
                f"{item['threshold']:.2f}    "
                f"{item['recall']:.3f}    "
                f"{item['precision']:.3f}    "
                f"{item['f1']:.3f}  "
                f"{item['tp']:3d}  "
                f"{item['fp']:3d}  "
                f"{item['fn']:3d}  "
                f"{item['tn']:3d}"
            )

    plot_threshold_metrics(results_by_model)
    print(f"\nGraph saved to: {FIGURE_FILE}")

if __name__ == "__main__":
    main()