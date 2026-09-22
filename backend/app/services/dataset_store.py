import json
from pathlib import Path

from app.models.dataset import (
    DatasetSampleRequest,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

DATA_ROOT = (
    PROJECT_ROOT
    / "data"
)

RAW_SAMPLE_DIR = (
    DATA_ROOT
    / "raw"
    / "samples"
)

MANIFEST_DIR = (
    DATA_ROOT
    / "manifests"
)

MANIFEST_PATH = (
    MANIFEST_DIR
    / "dataset_manifest.jsonl"
)


def ensure_dataset_directories(
) -> None:
    RAW_SAMPLE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def save_dataset_sample(
    sample:
        DatasetSampleRequest,
) -> tuple[
    Path,
    bool,
]:
    ensure_dataset_directories()

    sample_path = (
        RAW_SAMPLE_DIR
        / f"{sample.sample_id}.json"
    )

    if sample_path.exists():
        raise FileExistsError(
            "Sample already exists: "
            f"{sample.sample_id}"
        )

    sample_dict = (
        sample.model_dump(
            mode="json"
        )
    )

    with sample_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            sample_dict,
            file,
            ensure_ascii=False,
            indent=2,
        )


    manifest_record = {
        "schema_version":
            sample.schema_version,

        "sample_id":
            sample.sample_id,

        "signer_id":
            sample.signer_id,

        "sign_id":
            sample.sign_id,

        "take_id":
            sample.take_id,

        "label":
            sample.label,

        "raw_frame_count":
            sample.capture
            .raw_frame_count,

        "duration_ms":
            sample.capture
            .duration_ms,

        "input_usable":
            sample.quality
            .input_usable,

        "landmark_valid_ratio":
            sample.quality
            .landmark_valid_ratio,

        "shoulder_usable_ratio":
            sample.quality
            .shoulder_usable_ratio,

        "left_hand_usable_ratio":
            sample.quality
            .left_hand_usable_ratio,

        "right_hand_usable_ratio":
            sample.quality
            .right_hand_usable_ratio,

        "both_hands_usable_ratio":
            sample.quality
            .both_hands_usable_ratio,

        "active_hand":
            sample.quality
            .active_hand,

        "sample_path":
            sample_path
            .relative_to(
                PROJECT_ROOT
            )
            .as_posix(),
    }


    with MANIFEST_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                manifest_record,
                ensure_ascii=False,
            )
            + "\n"
        )

    return (
        sample_path,
        True,
    )
