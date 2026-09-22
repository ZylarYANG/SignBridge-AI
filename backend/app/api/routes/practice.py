from fastapi import APIRouter, HTTPException

from app.models.practice import (
    PracticeRequest,
    PracticeResponse,
)


router = APIRouter(
    prefix="/api",
    tags=["practice"],
)


EXPECTED_SEQUENCE_LENGTH = 64
EXPECTED_LANDMARK_COUNT = 54
EXPECTED_COORDINATE_COUNT = 2


@router.post(
    "/practice",
    response_model=PracticeResponse,
)
async def practice(
    payload: PracticeRequest,
) -> PracticeResponse:

    frames = payload.landmarks

    if payload.sequence_length != EXPECTED_SEQUENCE_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=(
                f"sequence_length must be "
                f"{EXPECTED_SEQUENCE_LENGTH}, "
                f"received {payload.sequence_length}."
            ),
        )

    if len(frames) != EXPECTED_SEQUENCE_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Expected {EXPECTED_SEQUENCE_LENGTH} frames, "
                f"received {len(frames)}."
            ),
        )

    for frame_index, frame in enumerate(frames):
        if len(frame) != EXPECTED_LANDMARK_COUNT:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Frame {frame_index}: expected "
                    f"{EXPECTED_LANDMARK_COUNT} landmarks, "
                    f"received {len(frame)}."
                ),
            )

        for point_index, point in enumerate(frame):
            if len(point) != EXPECTED_COORDINATE_COUNT:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Frame {frame_index}, "
                        f"landmark {point_index}: "
                        "expected [x, y]."
                    ),
                )

    return PracticeResponse(
        status="ok",
        mode="mock",
        request_id=payload.request_id,
        target_sign_id=payload.target_sign_id,
        received_shape=(
            len(frames),
            len(frames[0]),
            len(frames[0][0]),
        ),
        message=(
            "SignBridge landmark sequence "
            "received successfully."
        ),
    )
