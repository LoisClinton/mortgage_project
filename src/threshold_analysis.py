"""Explore classification thresholds using validation data."""

from pathlib import Path

import matplotlib.pyplot as plt
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

from src.data import load_data
from src.model import (
    BASELINE_FEATURES,
    EXTENDED_FEATURES_VER_1,
    EXTENDED_FEATURES_VER_2,
    SELECTED_THRESHOLD,
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
ROC_FIGURE_FILE = FIGURE_FILE.parent / "model_comparison_roc.png"
PR_FIGURE_FILE = FIGURE_FILE.parent / "model_comparison_precision_recall.png"
METRICS_FIGURE_FILE = FIGURE_FILE.parent / "model_comparison_metrics.png"
RANKING_METRICS_FIGURE_FILE = (
    FIGURE_FILE.parent / "model_comparison_roc_auc_average_precision.png"
)
CONFUSION_FIGURE_FILE = (
    FIGURE_FILE.parent / "validation_confusion_matrices.png"
)
ERROR_COUNTS_FIGURE_FILE = (
    FIGURE_FILE.parent / "model_comparison_false_positives_negatives.png"
)
MODEL_ERROR_FIGURE_PREFIX = FIGURE_FILE.parent / "errors_"


def plot_threshold_metrics(results_by_model):
    """Save validation precision and recall against each tested threshold."""
    FIGURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    figure, axis = plt.subplots(figsize=(8, 5))
    for label, records in results_by_model.items():
        i = list(results_by_model.keys()).index(label)
        base_color = colors[i % len(colors)]
        thresholds = [item["threshold"] for item in records]
        precision = [item["precision"] for item in records]
        recall = [item["recall"] for item in records]
        axis.plot(thresholds, precision, marker="d", ms=4, color=base_color, label=f"{label} precision")
        axis.plot(thresholds, recall, marker="d", ms=4, linestyle="--", color=base_color, alpha=0.7, label=f"{label} recall")

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


def plot_roc_curves(validation_models):
    """Save validation ROC curves for each candidate model."""
    figure, axis = plt.subplots(figsize=(8, 5))

    for label, (model, X_validation, y_validation) in validation_models.items():
        scores = model.predict_proba(X_validation)[:, 1]
        false_positive_rate, true_positive_rate, _ = roc_curve(
            y_validation, scores
        )
        axis.plot(
            false_positive_rate,
            true_positive_rate,
            label=f"{label} (AUC={roc_auc_score(y_validation, scores):.3f})",
        )

    axis.plot([0, 1], [0, 1], linestyle=":", color="grey", label="Random classifier")
    axis.set(
        title="Validation ROC curves by model",
        xlabel="False-positive rate",
        ylabel="True-positive rate (recall)",
        xlim=(0, 1),
        ylim=(0, 1.05),
    )
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(ROC_FIGURE_FILE, dpi=150)
    plt.close(figure)


def plot_precision_recall_curves(validation_models):
    """Save validation precision-recall curves for each candidate model."""
    figure, axis = plt.subplots(figsize=(8, 5))

    for label, (model, X_validation, y_validation) in validation_models.items():
        scores = model.predict_proba(X_validation)[:, 1]
        precision, recall, _ = precision_recall_curve(y_validation, scores)
        axis.plot(
            recall,
            precision,
            label=(
                f"{label} "
                f"(AP={average_precision_score(y_validation, scores):.3f})"
            ),
        )

    axis.set(
        title="Validation precision-recall curves by model",
        xlabel="Recall",
        ylabel="Precision",
        xlim=(0, 1),
        ylim=(0, 1.05),
    )
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(PR_FIGURE_FILE, dpi=150)
    plt.close(figure)


def plot_ranking_metrics(validation_models):
    """Save validation ROC-AUC and average-precision comparisons."""
    labels = list(validation_models)
    roc_auc_values = []
    average_precision_values = []

    for model, X_validation, y_validation in validation_models.values():
        scores = model.predict_proba(X_validation)[:, 1]
        roc_auc_values.append(roc_auc_score(y_validation, scores))
        average_precision_values.append(
            average_precision_score(y_validation, scores)
        )

    figure, axis = plt.subplots(figsize=(9, 5))
    positions = range(len(labels))
    width = 0.35
    axis.bar(
        [position - width / 2 for position in positions],
        roc_auc_values,
        width=width,
        label="ROC-AUC",
    )
    axis.bar(
        [position + width / 2 for position in positions],
        average_precision_values,
        width=width,
        label="Average precision (AP)",
    )
    axis.set(
        title="Validation ROC-AUC and average precision by model",
        ylabel="Score",
        ylim=(0, 1.05),
        xticks=list(positions),
        xticklabels=labels,
    )
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(RANKING_METRICS_FIGURE_FILE, dpi=150)
    plt.close(figure)


def plot_confusion_matrices(models):
    """Save confusion matrices for each model on validation data."""
    figure, axes = plt.subplots(
        1,
        len(models),
        figsize=(14, 4.5),
        squeeze=False,
        constrained_layout=True,
    )
    axes = axes[0]

    for axis, (label, (model, X_validation, y_validation)) in zip(
        axes, models.items()
    ):
        scores = model.predict_proba(X_validation)[:, 1]
        predicted = (scores >= SELECTED_THRESHOLD).astype(int)
        matrix = confusion_matrix(
            y_validation,
            predicted,
            labels=[0, 1],
        )
        image = axis.imshow(matrix, cmap="magma", vmin=0)
        axis.set(
            title=label,
            xlabel="Predicted class",
            ylabel="Actual class",
            xticks=[0, 1],
            yticks=[0, 1],
            xticklabels=["No difficulty (0)", "Difficulty (1)"],
            yticklabels=["No difficulty (0)", "Difficulty (1)"],
        )
        for row in range(2):
            for column in range(2):
                axis.text(
                    column,
                    row,
                    str(matrix[row, column]),
                    ha="center",
                    va="center",
                    color="black" if matrix[row, column] > matrix.max() / 2 else "white",
                    fontsize=14,
                )

    figure.suptitle(
        "Validation confusion matrices "
        f"(classification threshold {SELECTED_THRESHOLD:.2f})"
    )
    figure.colorbar(image, ax=axes, fraction=0.025, pad=0.04)
    figure.savefig(CONFUSION_FIGURE_FILE, dpi=150)
    plt.close(figure)


def plot_model_metrics(results_by_model):
    """Save selected-threshold validation metrics for each candidate model."""
    metric_names = ("precision", "recall", "f1", "accuracy")
    labels = list(results_by_model)
    values = {
        metric: [
            next(
                item[metric]
                for item in results_by_model[label]
                if item["threshold"] == SELECTED_THRESHOLD
            )
            for label in labels
        ]
        for metric in metric_names
    }

    figure, axis = plt.subplots(figsize=(9, 5))
    positions = range(len(labels))
    width = 0.2
    for offset, metric in enumerate(metric_names):
        axis.bar(
            [position + (offset - 1.5) * width for position in positions],
            values[metric],
            width=width,
            label=metric.capitalize(),
        )

    axis.set(
       title=(
           "Validation metrics at classification "
           f"threshold {SELECTED_THRESHOLD:.2f}"
       ),
       ylabel="Score",
       ylim=(0, 1.05),
       xticks=list(positions),
       xticklabels=labels,
    )
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(METRICS_FIGURE_FILE, dpi=150)
    plt.close(figure)


def plot_error_counts(results_by_model):
    """Save validation false-positive and false-negative counts by threshold."""
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)

    for index, (label, records) in enumerate(results_by_model.items()):
        color = colors[index % len(colors)]
        thresholds = [item["threshold"] for item in records]
        false_positives = [item["fp"] for item in records]
        false_negatives = [item["fn"] for item in records]
        axes[0].plot(
            thresholds,
            false_positives,
            marker="o",
            color=color,
            label=label,
        )
        axes[1].plot(
            thresholds,
            false_negatives,
            marker="o",
            color=color,
            label=label,
        )

    axes[0].set_title("False positives")
    axes[1].set_title("False negatives")
    for axis in axes:
        axis.set_xlabel("Classification threshold")
        axis.set_xticks(thresholds)
        axis.grid(alpha=0.3)
        axis.legend()
    axes[0].set_ylabel("Number of validation applications")
    figure.suptitle("Validation error counts by model and threshold")
    figure.tight_layout()
    figure.savefig(ERROR_COUNTS_FIGURE_FILE, dpi=150)
    plt.close(figure)


