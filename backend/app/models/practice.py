from pydantic import BaseModel, Field


class PracticeRequest(BaseModel):
    request_id: str
    target_sign_id: str

    raw_frame_count: int = Field(ge=1)
    sequence_length: int = Field(ge=1)

    # Expected runtime shape:
    # [64, 54, 2]
    landmarks: list[list[list[float]]]


class PracticeResponse(BaseModel):
    status: str
    mode: str

    request_id: str
    target_sign_id: str

    received_shape: tuple[int, int, int]

    message: str
