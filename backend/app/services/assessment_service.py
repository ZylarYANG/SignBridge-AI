from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_SAMPLE_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "samples"
)

EXPECTED_SHAPE = (64, 54, 2)

LEFT_HAND = slice(0, 21)
RIGHT_HAND = slice(21, 42)

HAND_SLICES = {
    "left": LEFT_HAND,
    "right": RIGHT_HAND,
}

SCORE_THRESHOLD = 70.0

# A distance equal to the S001 calibration scale
# receives about 85 points.
SCORE_DECAY = 0.16251892949777494

EPSILON = 1e-6


class AssessmentServiceError(RuntimeError):
    pass


@dataclass
class ReferenceBundle:
    sign_id: str
    prototype: np.ndarray
    active_hands: tuple[str, ...]
    sample_count: int

    handshape_scale: float
    trajectory_scale: float
    position_scale: float


def _point_valid_mask(
    points: np.ndarray,
) -> np.ndarray:
    return (
        np.linalg.norm(
            points,
            axis=-1,
        )
        > EPSILON
    )


def _hand_centroid_path(
    sequence: np.ndarray,
    hand: str,
) -> np.ndarray | None:
    hand_slice = HAND_SLICES[hand]

    points = sequence[
        :,
        hand_slice,
        :
    ]

    valid = _point_valid_mask(
        points
    )

    centroids = np.full(
        (
            sequence.shape[0],
            2,
        ),
        np.nan,
        dtype=np.float32,
    )

    for frame_index in range(
        sequence.shape[0]
    ):
        frame_valid = valid[
            frame_index
        ]

        if frame_valid.sum() < 5:
            continue

        centroids[
            frame_index
        ] = points[
            frame_index,
            frame_valid,
        ].mean(
            axis=0
        )

    finite = np.isfinite(
        centroids
    ).all(
        axis=1
    )

    indices = np.flatnonzero(
        finite
    )

    if len(indices) < 2:
        return None

    frame_indices = np.arange(
        sequence.shape[0]
    )

    interpolated = np.empty_like(
        centroids
    )

    for coordinate in range(2):
        interpolated[
            :,
            coordinate
        ] = np.interp(
            frame_indices,
            indices,
            centroids[
                indices,
                coordinate,
            ],
        )

    return interpolated


def _hand_coverage(
    sequence: np.ndarray,
    hand: str,
) -> float:
    points = sequence[
        :,
        HAND_SLICES[hand],
        :
    ]

    valid = _point_valid_mask(
        points
    )

    usable_frames = (
        valid.sum(
            axis=1
        )
        >= 8
    )

    return float(
        usable_frames.mean()
    )


def _normalized_hand_frame(
    points: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
] | None:
    valid = _point_valid_mask(
        points
    )

    if valid.sum() < 8:
        return None

    if not valid[0]:
        return None

    wrist = points[0]

    scale_candidates: list[float] = []

    for index in (
        5,
        9,
        13,
        17,
    ):
        if valid[index]:
            scale_candidates.append(
                float(
                    np.linalg.norm(
                        points[index]
                        - wrist
                    )
                )
            )

    if not scale_candidates:
        return None

    scale = float(
        np.mean(
            scale_candidates
        )
    )

    if scale <= EPSILON:
        return None

    normalized = (
        points - wrist
    ) / scale

    return (
        normalized,
        valid,
    )


def _handshape_distance(
    candidate: np.ndarray,
    reference: np.ndarray,
    active_hands: tuple[str, ...],
) -> float:
    distances: list[float] = []

    for hand in active_hands:
        hand_slice = (
            HAND_SLICES[hand]
        )

        for frame_index in range(
            candidate.shape[0]
        ):
            candidate_frame = (
                _normalized_hand_frame(
                    candidate[
                        frame_index,
                        hand_slice,
                        :,
                    ]
                )
            )

            reference_frame = (
                _normalized_hand_frame(
                    reference[
                        frame_index,
                        hand_slice,
                        :,
                    ]
                )
            )

            if (
                candidate_frame is None
                or reference_frame is None
            ):
                continue

            (
                candidate_normalized,
                candidate_valid,
            ) = candidate_frame

            (
                reference_normalized,
                reference_valid,
            ) = reference_frame

            common = (
                candidate_valid
                & reference_valid
            )

            if common.sum() < 8:
                continue

            frame_distance = (
                np.linalg.norm(
                    candidate_normalized[
                        common
                    ]
                    - reference_normalized[
                        common
                    ],
                    axis=1,
                )
                .mean()
            )

            distances.append(
                float(
                    frame_distance
                )
            )

    if not distances:
        return math.inf

    return float(
        np.mean(
            distances
        )
    )


