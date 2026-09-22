from __future__ import annotations

import random
from dataclasses import dataclass

from training.dataset_loader import (
    DatasetError,
    DatasetRecord,
    split_records_by_signer,
)


@dataclass(frozen=True)
class SignerSplit:
    train_signers: tuple[str, ...]
    validation_signers: tuple[str, ...]
    test_signers: tuple[str, ...]


def make_signer_split(
    records: list[DatasetRecord],
    seed: int = 42,
) -> SignerSplit:
    signers = sorted(
        {
            record.signer_id
            for record in records
        }
    )

    if len(signers) < 3:
        raise DatasetError(
            "At least 3 distinct signers are required. "
            f"Current signer count: {len(signers)}"
        )

    rng = random.Random(seed)
    rng.shuffle(signers)

    signer_count = len(signers)

    test_count = max(
        1,
        round(signer_count * 0.15),
    )

    validation_count = max(
        1,
        round(signer_count * 0.15),
    )

    while (
        signer_count
        - test_count
        - validation_count
        < 1
    ):
        if validation_count > 1:
            validation_count -= 1
        elif test_count > 1:
            test_count -= 1
        else:
            break

    test_signers = tuple(
        sorted(
            signers[:test_count]
        )
    )

    validation_signers = tuple(
        sorted(
            signers[
                test_count:
                test_count + validation_count
            ]
        )
    )

    train_signers = tuple(
        sorted(
            signers[
                test_count + validation_count:
            ]
        )
    )

    return SignerSplit(
        train_signers=train_signers,
        validation_signers=validation_signers,
        test_signers=test_signers,
    )


def apply_signer_split(
    records: list[DatasetRecord],
    split: SignerSplit,
) -> tuple[
    list[DatasetRecord],
    list[DatasetRecord],
    list[DatasetRecord],
]:
    return split_records_by_signer(
        records=records,
        train_signers=set(split.train_signers),
        validation_signers=set(split.validation_signers),
        test_signers=set(split.test_signers),
    )
