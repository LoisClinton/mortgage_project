"""Explore classification thresholds using validation data."""

from src.data import load_data
from src.model import (
    BASELINE_FEATURES,
    EXTENDED_FEATURES,
    build_pipeline,
    split_data_three_way,
    threshold_analysis,
)

def main():
    df = load_data()

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

        for item in threshold_analysis(
            model, X_validation, y_validation
        ):
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

if __name__ == "__main__":
    main()