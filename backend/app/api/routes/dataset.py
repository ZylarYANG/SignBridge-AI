from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from app.models.dataset import (
    DatasetSampleRequest,
    DatasetSampleResponse,
)

from app.models.collector import (
    CollectorProfileUpdate,
)

from app.services.collector_store import (
    get_collector_profile,
    list_collector_profiles,
    save_collector_profile,
)

from app.services.dataset_store import (
    delete_dataset_sample,
    list_dataset_samples,
    save_dataset_sample,
)


router = APIRouter(
    prefix="/api/dataset",
    tags=["dataset"],
)


@router.post(
    "/samples",
    response_model=
        DatasetSampleResponse,
)
def create_dataset_sample(
    sample: DatasetSampleRequest,
) -> DatasetSampleResponse:

    if (
        len(sample.raw_frames)
        !=
        sample.capture.raw_frame_count
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "raw_frame_count does not "
                "match raw_frames length."
            ),
        )

    for frame_index, frame in enumerate(
        sample.raw_frames
    ):
        if len(
            frame.landmarks
        ) != 54:
            raise HTTPException(
                status_code=400,
                detail=(
                    "raw_frames"
                    f"[{frame_index}] "
                    "must contain "
                    "54 landmarks."
                ),
            )

    if len(
        sample.model_input
    ) != 64:
        raise HTTPException(
            status_code=400,
            detail=(
                "model_input must "
                "contain 64 frames."
            ),
        )

    for frame_index, frame in enumerate(
        sample.model_input
    ):
        if len(frame) != 54:
            raise HTTPException(
                status_code=400,
                detail=(
                    "model_input"
                    f"[{frame_index}] "
                    "must contain "
                    "54 landmarks."
                ),
            )

        for landmark_index, point in enumerate(
            frame
        ):
            if len(point) != 2:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "model_input"
                        f"[{frame_index}]"
                        f"[{landmark_index}] "
                        "must contain "
                        "2 coordinates."
                    ),
                )

    try:
        (
            sample_path,
            manifest_updated,
        ) = save_dataset_sample(
            sample
        )

    except FileExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return DatasetSampleResponse(
        status="saved",

        sample_id=
            sample.sample_id,

        file_path=
            sample_path
            .as_posix(),

        manifest_updated=
            manifest_updated,
    )


@router.get(
    "/samples"
)
def get_dataset_samples(
    signer_id: str = Query(
        ...,
        min_length=1,
    ),

    sign_id: str | None = Query(
        default=None,
    ),
) -> dict:
    records = (
        list_dataset_samples(
            signer_id=
                signer_id,

            sign_id=
                sign_id,
        )
    )

    return {
        "status":
            "ok",

        "count":
            len(records),

        "samples":
            records,
    }


@router.delete(
    "/samples/{sample_id}"
)
def remove_dataset_sample(
    sample_id: str,
) -> dict:
    try:
        return (
            delete_dataset_sample(
                sample_id
            )
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "/signers"
)
def get_signers() -> dict:
    profiles = (
        list_collector_profiles()
    )

    return {
        "status": "ok",

        "count":
            len(profiles),

        "signers": [
            profile.model_dump(
                mode="json"
            )
            for profile
            in profiles
        ],
    }


@router.get(
    "/signers/{signer_id}"
)
def get_signer_profile(
    signer_id: str,
) -> dict:
    try:
        profile, exists = (
            get_collector_profile(
                signer_id
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "ok",

        "exists":
            exists,

        "profile":
            profile.model_dump(
                mode="json"
            ),
    }


@router.put(
    "/signers/{signer_id}"
)
def update_signer_profile(
    signer_id: str,
    update:
        CollectorProfileUpdate,
) -> dict:
    try:
        profile = (
            save_collector_profile(
                signer_id,
                update,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "saved",

        "profile":
            profile.model_dump(
                mode="json"
            ),
    }
