from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from training.dataset_loader import (
    PROJECT_ROOT,
    load_catalog,
    load_manifest,
)
from training.models.bilstm_handshape_attention import (
    BiLSTMHandshapeAttention,
)
from training.torch_dataset import (
    SignBridgeDataset,
)


INACTIVE_SIGN_IDS = {
    "CSL_me",
    "CSL_please",
    "CSL_you",
}


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class RemappedDataset(Dataset):

    def __init__(
        self,
        records,
        old_to_new: dict[int, int],
    ) -> None:

        self.base = SignBridgeDataset(
            records
        )

        self.old_to_new = old_to_new


    def __len__(self):
        return len(self.base)


    def __getitem__(self, index):

        x, y = self.base[index]

        if torch.is_tensor(y):
            old_id = int(
                y.item()
            )
        else:
            old_id = int(y)

        new_id = self.old_to_new[
            old_id
        ]

        return (
            x,
            torch.tensor(
                new_id,
                dtype=torch.long,
            ),
        )


def run_epoch(
    model,
    loader,
    criterion,
    device,
    optimizer=None,
):
    training = (
        optimizer is not None
    )

    if training:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    total_correct = 0
    total_count = 0

    for x, y in loader:

        x = x.to(
            device
        )

        y = y.to(
            device
        )

        if training:
            optimizer.zero_grad(
                set_to_none=True
            )

        with torch.set_grad_enabled(
            training
        ):

            logits = model(x)

            loss = criterion(
                logits,
                y,
            )

            if training:

                loss.backward()

                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    1.0,
                )

                optimizer.step()

        batch_size = (
            y.size(0)
        )

        total_loss += (
            float(
                loss.item()
            )
            * batch_size
        )

        prediction = (
            logits.argmax(
                dim=1
            )
        )

        total_correct += int(
            (
                prediction == y
            )
            .sum()
            .item()
        )

        total_count += (
            batch_size
        )

    return (
        total_loss
        / max(
            total_count,
            1,
        ),
        total_correct
        / max(
            total_count,
            1,
        ),
    )


def evaluate(
    model,
    loader,
    device,
    num_classes,
):

    model.eval()

    confusion = torch.zeros(
        (
            num_classes,
            num_classes,
        ),
        dtype=torch.long,
    )

    top1_correct = 0
    top3_correct = 0
    total = 0

    with torch.no_grad():

        for x, y in loader:

            x = x.to(
                device
            )

            y = y.to(
                device
            )

            logits = model(x)

            top1 = logits.argmax(
                dim=1
            )

            top3 = logits.topk(
                k=min(
                    3,
                    num_classes,
                ),
                dim=1,
            ).indices

            top1_correct += int(
                (
                    top1 == y
                )
                .sum()
                .item()
            )

            top3_correct += int(
                (
                    top3
                    ==
                    y.unsqueeze(1)
                )
                .any(dim=1)
                .sum()
                .item()
            )

            total += (
                y.size(0)
            )

            for true_y, pred_y in zip(
                y.cpu(),
                top1.cpu(),
            ):
                confusion[
                    int(true_y),
                    int(pred_y),
                ] += 1

    per_class = []

    precision_values = []
    recall_values = []
    f1_values = []

    for class_id in range(
        num_classes
    ):

        tp = int(
            confusion[
                class_id,
                class_id,
            ]
        )

        support = int(
            confusion[
                class_id,
                :
            ].sum()
        )

        predicted = int(
            confusion[
                :,
                class_id,
            ].sum()
        )

        fp = (
            predicted - tp
        )

        fn = (
            support - tp
        )

        precision = (
            tp
            / (tp + fp)
            if (tp + fp) > 0
            else 0.0
        )

        recall = (
            tp
            / (tp + fn)
            if (tp + fn) > 0
            else 0.0
        )

        f1 = (
            2
            * precision
            * recall
            / (
                precision
                + recall
            )
            if (
                precision
                + recall
            ) > 0
            else 0.0
        )

        precision_values.append(
            precision
        )

        recall_values.append(
            recall
        )

        f1_values.append(
            f1
        )

        per_class.append({
            "class_id":
                class_id,

            "support":
                support,

            "correct":
                tp,

            "precision":
                precision,

            "recall":
                recall,

            "f1":
                f1,
        })

    return {
        "sample_count":
            total,

        "top1_accuracy":
            (
                top1_correct
                / total
            ),

        "top3_accuracy":
            (
                top3_correct
                / total
            ),

        "macro_precision":
            sum(
                precision_values
            )
            / num_classes,

        "macro_recall":
            sum(
                recall_values
            )
            / num_classes,

        "macro_f1":
            sum(
                f1_values
            )
            / num_classes,

        "per_class":
            per_class,

        "confusion_matrix":
            confusion.tolist(),
    }