def plot_individual_error_counts(results_by_model):
    """Save a screenshot-style false-positive/false-negative graph per model."""
    figure_files = []
    maximum_error_count = max(
        max(item["fp"], item["fn"])
        for records in results_by_model.values()
        for item in records
    )
    shared_y_limit = maximum_error_count + 5

    for label, records in results_by_model.items():
        thresholds = [item["threshold"] for item in records]
        false_positives = [item["fp"] for item in records]
        false_negatives = [item["fn"] for item in records]
        safe_label = (
            label.lower()
            .replace(" ", "_")
            .replace("-", "_")
        )
        figure_file = MODEL_ERROR_FIGURE_PREFIX.parent / (
            f"{MODEL_ERROR_FIGURE_PREFIX.name}{safe_label}.png"
        )

        figure, axis = plt.subplots(figsize=(9, 5))
        axis.plot(
            thresholds,
            false_positives,
            marker="o",
            linewidth=2,
            label="False positives",
        )
        axis.plot(
            thresholds,
            false_negatives,
            marker="o",
            linewidth=2,
            label="False negatives",
        )
        axis.set(
            title=f"{label}: false positives vs false negatives",
            xlabel="Classification threshold",
            ylabel="Number of validation applications",
            xticks=thresholds,
            ylim=(0, shared_y_limit),
        )
        axis.grid(axis="y", alpha=0.25, linestyle="--")
        axis.legend()
        figure.tight_layout()
        figure.savefig(figure_file, dpi=150)
        plt.close(figure)
        figure_files.append(figure_file)

    return figure_files


