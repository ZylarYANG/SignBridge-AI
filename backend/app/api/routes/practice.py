from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.practice import (
    PracticeRequest,
    PracticeResponse,
)

from app.services.assessment_service import (
    AssessmentServiceError,
    get_assessment_service,
)

from app.services.recognition_service import (
    RecognitionServiceError,
    get_recognition_service,
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

    if (
        payload.sequence_length
        != EXPECTED_SEQUENCE_LENGTH
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "sequence_length must be "
                f"{EXPECTED_SEQUENCE_LENGTH}, "
                "received "
                f"{payload.sequence_length}."
            ),
        )

    if (
        len(frames)
        != EXPECTED_SEQUENCE_LENGTH
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Expected "
                f"{EXPECTED_SEQUENCE_LENGTH} "
                "frames, received "
                f"{len(frames)}."
            ),
        )

    for (
        frame_index,
        frame,
    ) in enumerate(frames):

        if (
            len(frame)
            != EXPECTED_LANDMARK_COUNT
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Frame {frame_index}: "
                    "expected "
                    f"{EXPECTED_LANDMARK_COUNT} "
                    "landmarks, received "
                    f"{len(frame)}."
                ),
            )

        for (
            point_index,
            point,
        ) in enumerate(frame):

            if (
                len(point)
                != EXPECTED_COORDINATE_COUNT
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Frame {frame_index}, "
                        f"landmark {point_index}: "
                        "expected [x, y]."
                    ),
                )

    try:
        recognition_service = (
            get_recognition_service()
        )

        recognition = (
            recognition_service.predict(
                frames,
                top_k=3,
            )
        )

    except RecognitionServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    try:
        assessment_service = (
            get_assessment_service()
        )

        assessment = (
            assessment_service.assess(
                payload.target_sign_id,
                frames,
            )
        )

    except AssessmentServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    predicted_sign_id = (
        recognition[
            "prediction"
        ][
            "sign_id"
        ]
    )

    recognition_matches_target = (
        predicted_sign_id
        == payload.target_sign_id
    )

    return PracticeResponse(
        status="ok",
        mode="recognition_assessment",

        request_id=
            payload.request_id,

        target_sign_id=
            payload.target_sign_id,

        received_shape=(
            len(frames),
            len(frames[0]),
            len(frames[0][0]),
        ),

        recognition=
            recognition,

        recognition_matches_target=
            recognition_matches_target,

        evaluation=
            assessment[
                "evaluation"
            ],

        errors=
            assessment[
                "errors"
            ],

        quality=
            assessment[
                "quality"
            ],

        message=(
            "SignBridge recognition "
            "and assessment completed "
            "successfully."
        ),
    )
