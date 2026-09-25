from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from training.dataset_loader import (
    PROJECT_ROOT,
    load_catalog,
    load_manifest,
)
from training.models.bilstm_contrastive import (
    BiLSTMContrastiveBaseline,
)
from training.torch_dataset import (
    SignBridgeDataset,
)


INACTIVE_SIGN_IDS = {
    "CSL_me",
    "CSL_please",
    "CSL_you",
}

TRAIN_SIGNERS = (
    "S001",
    "S002",
    "S003",
)


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(
            seed
        )


class ContrastiveDataset(Dataset):

    def __init__(
        self,
        records,
        old_to_new,
        signer_to_index,
    ) -> None:

        self.records = list(
            records
        )

        self.base = SignBridgeDataset(
            self.records
        )

        self.old_to_new = (
            old_to_new
        )

        self.signer_to_index = (
            signer_to_index
        )


    def __len__(self):
        return len(
            self.records
        )


    def __getitem__(
        self,
        index,
    ):

        x, _ = self.base[
            index
        ]

        record = self.records[
            index
        ]

        y = self.old_to_new[
            record.class_id
        ]

        signer = (
            self.signer_to_index[
                record.signer_id
            ]
        )

        return (
            x,
            torch.tensor(
                y,
                dtype=torch.long,
            ),
            torch.tensor(
                signer,
                dtype=torch.long,
            ),
        )


class CrossSignerClassBatchSampler:
    """
    Every training batch contains exactly:

        12 classes
        x
        3 training signers
        =
        36 samples

    One sample is selected for every
    (class, signer) combination.

    S003 has fewer samples, so it is deliberately
    cycled/oversampled to give every signer equal
    influence in each batch.
    """

    def __init__(
        self,
        records,
        old_to_new,
        train_signers,
        seed,
    ) -> None:

        self.seed = seed
        self.epoch = 0

        self.groups = defaultdict(
            list
        )

        signer_set = set(
            train_signers
        )

        for index, record in enumerate(
            records
        ):

            if (
                record.signer_id
                not in signer_set
            ):
                continue

            class_id = (
                old_to_new[
                    record.class_id
                ]
            )

            key = (
                class_id,
                record.signer_id,
            )

            self.groups[
                key
            ].append(
                index
            )

        self.classes = sorted({
            class_id
            for class_id, _
            in self.groups
        })

        self.signers = tuple(
            train_signers
        )

        expected = (
            len(self.classes)
            * len(self.signers)
        )

        if (
            len(self.groups)
            != expected
        ):
            raise RuntimeError(
                "Missing class/signer groups. "
                f"Expected {expected}, "
                f"got {len(self.groups)}"
            )

        for class_id in self.classes:
            for signer in self.signers:

                key = (
                    class_id,
                    signer,
                )

                if not self.groups[
                    key
                ]:
                    raise RuntimeError(
                        "Empty class/signer "
                        f"group: {key}"
                    )

        self.num_batches = max(
            len(indices)
            for indices
            in self.groups.values()
        )


    def __len__(
        self,
    ):
        return self.num_batches


    def __iter__(
        self,
    ):

        rng = random.Random(
            self.seed
            + self.epoch
        )

        shuffled = {}

        for key, indices in (
            self.groups.items()
        ):

            values = list(
                indices
            )

            rng.shuffle(
                values
            )

            shuffled[
                key
            ] = values

        for batch_index in range(
            self.num_batches
        ):

            batch = []

            for class_id in (
                self.classes
            ):

                for signer in (
                    self.signers
                ):

                    values = shuffled[
                        (
                            class_id,
                            signer,
                        )
                    ]

                    index = values[
                        batch_index
                        % len(values)
                    ]

                    batch.append(
                        index
                    )

            rng.shuffle(
                batch
            )

            yield batch

        self.epoch += 1


def cross_signer_supcon_loss(
    projection,
    labels,
    signer_ids,
    temperature,
):
    """
    Positives:
        same class
        AND
        different signer

    Negatives:
        every other non-self sample.
    """

    batch_size = (
        projection.shape[0]
    )

    similarity = (
        projection
        @ projection.T
    ) / temperature

    eye = torch.eye(
        batch_size,
        dtype=torch.bool,
        device=projection.device,
    )

    same_class = (
        labels.unsqueeze(0)
        ==
        labels.unsqueeze(1)
    )

    different_signer = (
        signer_ids.unsqueeze(0)
        !=
        signer_ids.unsqueeze(1)
    )

    positive_mask = (
        same_class
        &
        different_signer
        &
        ~eye
    )

    non_self_mask = (
        ~eye
    )

    row_max = (
        similarity.masked_fill(
            eye,
            float("-inf"),
        )
        .max(
            dim=1,
            keepdim=True,
        )
        .values
        .detach()
    )

    stable_similarity = (
        similarity
        - row_max
    )

    exp_logits = (
        torch.exp(
            stable_similarity
        )
        * non_self_mask.to(
            projection.dtype
        )
    )

    denominator = (
        exp_logits.sum(
            dim=1,
            keepdim=True,
        )
        .clamp_min(
            1e-12
        )
    )

    log_prob = (
        stable_similarity
        - torch.log(
            denominator
        )
    )

    positive_count = (
        positive_mask.sum(
            dim=1
        )
    )

    valid_anchor = (
        positive_count > 0
    )

    if not bool(
        valid_anchor.any()
    ):
        raise RuntimeError(
            "Contrastive batch has no "
            "cross-signer positives."
        )

    positive_log_prob = (
        (
            log_prob
            * positive_mask.to(
                log_prob.dtype
            )
        )
        .sum(
            dim=1
        )
        /
        positive_count.clamp_min(
            1
        )
    )

    return -positive_log_prob[
        valid_anchor
    ].mean()


