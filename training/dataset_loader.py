from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CATALOG_PATH = (
    PROJECT_ROOT
    / "config"
    / "sign_catalog.json"
)

DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "manifests"
    / "dataset_manifest.jsonl"
)

EXPECTED_SEQUENCE_LENGTH = 64
EXPECTED_LANDMARK_COUNT = 54
EXPECTED_COORDINATE_COUNT = 2


class DatasetError(RuntimeError):
    """Base exception for dataset loading."""


class DatasetValidationError(DatasetError):
    """Raised when one sample is invalid."""


@dataclass(frozen=True)
class SignDefinition:
    class_id: int
    sign_id: str
    label: str
    handedness_policy: str
    required_parts: tuple[str, ...]
    direction_reference: str
    direction_sensitive: bool


@dataclass(frozen=True)
class DatasetRecord:
    sample_id: str
    signer_id: str
    sign_id: str
    class_id: int
    label: str
    take_id: int

    input_usable: bool
    active_hand: str

    sample_path: Path

    raw_frame_count: int
    duration_ms: float

    landmark_valid_ratio: float
    shoulder_usable_ratio: float
    left_hand_usable_ratio: float
    right_hand_usable_ratio: float
    both_hands_usable_ratio: float


@dataclass
class LoadedSample:
    record: DatasetRecord
    model_input: list[list[list[float]]]
    raw_frames: list[dict[str, Any]]
    payload: dict[str, Any]


@dataclass
class DatasetCatalog:
    schema_version: str
    signs: tuple[SignDefinition, ...]
    by_sign_id: dict[str, SignDefinition]
    by_class_id: dict[int, SignDefinition]


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as file:
            value = json.load(file)

    except FileNotFoundError as exc:
        raise DatasetError(
            f"File not found: {path}"
        ) from exc

    except json.JSONDecodeError as exc:
        raise DatasetError(
            f"Invalid JSON: {path} "
            f"(line {exc.lineno}, "
            f"column {exc.colno})"
        ) from exc

    if not isinstance(value, dict):
        raise DatasetError(
            f"Expected top-level JSON object: {path}"
        )

    return value


def load_catalog(
    path: Path | None = None,
) -> DatasetCatalog:
    catalog_path = (
        path
        if path is not None
        else CATALOG_PATH
    )

    payload = _read_json_file(
        catalog_path
    )

    schema_version = str(
        payload.get(
            "schema_version",
            "",
        )
    )

    raw_signs = payload.get(
        "signs"
    )

    if not isinstance(
        raw_signs,
        list,
    ):
        raise DatasetError(
            "sign_catalog.json must contain "
            "a signs array."
        )

    signs: list[SignDefinition] = []

    by_sign_id: dict[
        str,
        SignDefinition,
    ] = {}

    by_class_id: dict[
        int,
        SignDefinition,
    ] = {}

    for item in raw_signs:
        if not isinstance(
            item,
            dict,
        ):
            raise DatasetError(
                "Each catalog sign must "
                "be an object."
            )

        sign = SignDefinition(
            class_id=int(
                item["class_id"]
            ),
            sign_id=str(
                item["sign_id"]
            ),
            label=str(
                item["label"]
            ),
            handedness_policy=str(
                item["handedness_policy"]
            ),
            required_parts=tuple(
                str(part)
                for part in item.get(
                    "required_parts",
                    [],
                )
            ),
            direction_reference=str(
                item["direction_reference"]
            ),
            direction_sensitive=bool(
                item.get(
                    "direction_sensitive",
                    False,
                )
            ),
        )

        if sign.sign_id in by_sign_id:
            raise DatasetError(
                "Duplicate sign_id in catalog: "
                f"{sign.sign_id}"
            )

        if sign.class_id in by_class_id:
            raise DatasetError(
                "Duplicate class_id in catalog: "
                f"{sign.class_id}"
            )

        signs.append(sign)

        by_sign_id[
            sign.sign_id
        ] = sign

        by_class_id[
            sign.class_id
        ] = sign

    expected_class_ids = list(
        range(
            len(signs)
        )
    )

    actual_class_ids = sorted(
        by_class_id
    )

    if actual_class_ids != expected_class_ids:
        raise DatasetError(
            "Catalog class_id values must "
            "be continuous from 0. "
            f"Expected {expected_class_ids}, "
            f"got {actual_class_ids}."
        )

    return DatasetCatalog(
        schema_version=schema_version,
        signs=tuple(signs),
        by_sign_id=by_sign_id,
        by_class_id=by_class_id,
    )


def _resolve_sample_path(
    raw_path: str,
) -> Path:
    path = Path(
        raw_path
    )

    if not path.is_absolute():
        path = (
            PROJECT_ROOT
            / path
        )

    return path.resolve()


