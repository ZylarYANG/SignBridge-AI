from __future__ import annotations

import csv
import json
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from training.dataset_loader import (
    PROJECT_ROOT,
    load_catalog,
    load_manifest,
)
from training.models.bilstm_baseline import BiLSTMBaseline
from training.cross_validate_baseline import (
    RemappedDataset,
    set_seed,
    run_epoch,
    evaluate_model,
    metrics_from_confusion,
    write_matrix_csv,
    save_confusion_image,
)


EXCLUDED_SIGNS = {
    "CSL_me",
    "CSL_please",
    "CSL_you",
}

TRAIN_SIGNERS = {
    "S001",
    "S002",
}

VALIDATION_SIGNERS = {
    "S003",
}

TEST_SIGNERS = {
    "S004",
}

SEED = 42
EPOCHS = 30
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
HIDDEN_SIZE = 128
PATIENCE = 7


def main() -> int:
    set_seed(SEED)

    output_dir = (
        PROJECT_ROOT
        / "training"
        / "quick_validation_s004"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    catalog = load_catalog()

    all_records = load_manifest(
        catalog=catalog,
        usable_only=True,
    )

    active_signs = [
        sign
        for sign in catalog.signs
        if sign.sign_id
        not in EXCLUDED_SIGNS
    ]

    class_id_map = {
        sign.class_id: model_class_id
        for model_class_id, sign
        in enumerate(active_signs)
    }

    catalog_by_class = {
        model_class_id: sign
        for model_class_id, sign
        in enumerate(active_signs)
    }

    active_records = [
        record
        for record in all_records
        if record.sign_id
        not in EXCLUDED_SIGNS
    ]

    train_records = [
        record
        for record in active_records
        if record.signer_id
        in TRAIN_SIGNERS
    ]

    validation_records = [
        record
        for record in active_records
        if record.signer_id
        in VALIDATION_SIGNERS
    ]

    test_records = [
        record
        for record in active_records
        if record.signer_id
        in TEST_SIGNERS
    ]

    num_classes = len(
        active_signs
    )

    print()
    print(
        "========================================"
    )
    print(
        " SignBridge S004 Holdout Validation"
    )
    print(
        "========================================"
    )

    print(
        f"Classes    : {num_classes}"
    )

    print(
        "Excluded   : "
        + ", ".join(
            sorted(EXCLUDED_SIGNS)
        )
    )

    print(
        f"Train      : "
        f"{sorted(TRAIN_SIGNERS)} "
        f"({len(train_records)})"
    )

    print(
        f"Validation : "
        f"{sorted(VALIDATION_SIGNERS)} "
        f"({len(validation_records)})"
    )

    print(
        f"Test       : "
        f"{sorted(TEST_SIGNERS)} "
        f"({len(test_records)})"
    )

    if len(train_records) != 120:
        raise RuntimeError(
            "Expected 120 training samples, "
            f"found {len(train_records)}."
        )

    if len(validation_records) != 60:
        raise RuntimeError(
            "Expected 60 validation samples, "
            f"found {len(validation_records)}."
        )

    if len(test_records) != 240:
        raise RuntimeError(
            "Expected 240 S004 test samples, "
            f"found {len(test_records)}."
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

    train_loader = DataLoader(
        RemappedDataset(
            train_records,
            class_id_map,
        ),
        batch_size=BATCH_SIZE,
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
        batch_size=BATCH_SIZE,
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
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=(
            device.type == "cuda"
        ),
    )

    model = BiLSTMBaseline(
        num_classes=num_classes,
        hidden_size=HIDDEN_SIZE,
    ).to(device)

    criterion = (
        nn.CrossEntropyLoss()
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=1e-4,
    )

    best_validation_loss = (
        float("inf")
    )

    best_epoch = 0
    bad_epochs = 0

    checkpoint_path = (
        output_dir
        / "bilstm_s004_holdout.pt"
    )

    print()
    print("Starting training...")
    print()

    for epoch in range(
        1,
        EPOCHS + 1,
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

                    "num_classes":
                        num_classes,

                    "hidden_size":
                        HIDDEN_SIZE,

                    "seed":
                        SEED,

                    "excluded_signs":
                        sorted(
                            EXCLUDED_SIGNS
                        ),

                    "train_signers":
                        sorted(
                            TRAIN_SIGNERS
                        ),

                    "validation_signers":
                        sorted(
                            VALIDATION_SIGNERS
                        ),

                    "test_signers":
                        sorted(
                            TEST_SIGNERS
                        ),

                    "best_epoch":
                        best_epoch,

                    "best_validation_loss":
                        best_validation_loss,
                },
                checkpoint_path,
            )

        else:
            bad_epochs += 1

        if bad_epochs >= PATIENCE:
            print(
                "Early stopping."
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
        _,
    ) = run_epoch(
        model=model,
        loader=test_loader,
        criterion=criterion,
        device=device,
        optimizer=None,
    )

    (
        confusion_matrix,
        predictions,
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

    metrics = (
        metrics_from_confusion(
            confusion_matrix
        )
    )

    prediction_path = (
        output_dir
        / "predictions.csv"
    )

    with prediction_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(
                predictions[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(predictions)

    write_matrix_csv(
        output_dir
        / "confusion_matrix.csv",
        confusion_matrix,
        catalog_by_class,
    )

    save_confusion_image(
        output_dir
        / "confusion_matrix.png",
        confusion_matrix,
        catalog_by_class,
        (
            "SignBridge BiLSTM "
            "S004 Holdout"
        ),
    )

    per_class_rows = []

    print()
    print(
        "========================================"
    )
    print(
        " S004 Holdout Result"
    )
    print(
        "========================================"
    )

    print(
        f"Best epoch : "
        f"{best_epoch}"
    )

    print(
        f"Test loss  : "
        f"{test_loss:.4f}"
    )

    print(
        f"Top-1      : "
        f"{metrics['accuracy']:.3f}"
    )

    print(
        f"Top-3      : "
        f"{top3_accuracy:.3f}"
    )

    print(
        f"Macro-P    : "
        f"{metrics['macro_precision']:.3f}"
    )

    print(
        f"Macro-R    : "
        f"{metrics['macro_recall']:.3f}"
    )

    print(
        f"Macro-F1   : "
        f"{metrics['macro_f1']:.3f}"
    )

    print()
    print(
        "---------- Per-class ----------"
    )

    for item in metrics[
        "per_class"
    ]:
        class_id = (
            item["class_id"]
        )

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

        print(
            f"{class_id:2d} "
            f"{sign.sign_id:<20} "
            f"{item['correct']:2d}/"
            f"{item['support']:<2d} "
            f"recall="
            f"{item['recall']:.3f} "
            f"f1="
            f"{item['f1']:.3f}"
        )

    with (
        output_dir
        / "per_class_metrics.csv"
    ).open(
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

    summary = {
        "train_signers":
            sorted(TRAIN_SIGNERS),

        "validation_signers":
            sorted(
                VALIDATION_SIGNERS
            ),

        "test_signers":
            sorted(TEST_SIGNERS),

        "train_samples":
            len(train_records),

        "validation_samples":
            len(validation_records),

        "test_samples":
            len(test_records),

        "best_epoch":
            best_epoch,

        "test_loss":
            test_loss,

        "top1_accuracy":
            metrics["accuracy"],

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
    }

    (
        output_dir
        / "summary.json"
    ).write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Output:"
    )

    print(
        output_dir
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
