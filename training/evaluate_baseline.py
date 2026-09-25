from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from training.dataset_loader import (
    PROJECT_ROOT,
    load_catalog,
    load_manifest,
)
from training.models.bilstm_baseline import (
    BiLSTMBaseline,
)
from training.torch_dataset import (
    SignBridgeDataset,
)


CHECKPOINT_PATH = (
    PROJECT_ROOT
    / "models"
    / "checkpoints"
    / "bilstm_baseline_best.pt"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "training"
    / "evaluation"
)


def safe_div(
    numerator: float,
    denominator: float,
) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def compute_metrics(
    confusion_matrix: np.ndarray,
) -> dict:
    num_classes = (
        confusion_matrix.shape[0]
    )

    total = int(
        confusion_matrix.sum()
    )

    correct = int(
        np.trace(
            confusion_matrix
        )
    )

    accuracy = safe_div(
        correct,
        total,
    )

    per_class = []

    precisions = []
    recalls = []
    f1_scores = []

    for class_id in range(
        num_classes
    ):
        tp = int(
            confusion_matrix[
                class_id,
                class_id,
            ]
        )

        row_total = int(
            confusion_matrix[
                class_id,
                :,
            ].sum()
        )

        column_total = int(
            confusion_matrix[
                :,
                class_id,
            ].sum()
        )

        fn = row_total - tp
        fp = column_total - tp

        precision = safe_div(
            tp,
            tp + fp,
        )

        recall = safe_div(
            tp,
            tp + fn,
        )

        f1 = (
            safe_div(
                2
                * precision
                * recall,
                precision
                + recall,
            )
        )

        class_accuracy = (
            safe_div(
                tp,
                row_total,
            )
        )

        precisions.append(
            precision
        )

        recalls.append(
            recall
        )

        f1_scores.append(
            f1
        )

        per_class.append({
            "class_id":
                class_id,

            "support":
                row_total,

            "correct":
                tp,

            "incorrect":
                fn,

            "accuracy":
                class_accuracy,

            "precision":
                precision,

            "recall":
                recall,

            "f1":
                f1,
        })

    return {
        "accuracy":
            accuracy,

        "macro_precision":
            float(
                np.mean(
                    precisions
                )
            ),

        "macro_recall":
            float(
                np.mean(
                    recalls
                )
            ),

        "macro_f1":
            float(
                np.mean(
                    f1_scores
                )
            ),

        "per_class":
            per_class,
    }