def run_train_epoch(
    model,
    loader,
    criterion,
    optimizer,
    device,
    contrastive_weight,
    temperature,
):
    model.train()

    total_loss = 0.0
    total_ce = 0.0
    total_contrastive = 0.0
    total_correct = 0
    total_count = 0

    for (
        x,
        y,
        signer_ids,
    ) in loader:

        x = x.to(
            device
        )

        y = y.to(
            device
        )

        signer_ids = (
            signer_ids.to(
                device
            )
        )

        optimizer.zero_grad(
            set_to_none=True
        )

        logits, projection = model(
            x,
            return_projection=True,
        )

        ce_loss = criterion(
            logits,
            y,
        )

        contrastive_loss = (
            cross_signer_supcon_loss(
                projection=
                    projection,
                labels=y,
                signer_ids=
                    signer_ids,
                temperature=
                    temperature,
            )
        )

        loss = (
            ce_loss
            +
            contrastive_weight
            * contrastive_loss
        )

        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            1.0,
        )

        optimizer.step()

        batch_size = y.size(
            0
        )

        total_loss += (
            float(
                loss.item()
            )
            * batch_size
        )

        total_ce += (
            float(
                ce_loss.item()
            )
            * batch_size
        )

        total_contrastive += (
            float(
                contrastive_loss.item()
            )
            * batch_size
        )

        predictions = (
            logits.argmax(
                dim=1
            )
        )

        total_correct += int(
            (
                predictions == y
            )
            .sum()
            .item()
        )

        total_count += (
            batch_size
        )

    return {
        "loss":
            total_loss
            / total_count,

        "ce":
            total_ce
            / total_count,

        "contrastive":
            total_contrastive
            / total_count,

        "accuracy":
            total_correct
            / total_count,
    }


