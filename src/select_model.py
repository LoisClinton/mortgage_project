"""Select the feature set and threshold using validation data only."""
from src.model import (
    EXTENDED_FEATURES_VER_1,
    EXTENDED_FEATURES_VER_2,
    BASELINE_FEATURES,
    split_data_three_way,
    build_pipeline,
    evaluate,
    threshold_analysis,
)
import pandas as pd

MIN_VALIDATION_RECALL = 0.60


def select_configuration(df):
    """Choose the feature set and threshold using validation data only."""
    candidates = []

    for features in (
        BASELINE_FEATURES,
        EXTENDED_FEATURES_VER_1,
        EXTENDED_FEATURES_VER_2,
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

        validation = evaluate(
            model, X_validation, y_validation
        )

        rows = threshold_analysis(
            model, X_validation, y_validation
        )

        eligible = [
            row for row in rows
            if row["recall"] >= MIN_VALIDATION_RECALL
        ]

        if not eligible:
            raise ValueError(
                f"No cutoff meets the recall objective: {features}"
            )

        selected = max(
            eligible,
            key=lambda row: row["threshold"]
        )

        candidates.append({
            "features": list(features),
            "validation_roc_auc": float(
                validation["roc_auc"]
            ),
            "validation_average_precision": float(
                validation["average_precision"]
            ),
            "threshold": selected["threshold"],
            "validation_at_threshold": selected,
            "threshold_table": rows,
        })

    winner = max(
        candidates,
        key=lambda candidate: (
            candidate["validation_average_precision"],
            -len(candidate["features"])
        )
    )
    return winner, candidates


def print_configuration(label, configuration):
    """Print one candidate configuration with its validation results."""
    selected_metrics = configuration["validation_at_threshold"]
    threshold_table = pd.DataFrame(configuration["threshold_table"])[
        ["threshold", "recall", "precision", "f1", "accuracy", "tp", "fp", "fn", "tn"]
    ].copy()

    print(f"\n{label}")
    print("-" * len(label))
    print("Features: " + ", ".join(configuration["features"]))
    print(
        "Validation ROC-AUC: "
        f"{configuration['validation_roc_auc']:.3f}"
    )
    print(
        "Validation average precision: "
        f"{configuration['validation_average_precision']:.3f}"
    )
    print(f"Selected threshold: {configuration['threshold']:.2f}")
    print("\nPerformance at selected threshold:")
    print(f"  Recall:    {selected_metrics['recall']:.3f}")
    print(f"  Precision: {selected_metrics['precision']:.3f}")
    print(f"  F1:        {selected_metrics['f1']:.3f}")
    print(f"  Accuracy:  {selected_metrics['accuracy']:.3f}")
    print(
        "  Confusion counts: "
        f"TP={selected_metrics['tp']}, "
        f"FP={selected_metrics['fp']}, "
        f"FN={selected_metrics['fn']}, "
        f"TN={selected_metrics['tn']}"
    )
    print("\nThreshold comparison:")
    print(threshold_table.to_string(index=False, float_format=lambda value: f"{value:.3f}"))


def main():
    """Print the selected configuration and the candidate comparison."""
    df = pd.read_csv("data/mortgage_data.csv")
    winner, candidates = select_configuration(df)
    print_configuration("Selected configuration", winner)

    print("\nValidation comparison of candidate models")
    print("-----------------------------------------")
    for candidate in candidates:
        print(
            f"{', '.join(candidate['features'])}: "
            f"ROC-AUC={candidate['validation_roc_auc']:.3f}, "
            f"average precision={candidate['validation_average_precision']:.3f}, "
            f"threshold={candidate['threshold']:.2f}"
        )

if __name__ == "__main__":
    main()