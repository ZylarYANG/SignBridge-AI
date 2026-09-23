from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


SourceType = Literal[
    "team_member",
    "friend_or_roommate",
    "volunteer",
    "other",
]

AgeGroup = Literal[
    "under_18",
    "18_25",
    "26_40",
    "41_60",
    "60_plus",
    "unspecified",
]

GenderType = Literal[
    "male",
    "female",
    "other",
    "prefer_not_to_say",
    "unspecified",
]

DominantHand = Literal[
    "left",
    "right",
    "both",
    "unspecified",
]


class CollectorProfileUpdate(BaseModel):
    source_type: SourceType = "other"

    age_group: AgeGroup = "unspecified"

    gender: GenderType = "unspecified"

    dominant_hand: DominantHand = "unspecified"

    consent_confirmed: bool = False

    note: str = Field(
        default="",
        max_length=1000,
    )


class CollectorProfile(BaseModel):
    signer_id: str

    source_type: SourceType

    age_group: AgeGroup

    gender: GenderType

    dominant_hand: DominantHand

    consent_confirmed: bool

    note: str

    created_at: str | None = None

    updated_at: str | None = None