def _dtw_distance(
    first: np.ndarray,
    second: np.ndarray,
) -> float:
    first_relative = (
        first - first[0]
    )

    second_relative = (
        second - second[0]
    )

    n = len(first_relative)
    m = len(second_relative)

    matrix = np.full(
        (
            n + 1,
            m + 1,
        ),
        np.inf,
        dtype=np.float64,
    )

    matrix[0, 0] = 0.0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = float(
                np.linalg.norm(
                    first_relative[i - 1]
                    - second_relative[j - 1]
                )
            )

            matrix[i, j] = (
                cost
                + min(
                    matrix[i - 1, j],
                    matrix[i, j - 1],
                    matrix[i - 1, j - 1],
                )
            )

    return float(
        matrix[n, m]
        / max(
            1,
            n + m,
        )
    )


def _trajectory_distance(
    candidate: np.ndarray,
    reference: np.ndarray,
    active_hands: tuple[str, ...],
) -> float:
    distances: list[float] = []

    for hand in active_hands:
        candidate_path = (
            _hand_centroid_path(
                candidate,
                hand,
            )
        )

        reference_path = (
            _hand_centroid_path(
                reference,
                hand,
            )
        )

        if (
            candidate_path is None
            or reference_path is None
        ):
            continue

        distances.append(
            _dtw_distance(
                candidate_path,
                reference_path,
            )
        )

    if not distances:
        return math.inf

    return float(
        np.mean(
            distances
        )
    )


def _position_distance(
    candidate: np.ndarray,
    reference: np.ndarray,
    active_hands: tuple[str, ...],
) -> float:
    distances: list[float] = []

    for hand in active_hands:
        candidate_path = (
            _hand_centroid_path(
                candidate,
                hand,
            )
        )

        reference_path = (
            _hand_centroid_path(
                reference,
                hand,
            )
        )

        if (
            candidate_path is None
            or reference_path is None
        ):
            continue

        path_distance = float(
            np.linalg.norm(
                candidate_path
                - reference_path,
                axis=1,
            ).mean()
        )

        start_distance = float(
            np.linalg.norm(
                candidate_path[0]
                - reference_path[0]
            )
        )

        end_distance = float(
            np.linalg.norm(
                candidate_path[-1]
                - reference_path[-1]
            )
        )

        distances.append(
            (
                path_distance
                + 0.5 * start_distance
                + 0.5 * end_distance
            )
            / 2.0
        )

    if not distances:
        return math.inf

    return float(
        np.mean(
            distances
        )
    )


def _safe_scale(
    values: list[float],
    minimum: float,
) -> float:
    usable = np.asarray(
        [
            value
            for value in values
            if math.isfinite(value)
        ],
        dtype=np.float64,
    )

    if len(usable) == 0:
        return minimum

    percentile_90 = float(
        np.quantile(
            usable,
            0.90,
        )
    )

    median = float(
        np.median(
            usable
        )
    )

    return max(
        minimum,
        percentile_90,
        median * 1.25,
    )


def _score(
    distance: float,
    scale: float,
) -> float:
    if not math.isfinite(
        distance
    ):
        return 0.0

    ratio = (
        distance
        / max(
            scale,
            EPSILON,
        )
    )

    result = (
        100.0
        * math.exp(
            -SCORE_DECAY
            * ratio
        )
    )

    return round(
        max(
            0.0,
            min(
                100.0,
                result,
            ),
        ),
        1,
    )