def main() -> int:
    print()
    print(
        "========================================"
    )
    print(
        " SignBridge BiLSTM Evaluation"
    )
    print(
        "========================================"
    )

    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            "Checkpoint not found: "
            f"{CHECKPOINT_PATH}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        f"Device     : {device}"
    )

    if device.type == "cuda":
        print(
            "GPU        : "
            f"{torch.cuda.get_device_name(0)}"
        )

    checkpoint = torch.load(
        CHECKPOINT_PATH,
        map_location=device,
        weights_only=False,
    )

    required_keys = {
        "model_state_dict",
        "num_classes",
        "hidden_size",
        "class_mapping",
        "test_signers",
    }

    missing_keys = (
        required_keys
        -
        set(
            checkpoint.keys()
        )
    )

    if missing_keys:
        raise RuntimeError(
            "Checkpoint missing keys: "
            +
            ", ".join(
                sorted(
                    missing_keys
                )
            )
        )

    num_classes = int(
        checkpoint[
            "num_classes"
        ]
    )

    hidden_size = int(
        checkpoint[
            "hidden_size"
        ]
    )

    checkpoint_mapping = {
        int(class_id):
            sign_id
        for class_id, sign_id
        in checkpoint[
            "class_mapping"
        ].items()
    }

    test_signers = [
        str(value)
        for value
        in checkpoint[
            "test_signers"
        ]
    ]

    print(
        f"Classes    : {num_classes}"
    )

    print(
        f"Hidden size: {hidden_size}"
    )

    print(
        f"Test signer: {test_signers}"
    )

    catalog = load_catalog()

    if (
        len(catalog.signs)
        != num_classes
    ):
        raise RuntimeError(
            "Catalog/checkpoint class count mismatch: "
            f"{len(catalog.signs)} "
            f"vs {num_classes}"
        )

    catalog_by_class = {
        sign.class_id:
            sign
        for sign
        in catalog.signs
    }

    for class_id in range(
        num_classes
    ):
        checkpoint_sign_id = (
            checkpoint_mapping[
                class_id
            ]
        )

        catalog_sign_id = (
            catalog_by_class[
                class_id
            ].sign_id
        )

        if (
            checkpoint_sign_id
            != catalog_sign_id
        ):
            raise RuntimeError(
                "Class mapping mismatch at "
                f"class {class_id}: "
                f"{checkpoint_sign_id} "
                "!= "
                f"{catalog_sign_id}"
            )

    all_records = load_manifest(
        catalog=catalog,
        usable_only=True,
    )

    test_records = [
        record
        for record
        in all_records
        if record.signer_id
        in test_signers
    ]

    if not test_records:
        raise RuntimeError(
            "No test records found "
            "for checkpoint test signer."
        )

    print(
        f"Test samples: {len(test_records)}"
    )

    dataset = SignBridgeDataset(
        test_records
    )

    loader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=False,
        num_workers=0,
        pin_memory=(
            device.type
            ==
            "cuda"
        ),
    )

    model = BiLSTMBaseline(
        num_classes=
            num_classes,

        hidden_size=
            hidden_size,
    ).to(device)

    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )

    model.eval()

    criterion = (
        nn.CrossEntropyLoss(
            reduction="sum"
        )
    )

    confusion_matrix = np.zeros(
        (
            num_classes,
            num_classes,
        ),
        dtype=np.int64,
    )

    prediction_rows = []

    total_loss = 0.0

    record_cursor = 0

    top3_correct = 0

    with torch.no_grad():
        for x, y in loader:
            x = x.to(
                device
            )

            y = y.to(
                device
            )

            logits = model(
                x
            )

            total_loss += float(
                criterion(
                    logits,
                    y,
                ).item()
            )

            probabilities = (
                torch.softmax(
                    logits,
                    dim=1,
                )
            )

            predictions = (
                probabilities.argmax(
                    dim=1
                )
            )

            top_k = min(
                3,
                num_classes,
            )

            top3_indices = (
                probabilities.topk(
                    top_k,
                    dim=1,
                ).indices
            )

            batch_size = (
                y.size(0)
            )

            for batch_index in range(
                batch_size
            ):
                true_id = int(
                    y[
                        batch_index
                    ].item()
                )

                predicted_id = int(
                    predictions[
                        batch_index
                    ].item()
                )

                confidence = float(
                    probabilities[
                        batch_index,
                        predicted_id,
                    ].item()
                )

                top3_ids = [
                    int(value)
                    for value
                    in top3_indices[
                        batch_index
                    ].tolist()
                ]

                if true_id in top3_ids:
                    top3_correct += 1

                confusion_matrix[
                    true_id,
                    predicted_id,
                ] += 1

                record = (
                    test_records[
                        record_cursor
                    ]
                )

                record_cursor += 1

                true_sign = (
                    catalog_by_class[
                        true_id
                    ]
                )

                predicted_sign = (
                    catalog_by_class[
                        predicted_id
                    ]
                )

                prediction_rows.append({
                    "sample_id":
                        record.sample_id,

                    "signer_id":
                        record.signer_id,

                    "true_class_id":
                        true_id,

                    "true_sign_id":
                        true_sign.sign_id,

                    "true_label":
                        true_sign.label,

                    "predicted_class_id":
                        predicted_id,

                    "predicted_sign_id":
                        predicted_sign.sign_id,

                    "predicted_label":
                        predicted_sign.label,

                    "correct":
                        int(
                            true_id
                            ==
                            predicted_id
                        ),

                    "confidence":
                        confidence,

                    "top3_class_ids":
                        " | ".join(
                            str(value)
                            for value
                            in top3_ids
                        ),

                    "top3_sign_ids":
                        " | ".join(
                            catalog_by_class[
                                value
                            ].sign_id
                            for value
                            in top3_ids
                        ),
                })

    if (
        record_cursor
        != len(test_records)
    ):
        raise RuntimeError(
            "Prediction/sample alignment mismatch."
        )

    metrics = compute_metrics(
        confusion_matrix
    )

    sample_count = len(
        test_records
    )

    test_loss = (
        total_loss
        /
        sample_count
    )

    top3_accuracy = (
        top3_correct
        /
        sample_count
    )

    for item in metrics[
        "per_class"
    ]:
        sign = (
            catalog_by_class[
                item["class_id"]
            ]
        )

        item[
            "sign_id"
        ] = sign.sign_id

        item[
            "label"
        ] = sign.label

    confusion_rows = []

    for true_id in range(
        num_classes
    ):
        for predicted_id in range(
            num_classes
        ):
            if (
                true_id
                ==
                predicted_id
            ):
                continue

            count = int(
                confusion_matrix[
                    true_id,
                    predicted_id,
                ]
            )

            if count <= 0:
                continue

            true_sign = (
                catalog_by_class[
                    true_id
                ]
            )

            predicted_sign = (
                catalog_by_class[
                    predicted_id
                ]
            )

            confusion_rows.append({
                "true_class_id":
                    true_id,

                "true_sign_id":
                    true_sign.sign_id,

                "true_label":
                    true_sign.label,

                "predicted_class_id":
                    predicted_id,

                "predicted_sign_id":
                    predicted_sign.sign_id,

                "predicted_label":
                    predicted_sign.label,

                "count":
                    count,
            })

    confusion_rows.sort(
        key=lambda row: (
            -row["count"],
            row[
                "true_class_id"
            ],
            row[
                "predicted_class_id"
            ],
        )
    )

    predictions_path = (
        OUTPUT_DIR
        /
        "bilstm_predictions.csv"
    )

    with predictions_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "sample_id",
                "signer_id",
                "true_class_id",
                "true_sign_id",
                "true_label",
                "predicted_class_id",
                "predicted_sign_id",
                "predicted_label",
                "correct",
                "confidence",
                "top3_class_ids",
                "top3_sign_ids",
            ],
        )

        writer.writeheader()

        writer.writerows(
            prediction_rows
        )

    per_class_path = (
        OUTPUT_DIR
        /
        "bilstm_per_class_metrics.csv"
    )

    with per_class_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        fieldnames = [
            "class_id",
            "sign_id",
            "label",
            "support",
            "correct",
            "incorrect",
            "accuracy",
            "precision",
            "recall",
            "f1",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=
                fieldnames,
        )

        writer.writeheader()

        for row in metrics[
            "per_class"
        ]:
            writer.writerow({
                key:
                    row[key]
                for key
                in fieldnames
            })

    confusions_path = (
        OUTPUT_DIR
        /
        "bilstm_confusions.csv"
    )

    with confusions_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        fieldnames = [
            "true_class_id",
            "true_sign_id",
            "true_label",
            "predicted_class_id",
            "predicted_sign_id",
            "predicted_label",
            "count",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=
                fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            confusion_rows
        )

    confusion_csv_path = (
        OUTPUT_DIR
        /
        "bilstm_confusion_matrix.csv"
    )

    with confusion_csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.writer(
            file
        )

        writer.writerow(
            ["true\\pred"]
            +
            [
                checkpoint_mapping[
                    class_id
                ]
                for class_id
                in range(
                    num_classes
                )
            ]
        )

        for class_id in range(
            num_classes
        ):
            writer.writerow(
                [
                    checkpoint_mapping[
                        class_id
                    ]
                ]
                +
                confusion_matrix[
                    class_id,
                    :,
                ].tolist()
            )

    report = {
        "model":
            "BiLSTMBaseline",

        "checkpoint":
            str(
                CHECKPOINT_PATH
            ),

        "catalog_schema_version":
            catalog.schema_version,

        "test_signers":
            test_signers,

        "sample_count":
            sample_count,

        "num_classes":
            num_classes,

        "test_loss":
            test_loss,

        "accuracy":
            metrics[
                "accuracy"
            ],

        "top3_accuracy":
            top3_accuracy,

        "macro_precision":
            metrics[
                "macro_precision"
            ],

        "macro_recall":
            metrics[
                "macro_recall"
            ],

        "macro_f1":
            metrics[
                "macro_f1"
            ],

        "per_class":
            metrics[
                "per_class"
            ],

        "top_confusions":
            confusion_rows[:20],
    }

    report_path = (
        OUTPUT_DIR
        /
        "bilstm_evaluation.json"
    )

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    image_path = (
        OUTPUT_DIR
        /
        "bilstm_confusion_matrix.png"
    )

    image_created = False

    try:
        import matplotlib.pyplot as plt

        labels = [
            checkpoint_mapping[
                class_id
            ].replace(
                "CSL_",
                "",
            )
            for class_id
            in range(
                num_classes
            )
        ]

        figure, axis = (
            plt.subplots(
                figsize=(
                    12,
                    10,
                )
            )
        )

        image = axis.imshow(
            confusion_matrix
        )

        figure.colorbar(
            image,
            ax=axis,
            fraction=0.046,
            pad=0.04,
        )

        axis.set_xticks(
            np.arange(
                num_classes
            )
        )

        axis.set_yticks(
            np.arange(
                num_classes
            )
        )

        axis.set_xticklabels(
            labels,
            rotation=45,
            ha="right",
        )

        axis.set_yticklabels(
            labels
        )

        axis.set_xlabel(
            "Predicted class"
        )

        axis.set_ylabel(
            "True class"
        )

        axis.set_title(
            "SignBridge BiLSTM "
            "Confusion Matrix"
        )

        maximum = int(
            confusion_matrix.max()
        )

        threshold = (
            maximum / 2
            if maximum > 0
            else 0
        )

        for true_id in range(
            num_classes
        ):
            for predicted_id in range(
                num_classes
            ):
                value = int(
                    confusion_matrix[
                        true_id,
                        predicted_id,
                    ]
                )

                if value == 0:
                    continue

                axis.text(
                    predicted_id,
                    true_id,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=(
                        "white"
                        if value
                        >
                        threshold
                        else
                        "black"
                    ),
                )

        figure.tight_layout()

        figure.savefig(
            image_path,
            dpi=180,
            bbox_inches="tight",
        )

        plt.close(
            figure
        )

        image_created = True

    except ImportError:
        print()
        print(
            "WARNING: matplotlib is not installed."
        )

        print(
            "CSV/JSON evaluation files "
            "were still created."
        )

    print()
    print(
        "========================================"
    )
    print(
        " Evaluation summary"
    )
    print(
        "========================================"
    )

    print(
        f"Checkpoint    : {CHECKPOINT_PATH.name}"
    )

    print(
        f"Test signers  : {test_signers}"
    )

    print(
        f"Samples       : {sample_count}"
    )

    print(
        f"Test loss     : {test_loss:.4f}"
    )

    print(
        f"Top-1 accuracy: {metrics['accuracy']:.3f}"
    )

    print(
        f"Top-3 accuracy: {top3_accuracy:.3f}"
    )

    print(
        "Macro precision: "
        f"{metrics['macro_precision']:.3f}"
    )

    print(
        "Macro recall   : "
        f"{metrics['macro_recall']:.3f}"
    )

    print(
        "Macro F1       : "
        f"{metrics['macro_f1']:.3f}"
    )

    print()
    print(
        "---------- Per-class ----------"
    )

    for row in metrics[
        "per_class"
    ]:
        print(
            f"{row['class_id']:2d} "
            f"{row['sign_id']:<20} "
            f"{row['label']:<6} "
            f"{row['correct']}/{row['support']} "
            f"acc={row['accuracy']:.3f} "
            f"f1={row['f1']:.3f}"
        )

    print()
    print(
        "---------- Top confusions -----"
    )

    if not confusion_rows:
        print(
            "No misclassifications."
        )

    else:
        for row in confusion_rows[
            :15
        ]:
            print(
                f"{row['true_sign_id']:<20} "
                "-> "
                f"{row['predicted_sign_id']:<20} "
                f"x{row['count']}"
            )

    print()
    print(
        "Output:"
    )

    print(
        f"  {report_path}"
    )

    print(
        f"  {predictions_path}"
    )

    print(
        f"  {per_class_path}"
    )

    print(
        f"  {confusions_path}"
    )

    print(
        f"  {confusion_csv_path}"
    )

    if image_created:
        print(
            f"  {image_path}"
        )

    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