def main():
    """Print the threshold tables and save all comparison graphs."""
    df = load_data()
    results_by_model = {}
    validation_models = {}

    for label, features in (
        ("Two-feature baseline", BASELINE_FEATURES),
        ("Three-feature Extended ver 1", EXTENDED_FEATURES_VER_1),
        ("Four-feature Extended ver 2", EXTENDED_FEATURES_VER_2),
    ):
        (
            X_train,
            X_validation,
            X_final_test,
            y_train,
            y_validation,
            y_final_test,
        ) = split_data_three_way(df, features)

        model = build_pipeline()
        model.fit(X_train, y_train)
        validation_models[label] = (model, X_validation, y_validation)

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
    plot_roc_curves(validation_models)
    plot_precision_recall_curves(validation_models)
    plot_ranking_metrics(validation_models)
    plot_confusion_matrices(validation_models)
    plot_model_metrics(results_by_model)
    plot_error_counts(results_by_model)
    individual_error_figure_files = plot_individual_error_counts(
        results_by_model
    )
    for figure_file in (
        FIGURE_FILE,
        ROC_FIGURE_FILE,
        PR_FIGURE_FILE,
        RANKING_METRICS_FIGURE_FILE,
        CONFUSION_FIGURE_FILE,
        METRICS_FIGURE_FILE,
        ERROR_COUNTS_FIGURE_FILE,
        *individual_error_figure_files,
    ):
        print(f"\nGraph saved to: {figure_file}")

if __name__ == "__main__":
    main()