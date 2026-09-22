import json
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


def save_dataset_sample(
    sample: DatasetSampleRequest,
) -> tuple[Path, bool]:
    """
    保存完整样本 JSON，并向 JSONL manifest
    追加一条索引记录。

    不允许同 sample_id 覆盖已有数据。
    """

    ensure_dataset_directories()

    sample_path = (
        RAW_SAMPLE_DIR
        / f"{sample.sample_id}.json"
    )

    if sample_path.exists():
        raise FileExistsError(
            f"Sample already exists: "
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
            sample.capture.raw_frame_count,

        "duration_ms":
            sample.capture.duration_ms,

        "input_usable":
            sample.quality.input_usable,

        "landmark_valid_ratio":
            sample.quality.landmark_valid_ratio,

        "sample_path":
            sample_path.relative_to(
                PROJECT_ROOT
            ).as_posix(),
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

    return sample_path, True