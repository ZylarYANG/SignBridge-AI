import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.models.collector import (
    CollectorProfile,
    CollectorProfileUpdate,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

METADATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "metadata"
)

SIGNERS_PATH = (
    METADATA_DIR
    / "signers.json"
)


def _normalize_signer_id(
    signer_id: str,
) -> str:
    normalized = (
        signer_id
        .strip()
        .upper()
    )

    if not re.fullmatch(
        r"S\d{3,}",
        normalized,
    ):
        raise ValueError(
            "Invalid signer_id. "
            "Expected format such as S001."
        )

    return normalized


def _empty_database() -> dict:
    return {
        "schema_version": "1.0",
        "signers": {},
    }


def _read_database() -> dict:
    if not SIGNERS_PATH.exists():
        return _empty_database()

    with SIGNERS_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        data = json.load(file)

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Invalid signers metadata file."
        )

    if "signers" not in data:
        data["signers"] = {}

    return data


def _write_database(
    data: dict,
) -> None:
    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = (
        SIGNERS_PATH
        .with_suffix(".json.tmp")
    )

    with temp_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temp_path.replace(
        SIGNERS_PATH
    )


def _default_profile(
    signer_id: str,
) -> CollectorProfile:
    return CollectorProfile(
        signer_id=signer_id,
        source_type="other",
        age_group="unspecified",
        gender="unspecified",
        dominant_hand="unspecified",
        consent_confirmed=False,
        note="",
        created_at=None,
        updated_at=None,
    )


def get_collector_profile(
    signer_id: str,
) -> tuple[
    CollectorProfile,
    bool,
]:
    normalized = (
        _normalize_signer_id(
            signer_id
        )
    )

    database = (
        _read_database()
    )

    raw_profile = (
        database["signers"]
        .get(normalized)
    )

    if raw_profile is None:
        return (
            _default_profile(
                normalized
            ),
            False,
        )

    return (
        CollectorProfile(
            **raw_profile
        ),
        True,
    )


def list_collector_profiles(
) -> list[CollectorProfile]:
    database = (
        _read_database()
    )

    profiles = [
        CollectorProfile(
            **profile
        )
        for profile
        in database[
            "signers"
        ].values()
    ]

    profiles.sort(
        key=lambda item:
            item.signer_id
    )

    return profiles


def save_collector_profile(
    signer_id: str,
    update: CollectorProfileUpdate,
) -> CollectorProfile:
    normalized = (
        _normalize_signer_id(
            signer_id
        )
    )

    database = (
        _read_database()
    )

    now = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    existing = (
        database["signers"]
        .get(normalized)
    )

    created_at = (
        existing.get(
            "created_at"
        )
        if existing
        else now
    )

    profile = CollectorProfile(
        signer_id=
            normalized,

        source_type=
            update.source_type,

        age_group=
            update.age_group,

        gender=
            update.gender,

        dominant_hand=
            update.dominant_hand,

        consent_confirmed=
            update.consent_confirmed,

        note=
            update.note.strip(),

        created_at=
            created_at,

        updated_at=
            now,
    )

    database[
        "signers"
    ][normalized] = (
        profile.model_dump(
            mode="json"
        )
    )

    _write_database(
        database
    )

    return profile