class AssessmentService:
    def __init__(
        self,
        reference_signer: str | None = None,
    ) -> None:
        self.reference_signer = (
            reference_signer
            or os.getenv(
                "SIGNBRIDGE_REFERENCE_SIGNER",
                "S001",
            )
        ).strip().upper()

        self._reference_cache: dict[
            str,
            ReferenceBundle,
        ] = {}

    def _load_reference(
        self,
        sign_id: str,
    ) -> ReferenceBundle:
        cached = (
            self._reference_cache.get(
                sign_id
            )
        )

        if cached is not None:
            return cached

        pattern = (
            f"{self.reference_signer}_"
            f"{sign_id}_*.json"
        )

        paths = sorted(
            RAW_SAMPLE_DIR.glob(
                pattern
            )
        )

        sequences: list[np.ndarray] = []
        active_labels: list[str] = []

        for path in paths:
            try:
                payload = json.loads(
                    path.read_text(
                        encoding="utf-8-sig"
                    )
                )
            except (
                OSError,
                json.JSONDecodeError,
            ):
                continue

            if (
                payload.get("signer_id")
                != self.reference_signer
            ):
                continue

            if (
                payload.get("sign_id")
                != sign_id
            ):
                continue

            quality = (
                payload.get("quality")
                or {}
            )

            if (
                quality.get(
                    "input_usable",
                    True,
                )
                is False
            ):
                continue

            try:
                sequence = np.asarray(
                    payload[
                        "model_input"
                    ],
                    dtype=np.float32,
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            if (
                sequence.shape
                != EXPECTED_SHAPE
            ):
                continue

            if not np.isfinite(
                sequence
            ).all():
                continue

            sequences.append(
                sequence
            )

            active_hand = str(
                quality.get(
                    "active_hand",
                    "",
                )
            ).lower()

            if active_hand in {
                "left",
                "right",
                "both",
            }:
                active_labels.append(
                    active_hand
                )

        if not sequences:
            raise AssessmentServiceError(
                "No usable reference samples "
                f"for {self.reference_signer} "
                f"/ {sign_id}."
            )

        stack = np.stack(
            sequences,
            axis=0,
        )

        prototype = np.median(
            stack,
            axis=0,
        ).astype(
            np.float32
        )

        active_hands = (
            self._resolve_active_hands(
                active_labels,
                stack,
            )
        )

        handshape_distances: list[
            float
        ] = []

        trajectory_distances: list[
            float
        ] = []

        position_distances: list[
            float
        ] = []

        for sequence in sequences:
            handshape_distances.append(
                _handshape_distance(
                    sequence,
                    prototype,
                    active_hands,
                )
            )

            trajectory_distances.append(
                _trajectory_distance(
                    sequence,
                    prototype,
                    active_hands,
                )
            )

            position_distances.append(
                _position_distance(
                    sequence,
                    prototype,
                    active_hands,
                )
            )

        bundle = ReferenceBundle(
            sign_id=sign_id,
            prototype=prototype,
            active_hands=active_hands,
            sample_count=len(
                sequences
            ),
            handshape_scale=_safe_scale(
                handshape_distances,
                minimum=0.08,
            ),
            trajectory_scale=_safe_scale(
                trajectory_distances,
                minimum=0.04,
            ),
            position_scale=_safe_scale(
                position_distances,
                minimum=0.05,
            ),
        )

        self._reference_cache[
            sign_id
        ] = bundle

        return bundle

    def _resolve_active_hands(
        self,
        labels: list[str],
        stack: np.ndarray,
    ) -> tuple[str, ...]:
        if labels:
            counts = {
                "left":
                    labels.count(
                        "left"
                    ),
                "right":
                    labels.count(
                        "right"
                    ),
                "both":
                    labels.count(
                        "both"
                    ),
            }

            winner = max(
                counts,
                key=counts.get,
            )

            if (
                counts[winner]
                > 0
            ):
                if winner == "both":
                    return (
                        "left",
                        "right",
                    )

                return (
                    winner,
                )

        mean_sequence = (
            stack.mean(
                axis=0
            )
        )

        left_coverage = (
            _hand_coverage(
                mean_sequence,
                "left",
            )
        )

        right_coverage = (
            _hand_coverage(
                mean_sequence,
                "right",
            )
        )

        if (
            left_coverage >= 0.35
            and right_coverage >= 0.35
        ):
            return (
                "left",
                "right",
            )

        if (
            left_coverage
            >= right_coverage
        ):
            return (
                "left",
            )

        return (
            "right",
        )

    def reference_info(
        self,
        sign_id: str,
    ) -> dict[str, Any]:
        reference = (
            self._load_reference(
                sign_id
            )
        )

        return {
            "reference_signer":
                self.reference_signer,

            "sign_id":
                sign_id,

            "sample_count":
                reference.sample_count,

            "active_hands":
                list(
                    reference.active_hands
                ),

            "scales": {
                "handshape":
                    reference
                    .handshape_scale,

                "trajectory":
                    reference
                    .trajectory_scale,

                "position":
                    reference
                    .position_scale,
            },
        }

    def assess(
        self,
        sign_id: str,
        frames: list[
            list[
                list[float]
            ]
        ]
        | np.ndarray,
    ) -> dict[str, Any]:
        candidate = np.asarray(
            frames,
            dtype=np.float32,
        )

        if (
            candidate.shape
            != EXPECTED_SHAPE
        ):
            raise AssessmentServiceError(
                "Assessment expected shape "
                f"{EXPECTED_SHAPE}, "
                f"received {candidate.shape}."
            )

        if not np.isfinite(
            candidate
        ).all():
            raise AssessmentServiceError(
                "Assessment input contains "
                "NaN or infinite values."
            )

        reference = (
            self._load_reference(
                sign_id
            )
        )

        handshape_distance = (
            _handshape_distance(
                candidate,
                reference.prototype,
                reference.active_hands,
            )
        )

        trajectory_distance = (
            _trajectory_distance(
                candidate,
                reference.prototype,
                reference.active_hands,
            )
        )

        position_distance = (
            _position_distance(
                candidate,
                reference.prototype,
                reference.active_hands,
            )
        )

        handshape_score = _score(
            handshape_distance,
            reference.handshape_scale,
        )

        trajectory_score = _score(
            trajectory_distance,
            reference.trajectory_scale,
        )

        position_score = _score(
            position_distance,
            reference.position_scale,
        )

        overall = round(
            (
                handshape_score
                * 0.35
                +
                trajectory_score
                * 0.40
                +
                position_score
                * 0.25
            ),
            1,
        )

        coverage_values = [
            _hand_coverage(
                candidate,
                hand,
            )
            for hand
            in reference.active_hands
        ]

        input_usable = (
            bool(
                coverage_values
            )
            and min(
                coverage_values
            )
            >= 0.35
        )

        errors = (
            self._build_errors(
                candidate=candidate,
                reference=reference,
                handshape_score=
                    handshape_score,
                trajectory_score=
                    trajectory_score,
                position_score=
                    position_score,
            )
        )

        return {
            "evaluation": {
                "overall":
                    overall,

                "handshape": {
                    "score":
                        handshape_score,
                },

                "trajectory": {
                    "score":
                        trajectory_score,
                },

                "position": {
                    "score":
                        position_score,
                },
            },

            "errors":
                errors,

            "quality": {
                "input_usable":
                    input_usable,
            },
        }

    def _build_errors(
        self,
        *,
        candidate: np.ndarray,
        reference: ReferenceBundle,
        handshape_score: float,
        trajectory_score: float,
        position_score: float,
    ) -> list[dict[str, Any]]:
        errors: list[
            dict[str, Any]
        ] = []

        if (
            handshape_score
            < SCORE_THRESHOLD
        ):
            errors.append({
                "code":
                    "HANDSHAPE_MISMATCH",

                "severity":
                    self._severity(
                        handshape_score
                    ),
            })

        if (
            trajectory_score
            < SCORE_THRESHOLD
        ):
            errors.append({
                "code":
                    self
                    ._trajectory_error_code(
                        candidate,
                        reference,
                    ),

                "severity":
                    self._severity(
                        trajectory_score
                    ),
            })

        if (
            position_score
            < SCORE_THRESHOLD
        ):
            errors.append({
                "code":
                    self
                    ._position_error_code(
                        candidate,
                        reference,
                    ),

                "severity":
                    self._severity(
                        position_score
                    ),
            })

        errors.sort(
            key=lambda item:
                item["severity"],
            reverse=True,
        )

        return errors

    @staticmethod
    def _severity(
        score: float,
    ) -> float:
        value = (
            SCORE_THRESHOLD
            - score
        ) / SCORE_THRESHOLD

        return round(
            max(
                0.0,
                min(
                    1.0,
                    0.25 + value,
                ),
            ),
            3,
        )

    def _trajectory_error_code(
        self,
        candidate: np.ndarray,
        reference: ReferenceBundle,
    ) -> str:
        if (
            len(
                reference.active_hands
            )
            != 1
        ):
            return (
                "TRAJECTORY_MISMATCH"
            )

        hand = (
            reference.active_hands[0]
        )

        candidate_path = (
            _hand_centroid_path(
                candidate,
                hand,
            )
        )

        reference_path = (
            _hand_centroid_path(
                reference.prototype,
                hand,
            )
        )

        if (
            candidate_path is None
            or reference_path is None
        ):
            return (
                "TRAJECTORY_MISMATCH"
            )

        delta = (
            candidate_path.mean(
                axis=0
            )
            - reference_path.mean(
                axis=0
            )
        )

        prefix = (
            "LEFT_HAND"
            if hand == "left"
            else "RIGHT_HAND"
        )

        x_delta = float(
            delta[0]
        )

        y_delta = float(
            delta[1]
        )

        threshold = max(
            0.10,
            reference.position_scale,
        )

        if (
            abs(y_delta)
            >= abs(x_delta)
            and abs(y_delta)
            >= threshold
        ):
            if y_delta > 0:
                return (
                    f"{prefix}_PATH_TOO_LOW"
                )

            return (
                f"{prefix}_PATH_TOO_HIGH"
            )

        if abs(x_delta) >= threshold:
            if x_delta > 0:
                return (
                    f"{prefix}_PATH_TOO_RIGHT"
                )

            return (
                f"{prefix}_PATH_TOO_LEFT"
            )

        return (
            "TRAJECTORY_MISMATCH"
        )

    def _position_error_code(
        self,
        candidate: np.ndarray,
        reference: ReferenceBundle,
    ) -> str:
        if (
            len(
                reference.active_hands
            )
            != 1
        ):
            return (
                "POSITION_MISMATCH"
            )

        hand = (
            reference.active_hands[0]
        )

        candidate_path = (
            _hand_centroid_path(
                candidate,
                hand,
            )
        )

        reference_path = (
            _hand_centroid_path(
                reference.prototype,
                hand,
            )
        )

        if (
            candidate_path is None
            or reference_path is None
        ):
            return (
                "POSITION_MISMATCH"
            )

        delta = (
            candidate_path[0]
            - reference_path[0]
        )

        prefix = (
            "LEFT_HAND"
            if hand == "left"
            else "RIGHT_HAND"
        )

        x_delta = float(
            delta[0]
        )

        y_delta = float(
            delta[1]
        )

        threshold = max(
            0.10,
            reference.position_scale,
        )

        if (
            abs(y_delta)
            >= abs(x_delta)
            and abs(y_delta)
            >= threshold
        ):
            if y_delta > 0:
                return (
                    f"{prefix}_START_TOO_LOW"
                )

            return (
                f"{prefix}_START_TOO_HIGH"
            )

        if abs(x_delta) >= threshold:
            if x_delta > 0:
                return (
                    f"{prefix}_START_TOO_RIGHT"
                )

            return (
                f"{prefix}_START_TOO_LEFT"
            )

        return (
            "POSITION_MISMATCH"
        )


_assessment_service: (
    AssessmentService | None
) = None


def get_assessment_service(
) -> AssessmentService:
    global _assessment_service

    if _assessment_service is None:
        _assessment_service = (
            AssessmentService()
        )

    return _assessment_service
