import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.models.dataset import DatasetSampleRequest


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_ROOT = PROJECT_ROOT / "data"

RAW_SAMPLE_DIR = DATA_ROOT / "raw" / "samples"

MANIFEST_DIR = DATA_ROOT / "manifests"

MANIFEST_PATH = (
    MANIFEST_DIR
    / "dataset_manifest.jsonl"
)


def ensure_dataset_directories() -> None:
    RAW_SAMPLE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def _read_manifest_records() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []

    records: list[dict] = []

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        for raw_line in file:
            line = raw_line.strip()

            if not line:
                continue

            records.append(
                json.loads(line)
            )

    return records


def _write_manifest_records(
    records: list[dict],
) -> None:
    ensure_dataset_directories()

    if not records:
        MANIFEST_PATH.unlink(
            missing_ok=True
        )
        return

    temp_path = (
        MANIFEST_PATH
        .with_suffix(".jsonl.tmp")
    )

    with temp_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    temp_path.replace(
        MANIFEST_PATH
    )


def save_dataset_sample(
    sample: DatasetSampleRequest,
) -> tuple[Path, bool]:
    ensure_dataset_directories()

    sample_path = (
        RAW_SAMPLE_DIR
        / f"{sample.sample_id}.json"
    )

    existing_records = (
        _read_manifest_records()
    )

    if (
        sample_path.exists()
        or any(
            record.get("sample_id")
            == sample.sample_id
            for record
            in existing_records
        )
    ):
        raise FileExistsError(
            "Sample already exists: "
            f"{sample.sample_id}"
        )

    created_at = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    sample_dict = sample.model_dump(
        mode="json"
    )

    sample_dict[
        "created_at"
    ] = created_at

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

        "collection_profile":
            sample.collection_profile,

        "collection_session_id":
            sample.collection_session_id,

        "created_at":
            created_at,

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

    existing_records.append(
        manifest_record
    )

    _write_manifest_records(
        existing_records
    )

    return (
        sample_path,
        True,
    )


def list_dataset_samples(
    signer_id: str | None = None,
    sign_id: str | None = None,
) -> list[dict]:
    records = (
        _read_manifest_records()
    )

    if signer_id is not None:
        normalized_signer = (
            signer_id
            .strip()
            .upper()
        )

        records = [
            record
            for record
            in records
            if (
                record.get(
                    "signer_id"
                )
                == normalized_signer
            )
        ]

    if sign_id is not None:
        records = [
            record
            for record
            in records
            if (
                record.get(
                    "sign_id"
                )
                == sign_id
            )
        ]

    records.sort(
        key=lambda record: (
            str(
                record.get(
                    "sign_id",
                    "",
                )
            ),
            int(
                record.get(
                    "take_id",
                    0,
                )
            ),
        )
    )

    return records


def delete_dataset_sample(
    sample_id: str,
) -> dict:
    if not re.fullmatch(
        r"[A-Za-z0-9_-]+",
        sample_id,
    ):
        raise ValueError(
            "Invalid sample_id."
        )

    records = (
        _read_manifest_records()
    )

    target = next(
        (
            record
            for record
            in records
            if (
                record.get(
                    "sample_id"
                )
                == sample_id
            )
        ),
        None,
    )

    if target is None:
        raise FileNotFoundError(
            "Sample not found: "
            f"{sample_id}"
        )

    raw_path = str(
        target.get(
            "sample_path",
            "",
        )
    )

    sample_path = (
        PROJECT_ROOT
        / raw_path
    ).resolve()

    raw_root = (
        RAW_SAMPLE_DIR
        .resolve()
    )

    if not sample_path.is_relative_to(
        raw_root
    ):
        raise ValueError(
            "Unsafe sample path."
        )

    file_deleted = False

    if sample_path.exists():
        sample_path.unlink()
        file_deleted = True

    remaining_records = [
        record
        for record
        in records
        if (
            record.get(
                "sample_id"
            )
            != sample_id
        )
    ]

    _write_manifest_records(
        remaining_records
    )

    return {
        "status":
            "deleted",

        "sample_id":
            sample_id,

        "file_deleted":
            file_deleted,

        "manifest_updated":
            True,
    }