def run_eval_epoch(
    model,
    loader,
    criterion,
    device,
):
    model.eval()

    total_loss = 0.0
    total_correct = 0
    total_count = 0

    with torch.no_grad():

        for (
            x,
            y,
            _,
        ) in loader:

            x = x.to(
                device
            )

            y = y.to(
                device
            )

            logits = model(
                x
            )

            loss = criterion(
                logits,
                y,
            )

            batch_size = (
                y.size(0)
            )

            total_loss += (
                float(
                    loss.item()
                )
                * batch_size
            )

            predictions = (
                logits.argmax(
                    dim=1
                )
            )

            total_correct += int(
                (
                    predictions == y
                )
                .sum()
                .item()
            )

            total_count += (
                batch_size
            )

    return (
        total_loss
        / total_count,

        total_correct
        / total_count,
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

        for (
            x,
            y,
            _,
        ) in loader:

            x = x.to(
                device
            )

            y = y.to(
                device
            )

            logits = model(
                x
            )

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
                .any(
                    dim=1
                )
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

    precisions = []
    recalls = []
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

        precisions.append(
            precision
        )

        recalls.append(
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
            top1_correct
            / total,

        "top3_accuracy":
            top3_correct
            / total,

        "macro_precision":
            sum(
                precisions
            )
            / num_classes,

        "macro_recall":
            sum(
                recalls
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
    counts = Counter(
        old_to_new[
            record.class_id
        ]
        for record
        in records
    )

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
        "--projection-size",
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
        "--contrastive-weight",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.10,
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

    if (
        args.validation_signer
        == args.test_signer
    ):
        raise RuntimeError(
            "Validation and test signer "
            "must be different."
        )

    if (
        args.validation_signer
        in TRAIN_SIGNERS
        or args.test_signer
        in TRAIN_SIGNERS
    ):
        raise RuntimeError(
            "Validation/test signer overlaps "
            "with training signers."
        )

    set_seed(
        args.seed
    )

    catalog = load_catalog()

    all_records = load_manifest(
        catalog=catalog,
        usable_only=True,
    )

    active_signs = [
        sign
        for sign
        in catalog.signs
        if sign.sign_id
        not in INACTIVE_SIGN_IDS
    ]

    if len(
        active_signs
    ) != 12:
        raise RuntimeError(
            "Expected 12 active signs, "
            f"got {len(active_signs)}"
        )

    active_signs = sorted(
        active_signs,
        key=lambda sign:
            sign.class_id,
    )

    active_old_ids = {
        sign.class_id
        for sign
        in active_signs
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
        for record
        in all_records
        if record.class_id
        in active_old_ids
    ]

    train_records = [
        record
        for record
        in records
        if record.signer_id
        in TRAIN_SIGNERS
    ]

    validation_records = [
        record
        for record
        in records
        if record.signer_id
        ==
        args.validation_signer
    ]

    test_records = [
        record
        for record
        in records
        if record.signer_id
        ==
        args.test_signer
    ]

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

    signer_to_index = {
        signer:
            index
        for index, signer
        in enumerate(
            TRAIN_SIGNERS
        )
    }

    signer_to_index[
        args.validation_signer
    ] = len(
        signer_to_index
    )

    signer_to_index[
        args.test_signer
    ] = len(
        signer_to_index
    )

    print()
    print(
        "========================================"
    )
    print(
        " SignBridge Cross-Signer Contrastive"
    )
    print(
        "========================================"
    )

    print(
        "Train signers      :",
        list(
            TRAIN_SIGNERS
        ),
    )

    print(
        "Validation signers :",
        [
            args.validation_signer
        ],
    )

    print(
        "Test signers       :",
        [
            args.test_signer
        ],
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

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
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

    print(
        "Contrastive weight:",
        args.contrastive_weight,
    )

    print(
        "Temperature       :",
        args.temperature,
    )

    train_dataset = (
        ContrastiveDataset(
            train_records,
            old_to_new,
            signer_to_index,
        )
    )

    validation_dataset = (
        ContrastiveDataset(
            validation_records,
            old_to_new,
            signer_to_index,
        )
    )

    test_dataset = (
        ContrastiveDataset(
            test_records,
            old_to_new,
            signer_to_index,
        )
    )

    batch_sampler = (
        CrossSignerClassBatchSampler(
            records=train_records,
            old_to_new=
                old_to_new,
            train_signers=
                TRAIN_SIGNERS,
            seed=args.seed,
        )
    )

    print(
        "Balanced batch size:",
        (
            12
            * len(
                TRAIN_SIGNERS
            )
        ),
    )

    print(
        "Batches per epoch :",
        len(
            batch_sampler
        ),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_sampler=
            batch_sampler,
        num_workers=0,
        pin_memory=
            device.type
            == "cuda",
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=64,
        shuffle=False,
        num_workers=0,
        pin_memory=
            device.type
            == "cuda",
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=64,
        shuffle=False,
        num_workers=0,
        pin_memory=
            device.type
            == "cuda",
    )

    model = (
        BiLSTMContrastiveBaseline(
            num_classes=12,
            hidden_size=
                args.hidden_size,
            projection_size=
                args.projection_size,
        )
        .to(
            device
        )
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
        "bilstm_contrastive_"
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

        train_result = (
            run_train_epoch(
                model=model,
                loader=
                    train_loader,
                criterion=
                    criterion,
                optimizer=
                    optimizer,
                device=device,
                contrastive_weight=
                    args.contrastive_weight,
                temperature=
                    args.temperature,
            )
        )

        val_loss, val_acc = (
            run_eval_epoch(
                model=model,
                loader=
                    validation_loader,
                criterion=
                    criterion,
                device=device,
            )
        )

        print(
            f"Epoch {epoch:03d} | "
            f"loss {train_result['loss']:.4f} | "
            f"ce {train_result['ce']:.4f} | "
            f"supcon {train_result['contrastive']:.4f} | "
            f"train acc {train_result['accuracy']:.3f} | "
            f"val loss {val_loss:.4f} | "
            f"val acc {val_acc:.3f}"
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

                    "model":
                        "BiLSTMContrastiveBaseline",

                    "num_classes":
                        12,

                    "hidden_size":
                        args.hidden_size,

                    "projection_size":
                        args.projection_size,

                    "contrastive_weight":
                        args.contrastive_weight,

                    "temperature":
                        args.temperature,

                    "seed":
                        args.seed,

                    "best_epoch":
                        best_epoch,

                    "best_validation_loss":
                        best_validation_loss,

                    "train_signers":
                        list(
                            TRAIN_SIGNERS
                        ),

                    "validation_signers":
                        [
                            args.validation_signer
                        ],

                    "test_signers":
                        [
                            args.test_signer
                        ],

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
            >= args.patience
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
        model=model,
        loader=test_loader,
        device=device,
        num_classes=12,
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

        "model":
            "BiLSTMContrastiveBaseline",

        "dataset_snapshot_sha256":
            "E4AE9B57ABAEFE285E5C4B9398DB19C3E79B2D423C7EE5105D11B30C863DABB7",

        "seed":
            args.seed,

        "contrastive_weight":
            args.contrastive_weight,

        "temperature":
            args.temperature,

        "best_epoch":
            checkpoint[
                "best_epoch"
            ],

        "best_validation_loss":
            checkpoint[
                "best_validation_loss"
            ],

        "train_signers":
            list(
                TRAIN_SIGNERS
            ),

        "validation_signers":
            [
                args.validation_signer
            ],

        "test_signers":
            [
                args.test_signer
            ],

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