def load_manifest(
    manifest_path: Path | None = None,
    catalog: DatasetCatalog | None = None,
    usable_only: bool = False,
) -> list[DatasetRecord]:
    path = (
        manifest_path
        if manifest_path is not None
        else DEFAULT_MANIFEST_PATH
    )

    if not path.exists():
        return []

    active_catalog = (
        catalog
        if catalog is not None
        else load_catalog()
    )

    records: list[
        DatasetRecord
    ] = []

    seen_sample_ids: set[
        str
    ] = set()

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        for line_number, raw_line in enumerate(
            file,
            start=1,
        ):
            line = raw_line.strip()

            if not line:
                continue

            try:
                item = json.loads(
                    line
                )

            except json.JSONDecodeError as exc:
                raise DatasetError(
                    "Invalid manifest JSON "
                    f"at line {line_number}: "
                    f"{exc}"
                ) from exc

            if not isinstance(
                item,
                dict,
            ):
                raise DatasetError(
                    "Manifest line "
                    f"{line_number} "
                    "must contain a JSON object."
                )

            sample_id = str(
                item["sample_id"]
            )

            sign_id = str(
                item["sign_id"]
            )

            if sample_id in seen_sample_ids:
                raise DatasetError(
                    "Duplicate sample_id "
                    "in manifest: "
                    f"{sample_id}"
                )

            seen_sample_ids.add(
                sample_id
            )

            sign = (
                active_catalog
                .by_sign_id
                .get(sign_id)
            )

            if sign is None:
                raise DatasetError(
                    "Unknown sign_id "
                    "in manifest line "
                    f"{line_number}: "
                    f"{sign_id}"
                )

            input_usable = bool(
                item.get(
                    "input_usable",
                    False,
                )
            )

            if (
                usable_only
                and not input_usable
            ):
                continue

            record = DatasetRecord(
                sample_id=sample_id,
                signer_id=str(
                    item["signer_id"]
                ),
                sign_id=sign_id,
                class_id=sign.class_id,
                label=str(
                    item.get(
                        "label",
                        sign.label,
                    )
                ),
                take_id=int(
                    item["take_id"]
                ),
                input_usable=input_usable,
                active_hand=str(
                    item.get(
                        "active_hand",
                        "none",
                    )
                ),
                sample_path=_resolve_sample_path(
                    str(
                        item["sample_path"]
                    )
                ),
                raw_frame_count=int(
                    item.get(
                        "raw_frame_count",
                        0,
                    )
                ),
                duration_ms=float(
                    item.get(
                        "duration_ms",
                        0.0,
                    )
                ),
                landmark_valid_ratio=float(
                    item.get(
                        "landmark_valid_ratio",
                        0.0,
                    )
                ),
                shoulder_usable_ratio=float(
                    item.get(
                        "shoulder_usable_ratio",
                        0.0,
                    )
                ),
                left_hand_usable_ratio=float(
                    item.get(
                        "left_hand_usable_ratio",
                        0.0,
                    )
                ),
                right_hand_usable_ratio=float(
                    item.get(
                        "right_hand_usable_ratio",
                        0.0,
                    )
                ),
                both_hands_usable_ratio=float(
                    item.get(
                        "both_hands_usable_ratio",
                        0.0,
                    )
                ),
            )

            records.append(
                record
            )

    return records


def validate_model_input(
    model_input: Any,
) -> None:
    if not isinstance(
        model_input,
        list,
    ):
        raise DatasetValidationError(
            "model_input must be a list."
        )

    if (
        len(model_input)
        != EXPECTED_SEQUENCE_LENGTH
    ):
        raise DatasetValidationError(
            "Expected "
            f"{EXPECTED_SEQUENCE_LENGTH} "
            "frames, got "
            f"{len(model_input)}."
        )

    for frame_index, frame in enumerate(
        model_input
    ):
        if not isinstance(
            frame,
            list,
        ):
            raise DatasetValidationError(
                f"Frame {frame_index} "
                "must be a list."
            )

        if (
            len(frame)
            != EXPECTED_LANDMARK_COUNT
        ):
            raise DatasetValidationError(
                f"Frame {frame_index}: "
                "expected "
                f"{EXPECTED_LANDMARK_COUNT} "
                "landmarks, got "
                f"{len(frame)}."
            )

        for landmark_index, point in enumerate(
            frame
        ):
            if not isinstance(
                point,
                list,
            ):
                raise DatasetValidationError(
                    f"Frame {frame_index}, "
                    f"landmark {landmark_index}: "
                    "point must be a list."
                )

            if (
                len(point)
                != EXPECTED_COORDINATE_COUNT
            ):
                raise DatasetValidationError(
                    f"Frame {frame_index}, "
                    f"landmark {landmark_index}: "
                    "expected "
                    f"{EXPECTED_COORDINATE_COUNT} "
                    "coordinates."
                )

            for coordinate in point:
                if isinstance(
                    coordinate,
                    bool,
                ):
                    raise DatasetValidationError(
                        "Boolean coordinate "
                        "is not allowed."
                    )

                if not isinstance(
                    coordinate,
                    (int, float),
                ):
                    raise DatasetValidationError(
                        "Coordinates must be numeric."
                    )

                if not math.isfinite(
                    float(coordinate)
                ):
                    raise DatasetValidationError(
                        "Coordinates must be finite."
                    )


