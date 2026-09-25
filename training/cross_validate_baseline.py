from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from training.dataset_loader import (
    PROJECT_ROOT,
    load_catalog,
    load_manifest,
)
from training.models.bilstm_baseline import BiLSTMBaseline
from training.torch_dataset import SignBridgeDataset


OUTPUT_DIR = (
    PROJECT_ROOT
    / "training"
    / "cross_validation"
)

CHECKPOINT_DIR = (
    OUTPUT_DIR
    / "checkpoints"
)


class RemappedDataset(Dataset):
    def __init__(
        self,
        records,
        class_id_map: dict[int, int],
    ) -> None:
        self.base = SignBridgeDataset(
            records
        )

        self.class_id_map = (
            class_id_map
        )

    def __len__(self) -> int:
        return len(
            self.base
        )

    def __getitem__(
        self,
        index: int,
    ):
        x, y = self.base[index]

        if torch.is_tensor(y):
            original_class_id = int(
                y.item()
            )
        else:
            original_class_id = int(y)

        if (
            original_class_id
            not in self.class_id_map
        ):
            raise RuntimeError(
                "Class ID missing from "
                "active class mapping: "
                f"{original_class_id}"
            )

        model_class_id = (
            self.class_id_map[
                original_class_id
            ]
        )

        return (
            x,
            torch.tensor(
                model_class_id,
                dtype=torch.long,
            ),
        )


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
) -> tuple[float, float]:
    training = optimizer is not None

    if training:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    total_correct = 0
    total_count = 0

    for x, y in loader:
        x = x.to(device)
        y = y.to(device)

        if training:
            optimizer.zero_grad(set_to_none=True)

        with torch.set_grad_enabled(training):
            logits = model(x)
            loss = criterion(logits, y)

            if training:
                loss.backward()

                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    1.0,
                )

                optimizer.step()

        batch_size = y.size(0)

        total_loss += (
            float(loss.item())
            * batch_size
        )

        predictions = logits.argmax(dim=1)

        total_correct += int(
            (predictions == y)
            .sum()
            .item()
        )

        total_count += batch_size

    if total_count == 0:
        return 0.0, 0.0

    return (
        total_loss / total_count,
        total_correct / total_count,
    )


def metrics_from_confusion(
    matrix: np.ndarray,
) -> dict:
    num_classes = matrix.shape[0]

    total = int(matrix.sum())
    correct = int(np.trace(matrix))

    per_class = []

    precisions = []
    recalls = []
    f1s = []

    for class_id in range(num_classes):
        tp = int(
            matrix[class_id, class_id]
        )

        support = int(
            matrix[class_id, :].sum()
        )

        predicted = int(
            matrix[:, class_id].sum()
        )

        precision = safe_div(
            tp,
            predicted,
        )

        recall = safe_div(
            tp,
            support,
        )

        f1 = safe_div(
            2 * precision * recall,
            precision + recall,
        )

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

        per_class.append({
            "class_id": class_id,
            "support": support,
            "correct": tp,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })

    return {
        "accuracy": safe_div(
            correct,
            total,
        ),
        "macro_precision": float(
            np.mean(precisions)
        ),
        "macro_recall": float(
            np.mean(recalls)
        ),
        "macro_f1": float(
            np.mean(f1s)
        ),
        "per_class": per_class,
    }


def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    records,
    num_classes: int,
    device: torch.device,
    catalog_by_class: dict,
) -> tuple[
    np.ndarray,
    list[dict],
    float,
]:
    matrix = np.zeros(
        (num_classes, num_classes),
        dtype=np.int64,
    )

    prediction_rows = []

    top3_correct = 0
    cursor = 0

    model.eval()

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)

            logits = model(x)

            probabilities = torch.softmax(
                logits,
                dim=1,
            )

            predictions = probabilities.argmax(
                dim=1
            )

            top3 = probabilities.topk(
                min(3, num_classes),
                dim=1,
            ).indices

            for i in range(y.size(0)):
                true_id = int(y[i].item())

                predicted_id = int(
                    predictions[i].item()
                )

                confidence = float(
                    probabilities[
                        i,
                        predicted_id,
                    ].item()
                )

                top3_ids = [
                    int(v)
                    for v in top3[i].tolist()
                ]

                if true_id in top3_ids:
                    top3_correct += 1

                matrix[
                    true_id,
                    predicted_id,
                ] += 1

                record = records[cursor]
                cursor += 1

                prediction_rows.append({
                    "sample_id":
                        record.sample_id,

                    "signer_id":
                        record.signer_id,

                    "true_class_id":
                        true_id,

                    "true_sign_id":
                        catalog_by_class[
                            true_id
                        ].sign_id,

                    "predicted_class_id":
                        predicted_id,

                    "predicted_sign_id":
                        catalog_by_class[
                            predicted_id
                        ].sign_id,

                    "correct":
                        int(
                            true_id
                            == predicted_id
                        ),

                    "confidence":
                        confidence,

                    "top3_sign_ids":
                        " | ".join(
                            catalog_by_class[
                                class_id
                            ].sign_id
                            for class_id
                            in top3_ids
                        ),
                })

    if cursor != len(records):
        raise RuntimeError(
            "Prediction/record alignment mismatch."
        )

    top3_accuracy = safe_div(
        top3_correct,
        len(records),
    )

    return (
        matrix,
        prediction_rows,
        top3_accuracy,
    )