def class_counts(
    records,
    old_to_new,
):
    counts = Counter()

    for record in records:
        counts[
            old_to_new[
                record.class_id
            ]
        ] += 1

    return dict(
        sorted(
            counts.items()
        )
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=40,
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
        default=8,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--validation-signer",
        type=str,
        default="S004",
    )

    parser.add_argument(
        "--test-signer",
        type=str,
        default="S005",
    )

    args = parser.parse_args()

    set_seed(
        args.seed
    )

    catalog = (
        load_catalog()
    )

    all_records = load_manifest(
        catalog=catalog,
        usable_only=True,
    )


    active_signs = [
        sign
        for sign in catalog.signs
        if sign.sign_id
        not in INACTIVE_SIGN_IDS
    ]


    if len(active_signs) != 12:
        raise RuntimeError(
            "Expected 12 active signs, "
            f"got {len(active_signs)}"
        )


    active_old_ids = {
        sign.class_id
        for sign in active_signs
    }


    old_to_new = {
        sign.class_id:
            new_id

        for new_id, sign
        in enumerate(
            active_signs
        )
    }


    class_mapping = {
        new_id: {
            "original_class_id":
                sign.class_id,

            "sign_id":
                sign.sign_id,

            "label":
                sign.label,
        }

        for new_id, sign
        in enumerate(
            active_signs
        )
    }


    records = [
        record
        for record in all_records
        if record.class_id
        in active_old_ids
    ]


    train_signers = {
        "S001",
        "S002",
        "S003",
    }

    validation_signers = {
        args.validation_signer,
    }

    test_signers = {
        args.test_signer,
    }


    train_records = [
        r
        for r in records
        if r.signer_id
        in train_signers
    ]

    validation_records = [
        r
        for r in records
        if r.signer_id
        in validation_signers
    ]

    test_records = [
        r
        for r in records
        if r.signer_id
        in test_signers
    ]


    print()
    print(
        "========================================"
    )
    print(
        " SignBridge Handshape-Attention BiLSTM"
    )
    print(
        "========================================"
    )

    print(
        "Train signers      :",
        sorted(
            train_signers
        ),
    )

    print(
        "Validation signers :",
        sorted(
            validation_signers
        ),
    )

    print(
        "Test signers       :",
        sorted(
            test_signers
        ),
    )

    print()

    print(
        "Train samples      :",
        len(
            train_records
        ),
    )

    print(
        "Validation samples :",
        len(
            validation_records
        ),
    )

    print(
        "Test samples       :",
        len(
            test_records
        ),
    )

    print()

    print(
        "Train counts:",
        class_counts(
            train_records,
            old_to_new,
        ),
    )

    print(
        "Validation counts:",
        class_counts(
            validation_records,
            old_to_new,
        ),
    )

    print(
        "Test counts:",
        class_counts(
            test_records,
            old_to_new,
        ),
    )


    expected = (
        540,
        240,
        240,
    )

    actual = (
        len(
            train_records
        ),
        len(
            validation_records
        ),
        len(
            test_records
        ),
    )

    if actual != expected:

        raise RuntimeError(
            "Unexpected split sizes. "
            f"Expected {expected}, "
            f"got {actual}"
        )


    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else
        "cpu"
    )

    print()
    print(
        "Device:",
        device,
    )

    if device.type == "cuda":

        print(
            "GPU:",
            torch.cuda.get_device_name(
                0
            ),
        )


    train_loader = DataLoader(
        RemappedDataset(
            train_records,
            old_to_new,
        ),
        batch_size=
            args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=
            device.type == "cuda",
    )


    validation_loader = DataLoader(
        RemappedDataset(
            validation_records,
            old_to_new,
        ),
        batch_size=
            args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=
            device.type == "cuda",
    )


    test_loader = DataLoader(
        RemappedDataset(
            test_records,
            old_to_new,
        ),
        batch_size=
            args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=
            device.type == "cuda",
    )


    model = BiLSTMHandshapeAttention(
        num_classes=12,
        hidden_size=
            args.hidden_size,
    ).to(
        device
    )


    criterion = (
        nn.CrossEntropyLoss()
    )

    optimizer = (
        torch.optim.AdamW(
            model.parameters(),
            lr=
                args.learning_rate,
            weight_decay=
                1e-4,
        )
    )


    output_dir = (
        PROJECT_ROOT
        / "training"
        / "experiments"
        / "formal_12class"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )


    run_name = (
        "bilstm_hsa_"
        + args.validation_signer.lower()
        + "val_"
        + args.test_signer.lower()
        + "test"
    )

    checkpoint_path = (
        output_dir
        / f"{run_name}.pt"
    )

    evaluation_path = (
        output_dir
        / f"{run_name}.json"
    )


    best_validation_loss = (
        float("inf")
    )

    best_epoch = 0
    bad_epochs = 0


    print()
    print(
        "Starting training..."
    )


    for epoch in range(
        1,
        args.epochs + 1,
    ):

        train_loss, train_acc = (
            run_epoch(
                model,
                train_loader,
                criterion,
                device,
                optimizer,
            )
        )

        val_loss, val_acc = (
            run_epoch(
                model,
                validation_loader,
                criterion,
                device,
                None,
            )
        )

        print(
            f"Epoch {epoch:03d} | "
            f"train loss "
            f"{train_loss:.4f} | "
            f"train acc "
            f"{train_acc:.3f} | "
            f"val loss "
            f"{val_loss:.4f} | "
            f"val acc "
            f"{val_acc:.3f}"
        )


        if (
            val_loss
            <
            best_validation_loss
        ):

            best_validation_loss = (
                val_loss
            )

            best_epoch = (
                epoch
            )

            bad_epochs = 0

            torch.save(
                {
                    "model_state_dict":
                        model.state_dict(),

                    "num_classes":
                        12,

                    "hidden_size":
                        args.hidden_size,

                    "seed":
                        args.seed,

                    "best_epoch":
                        best_epoch,

                    "best_validation_loss":
                        best_validation_loss,

                    "train_signers":
                        sorted(
                            train_signers
                        ),

                    "validation_signers":
                        sorted(
                            validation_signers
                        ),

                    "test_signers":
                        sorted(
                            test_signers
                        ),

                    "class_mapping":
                        class_mapping,

                    "dataset_snapshot_sha256":
                        "E4AE9B57ABAEFE285E5C4B9398DB19C3E79B2D423C7EE5105D11B30C863DABB7",
                },
                checkpoint_path,
            )

        else:

            bad_epochs += 1


        if (
            bad_epochs
            >=
            args.patience
        ):

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


    metrics = evaluate(
        model,
        test_loader,
        device,
        12,
    )


    for item in (
        metrics[
            "per_class"
        ]
    ):

        info = class_mapping[
            item[
                "class_id"
            ]
        ]

        item.update(
            info
        )


    report = {
        "experiment":
            run_name,

        "dataset_snapshot_sha256":
            "E4AE9B57ABAEFE285E5C4B9398DB19C3E79B2D423C7EE5105D11B30C863DABB7",

        "seed":
            args.seed,

        "best_epoch":
            checkpoint[
                "best_epoch"
            ],

        "best_validation_loss":
            checkpoint[
                "best_validation_loss"
            ],

        "train_signers":
            sorted(
                train_signers
            ),

        "validation_signers":
            sorted(
                validation_signers
            ),

        "test_signers":
            sorted(
                test_signers
            ),

        "sample_counts": {
            "train":
                len(
                    train_records
                ),

            "validation":
                len(
                    validation_records
                ),

            "test":
                len(
                    test_records
                ),
        },

        "class_mapping":
            class_mapping,

        **metrics,
    }


    evaluation_path.write_text(
        json.dumps(
            report,
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
        " FINAL TEST RESULT"
    )
    print(
        "========================================"
    )

    print(
        f"Best epoch      : "
        f"{report['best_epoch']}"
    )

    print(
        f"Top-1 Accuracy  : "
        f"{metrics['top1_accuracy']:.4f}"
    )

    print(
        f"Top-3 Accuracy  : "
        f"{metrics['top3_accuracy']:.4f}"
    )

    print(
        f"Macro Precision : "
        f"{metrics['macro_precision']:.4f}"
    )

    print(
        f"Macro Recall    : "
        f"{metrics['macro_recall']:.4f}"
    )

    print(
        f"Macro F1        : "
        f"{metrics['macro_f1']:.4f}"
    )


    print()
    print(
        "Per-class:"
    )

    for item in (
        metrics[
            "per_class"
        ]
    ):

        print(
            f"{item['class_id']:2d} "
            f"{item['sign_id']:<18} "
            f"{item['label']:<6} "
            f"support={item['support']:>3} "
            f"correct={item['correct']:>3} "
            f"P={item['precision']:.3f} "
            f"R={item['recall']:.3f} "
            f"F1={item['f1']:.3f}"
        )


    print()
    print(
        "Checkpoint:",
        checkpoint_path,
    )

    print(
        "Evaluation:",
        evaluation_path,
    )


if __name__ == "__main__":
    main()
