from pydantic import BaseModel, Field


class PracticeRequest(BaseModel):
    request_id: str
    target_sign_id: str

    raw_frame_count: int = Field(
        ge=1
    )

    sequence_length: int = Field(
        ge=1
    )

    # Expected runtime shape:
    # [64, 54, 2]
    landmarks: list[
        list[
            list[float]
        ]
    ]


class RecognitionCandidate(BaseModel):
    model_class_id: int
    original_class_id: int

    sign_id: str
    label: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class RecognitionResult(BaseModel):
    prediction: RecognitionCandidate

    top3: list[
        RecognitionCandidate
    ]

    checkpoint_name: str
    device: str

    dataset_snapshot_sha256: str


class AssessmentScore(BaseModel):
    score: float = Field(
        ge=0.0,
        le=100.0,
    )


class AssessmentEvaluation(BaseModel):
    overall: float = Field(
        ge=0.0,
        le=100.0,
    )

    handshape: AssessmentScore
    trajectory: AssessmentScore
    position: AssessmentScore


class AssessmentError(BaseModel):
    code: str

    severity: float = Field(
        ge=0.0,
        le=1.0,
    )


class AssessmentQuality(BaseModel):
    input_usable: bool


class PracticeResponse(BaseModel):
    status: str
    mode: str

    request_id: str
    target_sign_id: str

    received_shape: tuple[
        int,
        int,
        int,
    ]

    recognition: RecognitionResult

    recognition_matches_target: bool

    evaluation: AssessmentEvaluation

    errors: list[
        AssessmentError
    ]

    quality: AssessmentQuality

    message: str