def write_matrix_csv(
    path: Path,
    matrix: np.ndarray,
    catalog_by_class: dict,
) -> None:
    num_classes = matrix.shape[0]

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            ["true\\pred"]
            +
            [
                catalog_by_class[i].sign_id
                for i in range(num_classes)
            ]
        )

        for class_id in range(num_classes):
            writer.writerow(
                [
                    catalog_by_class[
                        class_id
                    ].sign_id
                ]
                +
                matrix[
                    class_id,
                    :
                ].tolist()
            )


def save_confusion_image(
    path: Path,
    matrix: np.ndarray,
    catalog_by_class: dict,
    title: str,
) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    labels = [
        catalog_by_class[i]
        .sign_id
        .replace("CSL_", "")
        for i in range(
            matrix.shape[0]
        )
    ]

    figure, axis = plt.subplots(
        figsize=(12, 10)
    )

    image = axis.imshow(matrix)

    figure.colorbar(
        image,
        ax=axis,
        fraction=0.046,
        pad=0.04,
    )

    axis.set_xticks(
        np.arange(len(labels))
    )

    axis.set_yticks(
        np.arange(len(labels))
    )

    axis.set_xticklabels(
        labels,
        rotation=45,
        ha="right",
    )

    axis.set_yticklabels(labels)

    axis.set_xlabel(
        "Predicted class"
    )

    axis.set_ylabel(
        "True class"
    )

    axis.set_title(title)

    maximum = int(matrix.max())

    threshold = (
        maximum / 2
        if maximum > 0
        else 0
    )

    for row in range(
        matrix.shape[0]
    ):
        for column in range(
            matrix.shape[1]
        ):
            value = int(
                matrix[row, column]
            )

            if value == 0:
                continue

            axis.text(
                column,
                row,
                str(value),
                ha="center",
                va="center",
                fontsize=8,
                color=(
                    "white"
                    if value > threshold
                    else "black"
                ),
            )

    figure.tight_layout()

    figure.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(figure)

    return True


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-3,
    )

    parser.add_argument(
        "--hidden-size",
        type=int,
        default=128,
    )

    parser.add_argument(
        "--patience",
        type=int,
        default=7,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--exclude-sign",
        action="append",
        default=[],
        help=(
            "Exclude a sign_id from this "
            "experiment. May be repeated."
        ),
    )

    args = parser.parse_args()

    excluded_sign_ids = sorted(
        set(
            args.exclude_sign
        )
    )

    global OUTPUT_DIR
    global CHECKPOINT_DIR

    if excluded_sign_ids:
        suffix = "__".join(
            excluded_sign_ids
        )

        OUTPUT_DIR = (
            PROJECT_ROOT
            / "training"
            / (
                "cross_validation_"
                "exclude_"
                + suffix
            )
        )

        CHECKPOINT_DIR = (
            OUTPUT_DIR
            / "checkpoints"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    catalog = load_catalog()

    known_sign_ids = {
        sign.sign_id
        for sign in catalog.signs
    }

    unknown_exclusions = (
        set(excluded_sign_ids)
        - known_sign_ids
    )

    if unknown_exclusions:
        raise RuntimeError(
            "Unknown --exclude-sign value(s): "
            + ", ".join(
                sorted(
                    unknown_exclusions
                )
            )
        )

    active_signs = [
        sign
        for sign in catalog.signs
        if sign.sign_id
        not in excluded_sign_ids
    ]

    if len(active_signs) < 2:
        raise RuntimeError(
            "At least two active classes "
            "are required."
        )

    class_id_map = {
        sign.class_id: model_class_id
        for model_class_id, sign
        in enumerate(active_signs)
    }

    all_records = load_manifest(
        catalog=catalog,
        usable_only=True,
    )

    records = [
        record
        for record in all_records
        if record.sign_id
        not in excluded_sign_ids
    ]

    signers = sorted({
        record.signer_id
        for record in records
    })

    if len(signers) != 3:
        raise RuntimeError(
            "This 3-fold rotation script currently "
            "expects exactly 3 signers. "
            f"Found: {signers}"
        )

    if signers != [
        "S001",
        "S002",
        "S003",
    ]:
        print(
            "WARNING: signer IDs differ from "
            "S001/S002/S003."
        )

    folds = [
        {
            "fold": 1,
            "train": "S003",
            "validation": "S001",
            "test": "S002",
        },
        {
            "fold": 2,
            "train": "S001",
            "validation": "S002",
            "test": "S003",
        },
        {
            "fold": 3,
            "train": "S002",
            "validation": "S003",
            "test": "S001",
        },
    ]

    num_classes = len(
        active_signs
    )

    catalog_by_class = {
        model_class_id: sign
        for model_class_id, sign
        in enumerate(active_signs)
    }

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print()
    print(
        "========================================"
    )
    print(
        " SignBridge 3-Fold Signer Rotation"
    )
    print(
        "========================================"
    )
    print(
        f"Samples : {len(records)}"
    )
    print(
        f"Signers : {signers}"
    )
    print(
        f"Classes : {num_classes}"
    )

    if excluded_sign_ids:
        print(
            "Excluded: "
            + ", ".join(
                excluded_sign_ids
            )
        )

    print(
        f"Device  : {device}"
    )

    if device.type == "cuda":
        print(
            "GPU     : "
            f"{torch.cuda.get_device_name(0)}"
        )

    aggregate_matrix = np.zeros(
        (num_classes, num_classes),
        dtype=np.int64,
    )

    fold_rows = []
    all_predictions = []

    for fold_spec in folds:
        fold_id = fold_spec["fold"]

        train_signer = fold_spec["train"]

        validation_signer = (
            fold_spec["validation"]
        )

        test_signer = fold_spec["test"]

        train_records = [
            record
            for record in records
            if record.signer_id
            == train_signer
        ]

        validation_records = [
            record
            for record in records
            if record.signer_id
            == validation_signer
        ]

        test_records = [
            record
            for record in records
            if record.signer_id
            == test_signer
        ]

        print()
        print(
            "----------------------------------------"
        )
        print(
            f" Fold {fold_id}"
        )
        print(
            "----------------------------------------"
        )
        print(
            f"Train      : {train_signer} "
            f"({len(train_records)})"
        )
        print(
            f"Validation : {validation_signer} "
            f"({len(validation_records)})"
        )
        print(
            f"Test       : {test_signer} "
            f"({len(test_records)})"
        )

        set_seed(args.seed)

        train_loader = DataLoader(
            RemappedDataset(
                train_records,
                class_id_map,
            ),
            batch_size=args.batch_size,
            shuffle=True,
            num_workers=0,
            pin_memory=(
                device.type == "cuda"
            ),
        )

        validation_loader = DataLoader(
            RemappedDataset(
                validation_records,
                class_id_map,
            ),
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=0,
            pin_memory=(
                device.type == "cuda"
            ),
        )

        test_loader = DataLoader(
            RemappedDataset(
                test_records,
                class_id_map,
            ),
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=0,
            pin_memory=(
                device.type == "cuda"
            ),
        )

        model = BiLSTMBaseline(
            num_classes=num_classes,
            hidden_size=args.hidden_size,
        ).to(device)

        criterion = nn.CrossEntropyLoss()

        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=args.learning_rate,
            weight_decay=1e-4,
        )

        best_validation_loss = (
            float("inf")
        )

        best_epoch = 0
        bad_epochs = 0

        checkpoint_path = (
            CHECKPOINT_DIR
            / f"fold_{fold_id}.pt"
        )

        print()

        for epoch in range(
            1,
            args.epochs + 1,
        ):
            (
                train_loss,
                train_accuracy,
            ) = run_epoch(
                model=model,
                loader=train_loader,
                criterion=criterion,
                device=device,
                optimizer=optimizer,
            )

            (
                validation_loss,
                validation_accuracy,
            ) = run_epoch(
                model=model,
                loader=validation_loader,
                criterion=criterion,
                device=device,
                optimizer=None,
            )

            print(
                f"Fold {fold_id} | "
                f"Epoch {epoch:03d} | "
                f"train loss "
                f"{train_loss:.4f} | "
                f"train acc "
                f"{train_accuracy:.3f} | "
                f"val loss "
                f"{validation_loss:.4f} | "
                f"val acc "
                f"{validation_accuracy:.3f}"
            )

            if (
                validation_loss
                < best_validation_loss
            ):
                best_validation_loss = (
                    validation_loss
                )

                best_epoch = epoch

                bad_epochs = 0

                torch.save(
                    {
                        "model_state_dict":
                            model.state_dict(),

                        "fold":
                            fold_id,

                        "num_classes":
                            num_classes,

                        "hidden_size":
                            args.hidden_size,

                        "seed":
                            args.seed,

                        "train_signer":
                            train_signer,

                        "validation_signer":
                            validation_signer,

                        "test_signer":
                            test_signer,

                        "best_epoch":
                            best_epoch,

                        "best_validation_loss":
                            best_validation_loss,
                    },
                    checkpoint_path,
                )

            else:
                bad_epochs += 1

            if (
                bad_epochs
                >= args.patience
            ):
                print(
                    f"Fold {fold_id}: "
                    "early stopping."
                )
                break

        checkpoint = torch.load(
            checkpoint_path,
            map_location=device,
            weights_only=False,
        )

        model.load_state_dict(
            checkpoint[
                "model_state_dict"
            ]
        )

        (
            test_loss,
            test_accuracy,
        ) = run_epoch(
            model=model,
            loader=test_loader,
            criterion=criterion,
            device=device,
            optimizer=None,
        )

        (
            fold_matrix,
            fold_predictions,
            top3_accuracy,
        ) = evaluate_model(
            model=model,
            loader=test_loader,
            records=test_records,
            num_classes=num_classes,
            device=device,
            catalog_by_class=
                catalog_by_class,
        )

        fold_metrics = (
            metrics_from_confusion(
                fold_matrix
            )
        )

        aggregate_matrix += (
            fold_matrix
        )

        for row in fold_predictions:
            row["fold"] = fold_id
            row["train_signer"] = (
                train_signer
            )
            row[
                "validation_signer"
            ] = validation_signer
            row["test_signer"] = (
                test_signer
            )

        all_predictions.extend(
            fold_predictions
        )

        fold_row = {
            "fold":
                fold_id,

            "train_signer":
                train_signer,

            "validation_signer":
                validation_signer,

            "test_signer":
                test_signer,

            "train_samples":
                len(train_records),

            "validation_samples":
                len(validation_records),

            "test_samples":
                len(test_records),

            "best_epoch":
                best_epoch,

            "best_validation_loss":
                best_validation_loss,

            "test_loss":
                test_loss,

            "top1_accuracy":
                fold_metrics[
                    "accuracy"
                ],

            "top3_accuracy":
                top3_accuracy,

            "macro_precision":
                fold_metrics[
                    "macro_precision"
                ],

            "macro_recall":
                fold_metrics[
                    "macro_recall"
                ],

            "macro_f1":
                fold_metrics[
                    "macro_f1"
                ],
        }

        fold_rows.append(
            fold_row
        )

        write_matrix_csv(
            OUTPUT_DIR
            / (
                f"fold_{fold_id}_"
                "confusion_matrix.csv"
            ),
            fold_matrix,
            catalog_by_class,
        )

        save_confusion_image(
            OUTPUT_DIR
            / (
                f"fold_{fold_id}_"
                "confusion_matrix.png"
            ),
            fold_matrix,
            catalog_by_class,
            (
                "SignBridge BiLSTM "
                f"Fold {fold_id}"
            ),
        )

        print()
        print(
            f"Fold {fold_id} result"
        )
        print(
            f"  Best epoch : "
            f"{best_epoch}"
        )
        print(
            f"  Test loss  : "
            f"{test_loss:.4f}"
        )
        print(
            f"  Top-1      : "
            f"{fold_metrics['accuracy']:.3f}"
        )
        print(
            f"  Top-3      : "
            f"{top3_accuracy:.3f}"
        )
        print(
            f"  Macro-F1   : "
            f"{fold_metrics['macro_f1']:.3f}"
        )

    fold_metrics_path = (
        OUTPUT_DIR
        / "fold_metrics.csv"
    )

    with fold_metrics_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(
                fold_rows[0].keys()
            ),
        )

        writer.writeheader()

        writer.writerows(
            fold_rows
        )

    predictions_path = (
        OUTPUT_DIR
        / "all_predictions.csv"
    )

    with predictions_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        fieldnames = [
            "fold",
            "train_signer",
            "validation_signer",
            "test_signer",
            "sample_id",
            "signer_id",
            "true_class_id",
            "true_sign_id",
            "predicted_class_id",
            "predicted_sign_id",
            "correct",
            "confidence",
            "top3_sign_ids",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            all_predictions
        )

    aggregate_metrics = (
        metrics_from_confusion(
            aggregate_matrix
        )
    )

    per_class_rows = []

    for item in aggregate_metrics[
        "per_class"
    ]:
        class_id = item["class_id"]

        sign = (
            catalog_by_class[
                class_id
            ]
        )

        row = {
            "class_id":
                class_id,

            "sign_id":
                sign.sign_id,

            "label":
                sign.label,

            "support":
                item["support"],

            "correct":
                item["correct"],

            "precision":
                item["precision"],

            "recall":
                item["recall"],

            "f1":
                item["f1"],
        }

        per_class_rows.append(
            row
        )

    per_class_path = (
        OUTPUT_DIR
        / "per_class_metrics.csv"
    )

    with per_class_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(
                per_class_rows[0].keys()
            ),
        )

        writer.writeheader()

        writer.writerows(
            per_class_rows
        )

    write_matrix_csv(
        OUTPUT_DIR
        / (
            "aggregate_"
            "confusion_matrix.csv"
        ),
        aggregate_matrix,
        catalog_by_class,
    )

    image_created = (
        save_confusion_image(
            OUTPUT_DIR
            / (
                "aggregate_"
                "confusion_matrix.png"
            ),
            aggregate_matrix,
            catalog_by_class,
            (
                "SignBridge BiLSTM "
                "3-Fold Aggregate "
                "Confusion Matrix"
            ),
        )
    )

    top1_values = np.array(
        [
            row["top1_accuracy"]
            for row in fold_rows
        ],
        dtype=float,
    )

    top3_values = np.array(
        [
            row["top3_accuracy"]
            for row in fold_rows
        ],
        dtype=float,
    )

    f1_values = np.array(
        [
            row["macro_f1"]
            for row in fold_rows
        ],
        dtype=float,
    )

    summary = {
        "dataset_samples":
            len(records),

        "excluded_signs":
            excluded_sign_ids,

        "active_signs": [
            sign.sign_id
            for sign in active_signs
        ],

        "signers":
            signers,

        "num_classes":
            num_classes,

        "folds":
            fold_rows,

        "fold_mean_top1":
            float(
                top1_values.mean()
            ),

        "fold_std_top1":
            float(
                top1_values.std()
            ),

        "fold_mean_top3":
            float(
                top3_values.mean()
            ),

        "fold_std_top3":
            float(
                top3_values.std()
            ),

        "fold_mean_macro_f1":
            float(
                f1_values.mean()
            ),

        "fold_std_macro_f1":
            float(
                f1_values.std()
            ),

        "aggregate_accuracy":
            aggregate_metrics[
                "accuracy"
            ],

        "aggregate_macro_precision":
            aggregate_metrics[
                "macro_precision"
            ],

        "aggregate_macro_recall":
            aggregate_metrics[
                "macro_recall"
            ],

        "aggregate_macro_f1":
            aggregate_metrics[
                "macro_f1"
            ],
    }

    summary_path = (
        OUTPUT_DIR
        / "summary.json"
    )

    summary_path.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "========================================"
    )
    print(
        " 3-Fold Summary"
    )
    print(
        "========================================"
    )

    for row in fold_rows:
        print(
            f"Fold {row['fold']} | "
            f"train={row['train_signer']} | "
            f"val={row['validation_signer']} | "
            f"test={row['test_signer']} | "
            f"Top-1={row['top1_accuracy']:.3f} | "
            f"Top-3={row['top3_accuracy']:.3f} | "
            f"F1={row['macro_f1']:.3f}"
        )

    print()
    print(
        "Fold Top-1 : "
        f"{top1_values.mean():.3f} "
        f"± {top1_values.std():.3f}"
    )

    print(
        "Fold Top-3 : "
        f"{top3_values.mean():.3f} "
        f"± {top3_values.std():.3f}"
    )

    print(
        "Fold F1    : "
        f"{f1_values.mean():.3f} "
        f"± {f1_values.std():.3f}"
    )

    print()
    print(
        "Aggregate accuracy : "
        f"{aggregate_metrics['accuracy']:.3f}"
    )

    print(
        "Aggregate Macro-F1 : "
        f"{aggregate_metrics['macro_f1']:.3f}"
    )

    print()
    print(
        "---------- Per-class aggregate ----------"
    )

    for row in per_class_rows:
        print(
            f"{row['class_id']:2d} "
            f"{row['sign_id']:<20} "
            f"{row['label']:<6} "
            f"{row['correct']}/{row['support']} "
            f"recall={row['recall']:.3f} "
            f"f1={row['f1']:.3f}"
        )

    print()
    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    if not image_created:
        print(
            "matplotlib unavailable: "
            "PNG was not generated."
        )

    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
