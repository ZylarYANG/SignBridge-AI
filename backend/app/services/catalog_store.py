import json
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

CATALOG_PATH = (
    PROJECT_ROOT
    / "config"
    / "sign_catalog.json"
)


REQUIRED_QUALITY_KEYS = {
    "minimum_raw_frames",
    "minimum_shoulder_usable_ratio",
    "minimum_single_hand_usable_ratio",
    "minimum_both_hands_usable_ratio",
    "minimum_hand_landmark_ratio_per_frame",
}


def load_sign_catalog() -> dict:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            "Sign catalog not found: "
            f"{CATALOG_PATH}"
        )

    with CATALOG_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        catalog = json.load(file)

    if not isinstance(
        catalog,
        dict,
    ):
        raise ValueError(
            "Sign catalog must be a JSON object."
        )

    signs = catalog.get(
        "signs"
    )

    if not isinstance(
        signs,
        list,
    ) or not signs:
        raise ValueError(
            "Sign catalog must contain "
            "a non-empty signs list."
        )

    class_ids = [
        sign.get(
            "class_id"
        )
        for sign in signs
    ]

    sign_ids = [
        sign.get(
            "sign_id"
        )
        for sign in signs
    ]

    if any(
        not isinstance(
            class_id,
            int,
        )
        for class_id in class_ids
    ):
        raise ValueError(
            "Every sign must have "
            "an integer class_id."
        )

    if len(
        set(class_ids)
    ) != len(
        class_ids
    ):
        raise ValueError(
            "Duplicate class_id found "
            "in sign catalog."
        )

    if len(
        set(sign_ids)
    ) != len(
        sign_ids
    ):
        raise ValueError(
            "Duplicate sign_id found "
            "in sign catalog."
        )

    expected_class_ids = list(
        range(
            len(signs)
        )
    )

    if sorted(
        class_ids
    ) != expected_class_ids:
        raise ValueError(
            "class_id must be continuous "
            "from 0 to N-1."
        )

    quality_policy = (
        catalog.get(
            "quality_policy"
        )
    )

    if not isinstance(
        quality_policy,
        dict,
    ):
        raise ValueError(
            "quality_policy is missing."
        )

    missing_quality_keys = (
        REQUIRED_QUALITY_KEYS
        -
        set(
            quality_policy.keys()
        )
    )

    if missing_quality_keys:
        raise ValueError(
            "quality_policy is missing: "
            +
            ", ".join(
                sorted(
                    missing_quality_keys
                )
            )
        )

    model_input = catalog.get(
        "model_input"
    )

    if not isinstance(
        model_input,
        dict,
    ):
        raise ValueError(
            "model_input is missing."
        )

    if (
        model_input.get(
            "sequence_length"
        )
        != 64
    ):
        raise ValueError(
            "Current pipeline expects "
            "sequence_length = 64."
        )

    if (
        model_input.get(
            "landmark_count"
        )
        != 54
    ):
        raise ValueError(
            "Current pipeline expects "
            "landmark_count = 54."
        )

    signs.sort(
        key=lambda sign:
            sign["class_id"]
    )

    return catalog
