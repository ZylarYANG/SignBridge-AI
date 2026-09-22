from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.dataset import (
    DatasetSampleRequest,
    DatasetSampleResponse,
)

from app.services.dataset_store import (
    PROJECT_ROOT,
    save_dataset_sample,
)


router = APIRouter(
    prefix="/api/dataset",
    tags=["dataset"],
)


EXPECTED_MODEL_FRAMES = 64
EXPECTED_LANDMARKS = 54
EXPECTED_COORDINATES = 2


def validate_sample_shape(
    payload: DatasetSampleRequest,
) -> None:
    """
    检查 raw frame 和 model_input
    的关键 shape。
    """

    if (
        len(payload.raw_frames)
        != payload.capture.raw_frame_count
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "raw_frame_count does not "
                "match raw_frames length."
            ),
        )

    for (
        frame_index,
        frame,
    ) in enumerate(
        payload.raw_frames
    ):
        if len(frame.landmarks) != 54:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Raw frame "
                    f"{frame_index}: "
                    "expected 54 landmarks, "
                    f"received "
                    f"{len(frame.landmarks)}."
                ),
            )

    if (
        len(payload.model_input)
        != EXPECTED_MODEL_FRAMES
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "model_input must contain "
                "64 frames."
            ),
        )

    for (
        frame_index,
        frame,
    ) in enumerate(
        payload.model_input
    ):
        if (
            len(frame)
            != EXPECTED_LANDMARKS
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Model frame "
                    f"{frame_index}: "
                    "expected 54 landmarks."
                ),
            )

        for (
            point_index,
            point,
        ) in enumerate(frame):
            if (
                len(point)
                != EXPECTED_COORDINATES
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Model frame "
                        f"{frame_index}, "
                        f"point {point_index}: "
                        "expected [x, y]."
                    ),
                )


@router.post(
    "/samples",
    response_model=
        DatasetSampleResponse,
)
async def create_dataset_sample(
    payload: DatasetSampleRequest,
) -> DatasetSampleResponse:

    validate_sample_shape(
        payload
    )

    try:
        sample_path, manifest_updated = (
            save_dataset_sample(
                payload
            )
        )

    except FileExistsError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    relative_path = (
        sample_path
        .relative_to(PROJECT_ROOT)
        .as_posix()
    )

    return DatasetSampleResponse(
        status="saved",
        sample_id=
            payload.sample_id,
        file_path=
            relative_path,
        manifest_updated=
            manifest_updated,
    )