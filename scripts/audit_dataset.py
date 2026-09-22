from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from training.dataset_loader import (
    load_catalog,
    load_manifest,
    load_sample,
)


def percentage(
    value: float,
) -> str:
    return (
        f"{value * 100:.1f}%"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit SignBridge "
            "dataset integrity."
        )
    )

    parser.add_argument(
        "--usable-only",
        action="store_true",
        help=(
            "Audit only samples marked "
            "input_usable=true."
        ),
    )

    args = parser.parse_args()

    catalog = load_catalog()

    print()
    print(
        "========================================"
    )
    print(
        " SignBridge Dataset Audit"
    )
    print(
        "========================================"
    )

    print(
        f"Catalog schema : "
        f"{catalog.schema_version}"
    )

    print(
        f"Classes        : "
        f"{len(catalog.signs)}"
    )

    records = load_manifest(
        catalog=catalog,
        usable_only=args.usable_only,
    )

    print(
        f"Manifest rows  : "
        f"{len(records)}"
    )

    if not records:
        print()
        print(
            "Dataset is currently empty."
        )
        print(
            "No integrity errors found."
        )
        print()

        return 0

    signer_counts = Counter(
        record.signer_id
        for record in records
    )

    class_counts = Counter(
        record.class_id
        for record in records
    )

    active_hand_counts = Counter(
        record.active_hand
        for record in records
    )

    usable_count = sum(
        1
        for record in records
        if record.input_usable
    )

    print(
        f"Usable samples : "
        f"{usable_count}"
    )

    print(
        f"Rejected       : "
        f"{len(records) - usable_count}"
    )

    print(
        f"Signers        : "
        f"{len(signer_counts)}"
    )

    errors: list[str] = []

    for record in records:
        try:
            load_sample(
                record
            )

        except Exception as exc:
            errors.append(
                f"{record.sample_id}: "
                f"{exc}"
            )

    print()
    print(
        "---------- Samples by signer ----------"
    )

    for signer_id in sorted(
        signer_counts
    ):
        print(
            f"{signer_id:<12} "
            f"{signer_counts[signer_id]}"
        )

    print()
    print(
        "----------- Samples by class ----------"
    )

    for sign in catalog.signs:
        count = class_counts.get(
            sign.class_id,
            0,
        )

        print(
            f"{sign.class_id:>2}  "
            f"{sign.sign_id:<20} "
            f"{sign.label:<8} "
            f"{count}"
        )

    print()
    print(
        "----------- Active hand ---------------"
    )

    for hand in (
        "left",
        "right",
        "both",
        "none",
    ):
        print(
            f"{hand:<8} "
            f"{active_hand_counts.get(hand, 0)}"
        )

    average_landmark_ratio = (
        sum(
            record.landmark_valid_ratio
            for record in records
        )
        / len(records)
    )

    average_shoulder_ratio = (
        sum(
            record.shoulder_usable_ratio
            for record in records
        )
        / len(records)
    )

    print()
    print(
        "----------- Quality -------------------"
    )

    print(
        "Average landmark validity : "
        f"{percentage(average_landmark_ratio)}"
    )

    print(
        "Average shoulder usability: "
        f"{percentage(average_shoulder_ratio)}"
    )

    print()
    print(
        "----------- Integrity -----------------"
    )

    if errors:
        print(
            f"FAILED: "
            f"{len(errors)} "
            "invalid sample(s)"
        )

        for error in errors:
            print(
                f"  - {error}"
            )

        print()

        return 1

    print(
        "PASS: all sample files "
        "are structurally valid."
    )

    print(
        "Expected model shape: "
        "[64, 54, 2]"
    )

    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