def load_sample(
    record: DatasetRecord,
) -> LoadedSample:
    if not record.sample_path.exists():
        raise DatasetValidationError(
            "Sample file missing: "
            f"{record.sample_path}"
        )

    payload = _read_json_file(
        record.sample_path
    )

    if (
        str(
            payload.get(
                "sample_id",
                "",
            )
        )
        != record.sample_id
    ):
        raise DatasetValidationError(
            "sample_id mismatch: "
            f"{record.sample_id}"
        )

    if (
        str(
            payload.get(
                "signer_id",
                "",
            )
        )
        != record.signer_id
    ):
        raise DatasetValidationError(
            "signer_id mismatch: "
            f"{record.sample_id}"
        )

    if (
        str(
            payload.get(
                "sign_id",
                "",
            )
        )
        != record.sign_id
    ):
        raise DatasetValidationError(
            "sign_id mismatch: "
            f"{record.sample_id}"
        )

    if (
        int(
            payload.get(
                "take_id",
                -1,
            )
        )
        != record.take_id
    ):
        raise DatasetValidationError(
            "take_id mismatch: "
            f"{record.sample_id}"
        )

    model_input = payload.get(
        "model_input"
    )

    validate_model_input(
        model_input
    )

    raw_frames = payload.get(
        "raw_frames"
    )

    if not isinstance(
        raw_frames,
        list,
    ):
        raise DatasetValidationError(
            "raw_frames must be "
            "a list: "
            f"{record.sample_id}"
        )

    if (
        len(raw_frames)
        != record.raw_frame_count
    ):
        raise DatasetValidationError(
            "raw_frame_count mismatch: "
            f"{record.sample_id} "
            f"manifest={record.raw_frame_count}, "
            f"file={len(raw_frames)}"
        )

    return LoadedSample(
        record=record,
        model_input=model_input,
        raw_frames=raw_frames,
        payload=payload,
    )


def iter_samples(
    records: Iterable[
        DatasetRecord
    ],
) -> Iterable[
    LoadedSample
]:
    for record in records:
        yield load_sample(
            record
        )


def get_training_arrays(
    records: Iterable[
        DatasetRecord
    ],
) -> tuple[
    list[list[list[list[float]]]],
    list[int],
    list[str],
    list[str],
]:
    """
    Returns:

    X:
        [N, 64, 54, 2]

    y:
        [N] class IDs

    signer_ids:
        [N]

    sample_ids:
        [N]
    """

    X: list[
        list[
            list[
                list[float]
            ]
        ]
    ] = []

    y: list[int] = []

    signer_ids: list[
        str
    ] = []

    sample_ids: list[
        str
    ] = []

    for sample in iter_samples(
        records
    ):
        X.append(
            sample.model_input
        )

        y.append(
            sample.record.class_id
        )

        signer_ids.append(
            sample.record.signer_id
        )

        sample_ids.append(
            sample.record.sample_id
        )

    return (
        X,
        y,
        signer_ids,
        sample_ids,
    )


def split_records_by_signer(
    records: list[
        DatasetRecord
    ],
    train_signers: set[str],
    validation_signers: set[str],
    test_signers: set[str],
) -> tuple[
    list[DatasetRecord],
    list[DatasetRecord],
    list[DatasetRecord],
]:
    overlap = (
        train_signers
        & validation_signers
    ) | (
        train_signers
        & test_signers
    ) | (
        validation_signers
        & test_signers
    )

    if overlap:
        raise DatasetError(
            "Signer leakage detected. "
            "The following signer IDs "
            "appear in multiple splits: "
            f"{sorted(overlap)}"
        )

    train: list[
        DatasetRecord
    ] = []

    validation: list[
        DatasetRecord
    ] = []

    test: list[
        DatasetRecord
    ] = []

    known_signers = (
        train_signers
        | validation_signers
        | test_signers
    )

    for record in records:
        signer_id = (
            record.signer_id
        )

        if signer_id not in known_signers:
            raise DatasetError(
                "Signer has no assigned "
                "dataset split: "
                f"{signer_id}"
            )

        if signer_id in train_signers:
            train.append(
                record
            )

        elif (
            signer_id
            in validation_signers
        ):
            validation.append(
                record
            )

        else:
            test.append(
                record
            )

    return (
        train,
        validation,
        test,
    )
