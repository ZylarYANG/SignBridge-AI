from typing import Literal

from pydantic import BaseModel, Field


class RawLandmarkPoint(BaseModel):
    x: float
    y: float
    valid: bool


class RawLandmarkFrame(BaseModel):
    timestamp_ms: float

    landmarks: list[
        RawLandmarkPoint
    ]


class CaptureMetadata(BaseModel):
    duration_ms: float = Field(gt=0)
    raw_frame_count: int = Field(gt=0)


class SampleQuality(BaseModel):
    input_usable: bool
    landmark_valid_ratio: float = Field(
        ge=0.0,
        le=1.0,
    )


class DatasetSampleRequest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"

    sample_id: str

    signer_id: str
    sign_id: str

    take_id: int = Field(ge=1)

    label: str

    capture: CaptureMetadata

    quality: SampleQuality

    raw_frames: list[
        RawLandmarkFrame
    ]

    model_input: list[
        list[
            list[float]
        ]
    ]


class DatasetSampleResponse(BaseModel):
    status: str

    sample_id: str

    file_path: str

    manifest_updated: bool