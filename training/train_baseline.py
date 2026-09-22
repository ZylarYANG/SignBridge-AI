from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from training.dataset_loader import (
    DatasetError,
    PROJECT_ROOT,
    load_catalog,
    load_manifest,
)
from training.models.bilstm_baseline import BiLSTMBaseline
from training.split import (
    apply_signer_split,
    make_signer_split,
)
from training.torch_dataset import SignBridgeDataset


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


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


def get_class_counts(
    records,
) -> dict[int, int]:
    counter = Counter(
        record.class_id
        for record in records
    )

    return dict(
        sorted(counter.items())
    )


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
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--patience",
        type=int,
        default=7,
    )

    args = parser.parse_args()

    set_seed(args.seed)

    catalog = load_catalog()

    records = load_manifest(
        catalog=catalog,
        usable_only=True,
    )

    if not records:
        print()
        print("No usable dataset samples found.")
        print("Collect real samples before training.")
        print()

        return 0

    signers = sorted(
        {
            record.signer_id
            for record in records
        }
    )

    print()
    print("========================================")
    print(" SignBridge Mini Baseline")
    print("========================================")
    print(f"Samples : {len(records)}")
    print(f"Signers : {len(signers)}")
    print(f"Classes : {len(catalog.signs)}")

    if len(signers) < 3:
        print()
        print("Training skipped.")
        print(
            "Need at least 3 distinct signers "
            "for signer-independent splitting."
        )
        print(f"Current signers: {signers}")
        print()

        return 0

    split = make_signer_split(
        records,
        seed=args.seed,
    )

    (
        train_records,
        validation_records,
        test_records,
    ) = apply_signer_split(
        records,
        split,
    )

    print()
    print("Signer split:")
    print(
        f"  train      : {list(split.train_signers)}"
    )
    print(
        f"  validation : {list(split.validation_signers)}"
    )
    print(
        f"  test       : {list(split.test_signers)}"
    )

    print()
    print("Sample counts:")
    print(f"  train      : {len(train_records)}")
    print(f"  validation : {len(validation_records)}")
    print(f"  test       : {len(test_records)}")

    print()
    print(
        "Train class counts:",
        get_class_counts(train_records),
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print()
    print(f"Device : {device}")

    if device.type == "cuda":
        print(
            "GPU    : "
            f"{torch.cuda.get_device_name(0)}"
        )

    train_loader = DataLoader(
        SignBridgeDataset(train_records),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )

    validation_loader = DataLoader(
        SignBridgeDataset(validation_records),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )

    test_loader = DataLoader(
        SignBridgeDataset(test_records),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )

    model = BiLSTMBaseline(
        num_classes=len(catalog.signs),
        hidden_size=args.hidden_size,
    ).to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=1e-4,
    )

    checkpoint_dir = (
        PROJECT_ROOT
        / "models"
        / "checkpoints"
    )

    checkpoint_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint_path = (
        checkpoint_dir
        / "bilstm_baseline_best.pt"
    )

    metadata_path = (
        checkpoint_dir
        / "bilstm_baseline_best.json"
    )

    best_validation_loss = float("inf")
    best_epoch = 0
    bad_epochs = 0

    print()
    print("Starting training...")

    for epoch in range(
        1,
        args.epochs + 1,
    ):
        train_loss, train_accuracy = run_epoch(
            model=model,
            loader=train_loader,
            criterion=criterion,
            device=device,
            optimizer=optimizer,
        )

        validation_loss, validation_accuracy = run_epoch(
            model=model,
            loader=validation_loader,
            criterion=criterion,
            device=device,
            optimizer=None,
        )

        print(
            f"Epoch {epoch:03d} | "
            f"train loss {train_loss:.4f} | "
            f"train acc {train_accuracy:.3f} | "
            f"val loss {validation_loss:.4f} | "
            f"val acc {validation_accuracy:.3f}"
        )

        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            best_epoch = epoch
            bad_epochs = 0

            torch.save(
                {
                    "model_state_dict":
                        model.state_dict(),

                    "num_classes":
                        len(catalog.signs),

                    "hidden_size":
                        args.hidden_size,

                    "catalog_schema_version":
                        catalog.schema_version,

                    "class_mapping": {
                        sign.class_id:
                            sign.sign_id
                        for sign in catalog.signs
                    },

                    "seed":
                        args.seed,

                    "train_signers":
                        list(split.train_signers),

                    "validation_signers":
                        list(
                            split.validation_signers
                        ),

                    "test_signers":
                        list(split.test_signers),
                },
                checkpoint_path,
            )

        else:
            bad_epochs += 1

        if bad_epochs >= args.patience:
            print("Early stopping.")
            break

    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    test_loss, test_accuracy = run_epoch(
        model=model,
        loader=test_loader,
        criterion=criterion,
        device=device,
        optimizer=None,
    )

    metadata = {
        "model": "BiLSTMBaseline",
        "input_shape": [64, 54, 2],
        "num_classes": len(catalog.signs),
        "best_epoch": best_epoch,
        "best_validation_loss":
            best_validation_loss,
        "test_loss": test_loss,
        "test_accuracy": test_accuracy,
        "seed": args.seed,
        "train_signers":
            list(split.train_signers),
        "validation_signers":
            list(split.validation_signers),
        "test_signers":
            list(split.test_signers),
    }

    metadata_path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("========================================")
    print(" Training complete")
    print("========================================")
    print(f"Best epoch    : {best_epoch}")
    print(f"Test loss     : {test_loss:.4f}")
    print(f"Test accuracy : {test_accuracy:.3f}")
    print(f"Checkpoint    : {checkpoint_path}")
    print()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())

    except DatasetError as exc:
        print(
            f"Dataset error: {exc}"
        )

        raise SystemExit(1)
