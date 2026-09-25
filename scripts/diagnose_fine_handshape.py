from __future__ import annotations

import csv
import json
import math
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "manifests"
    / "dataset_manifest.jsonl"
)

CATALOG_PATH = (
    PROJECT_ROOT
    / "config"
    / "sign_catalog.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "output"
    / "fine_handshape_diagnosis"
)

PLOT_DIR = (
    OUTPUT_DIR
    / "plots"
)


TRAIN_SIGNERS = {
    "S001",
    "S002",
    "S003",
}

ALL_SIGNERS = [
    "S001",
    "S002",
    "S003",
    "S004",
    "S005",
]

INACTIVE_SIGNS = {
    "CSL_me",
    "CSL_please",
    "CSL_you",
}

FOCUS_SIGNS = {
    "CSL_bye",
    "CSL_hello",
    "CSL_what",
}

TARGET_CASES = [
    ("S004", "CSL_bye"),
    ("S005", "CSL_bye"),
    ("S004", "CSL_hello"),
    ("S005", "CSL_hello"),
    ("S004", "CSL_what"),
    ("S005", "CSL_what"),
]

HAND_POINT_COUNT = 21

PALM_ANCHORS = [
    5,
    9,
    13,
    17,
]

TRAJECTORY_POINTS = [
    0,   # wrist
    4,   # thumb tip
    8,   # index tip
    12,  # middle tip
    16,  # ring tip
    20,  # little tip
]

TRAJECTORY_STEPS = 24
SHAPE_PHASES = 3

MIN_HAND_VALID = 16


def safe_nanmean(
    array,
    axis=0,
):
    with warnings.catch_warnings():
        warnings.simplefilter(
            "ignore",
            category=RuntimeWarning,
        )

        return np.nanmean(
            array,
            axis=axis,
        )


def fmt(
    value,
    digits=4,
):
    if value is None:
        return "nan"

    value = float(value)

    if not math.isfinite(
        value
    ):
        return "nan"

    return (
        f"{value:.{digits}f}"
    )


def point_valid(
    point,
):
    return bool(
        point
        and point.get(
            "valid",
            False,
        )
    )


def load_catalog():
    data = json.loads(
        CATALOG_PATH.read_text(
            encoding="utf-8"
        )
    )

    return {
        sign["sign_id"]:
            sign
        for sign
        in data.get(
            "signs",
            []
        )
    }


def load_manifest():
    records = []

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:

        for line in handle:

            line = (
                line.strip()
            )

            if not line:
                continue

            row = json.loads(
                line
            )

            if not row.get(
                "input_usable",
                True,
            ):
                continue

            records.append(
                row
            )

    return records


def resolve_sample_path(
    record,
):
    raw_path = record.get(
        "sample_path"
    )

    if raw_path:
        path = Path(
            raw_path
        )

        if not path.is_absolute():
            path = (
                PROJECT_ROOT
                / path
            )

        if path.exists():
            return path

    fallback = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / "samples"
        / (
            record[
                "sample_id"
            ]
            + ".json"
        )
    )

    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        record[
            "sample_id"
        ]
    )


def shoulder_frame(
    landmarks,
):
    if len(
        landmarks
    ) < 54:
        return None

    left = landmarks[45]
    right = landmarks[46]

    if not (
        point_valid(left)
        and point_valid(right)
    ):
        return None

    lx = float(
        left["x"]
    )
    ly = float(
        left["y"]
    )

    rx = float(
        right["x"]
    )
    ry = float(
        right["y"]
    )

    width = math.hypot(
        lx - rx,
        ly - ry,
    )

    if width < 1e-6:
        return None

    return (
        (lx + rx) / 2.0,
        (ly + ry) / 2.0,
        width,
    )


def hand_valid_count(
    landmarks,
    start,
):
    return sum(
        1
        for point
        in landmarks[
            start:
            start + HAND_POINT_COUNT
        ]
        if point_valid(
            point
        )
    )


def normalized_handshape(
    landmarks,
    start,
):
    hand = landmarks[
        start:
        start + HAND_POINT_COUNT
    ]

    if len(
        hand
    ) != HAND_POINT_COUNT:
        return None

    if (
        hand_valid_count(
            landmarks,
            start,
        )
        < MIN_HAND_VALID
    ):
        return None

    wrist = hand[0]

    if not point_valid(
        wrist
    ):
        return None

    wx = float(
        wrist["x"]
    )
    wy = float(
        wrist["y"]
    )

    anchor_distances = []

    for index in (
        PALM_ANCHORS
    ):
        point = hand[
            index
        ]

        if not point_valid(
            point
        ):
            continue

        anchor_distances.append(
            math.hypot(
                float(
                    point["x"]
                ) - wx,
                float(
                    point["y"]
                ) - wy,
            )
        )

    if len(
        anchor_distances
    ) < 2:
        return None

    scale = float(
        np.mean(
            anchor_distances
        )
    )

    if scale < 1e-6:
        return None

    output = np.full(
        (
            HAND_POINT_COUNT,
            2,
        ),
        np.nan,
        dtype=np.float64,
    )

    for index, point in enumerate(
        hand
    ):
        if not point_valid(
            point
        ):
            continue

        output[
            index,
            0,
        ] = (
            float(
                point["x"]
            )
            - wx
        ) / scale

        output[
            index,
            1,
        ] = (
            float(
                point["y"]
            )
            - wy
        ) / scale

    return output


def body_trajectory_points(
    landmarks,
    start,
):
    transform = shoulder_frame(
        landmarks
    )

    if transform is None:
        return None

    cx, cy, scale = (
        transform
    )

    output = np.full(
        (
            len(
                TRAJECTORY_POINTS
            ),
            2,
        ),
        np.nan,
        dtype=np.float64,
    )

    valid_count = 0

    for output_index, local_index in enumerate(
        TRAJECTORY_POINTS
    ):
        point = landmarks[
            start
            + local_index
        ]

        if not point_valid(
            point
        ):
            continue

        output[
            output_index,
            0,
        ] = (
            float(
                point["x"]
            )
            - cx
        ) / scale

        output[
            output_index,
            1,
        ] = (
            float(
                point["y"]
            )
            - cy
        ) / scale

        valid_count += 1

    if valid_count < 3:
        return None

    return output


def select_active_hand(
    frames,
):
    left_scores = []
    right_scores = []

    for frame in frames:

        landmarks = frame.get(
            "landmarks",
            []
        )

        if len(
            landmarks
        ) < 42:
            continue

        left_scores.append(
            hand_valid_count(
                landmarks,
                0,
            )
        )

        right_scores.append(
            hand_valid_count(
                landmarks,
                21,
            )
        )

    left_mean = (
        float(
            np.mean(
                left_scores
            )
        )
        if left_scores
        else 0.0
    )

    right_mean = (
        float(
            np.mean(
                right_scores
            )
        )
        if right_scores
        else 0.0
    )

    return (
        "left"
        if left_mean
        > right_mean
        else "right"
    )


def phase_signature(
    frame_features,
):
    frame_count = len(
        frame_features
    )

    if frame_count == 0:
        return None

    sample_shape = None

    for item in (
        frame_features
    ):
        if item is not None:
            sample_shape = (
                item.shape
            )
            break

    if sample_shape is None:
        return None

    phase_vectors = []

    for phase in range(
        SHAPE_PHASES
    ):

        start = int(
            round(
                phase
                * frame_count
                / SHAPE_PHASES
            )
        )

        end = int(
            round(
                (
                    phase + 1
                )
                * frame_count
                / SHAPE_PHASES
            )
        )

        items = [
            frame_features[
                index
            ]
            for index in range(
                start,
                end,
            )
            if frame_features[
                index
            ] is not None
        ]

        if not items:
            mean = np.full(
                sample_shape,
                np.nan,
                dtype=np.float64,
            )
        else:
            mean = safe_nanmean(
                np.stack(
                    items,
                    axis=0,
                ),
                axis=0,
            )

        phase_vectors.append(
            mean.reshape(-1)
        )

    return np.concatenate(
        phase_vectors
    )


def interpolate_matrix(
    matrix,
    steps,
):
    matrix = np.asarray(
        matrix,
        dtype=np.float64,
    )

    if matrix.ndim != 2:
        raise ValueError(
            "matrix must be 2D"
        )

    frame_count = matrix.shape[0]
    feature_count = matrix.shape[1]

    if frame_count == 0:
        return None

    source_t = np.linspace(
        0.0,
        1.0,
        frame_count,
    )

    target_t = np.linspace(
        0.0,
        1.0,
        steps,
    )

    output = np.full(
        (
            steps,
            feature_count,
        ),
        np.nan,
        dtype=np.float64,
    )

    for feature_index in range(
        feature_count
    ):

        values = matrix[
            :,
            feature_index,
        ]

        mask = np.isfinite(
            values
        )

        count = int(
            mask.sum()
        )

        if count == 0:
            continue

        if count == 1:

            output[
                :,
                feature_index,
            ] = values[
                mask
            ][0]

            continue

        output[
            :,
            feature_index,
        ] = np.interp(
            target_t,
            source_t[
                mask
            ],
            values[
                mask
            ],
        )

    return output


def trajectory_signature(
    frame_features,
):
    sample_shape = None

    for item in (
        frame_features
    ):
        if item is not None:
            sample_shape = (
                item.shape
            )
            break

    if sample_shape is None:
        return None

    matrix = []

    for item in frame_features:

        if item is None:
            matrix.append(
                np.full(
                    sample_shape,
                    np.nan,
                    dtype=np.float64,
                ).reshape(-1)
            )
        else:
            matrix.append(
                item.reshape(-1)
            )

    resampled = (
        interpolate_matrix(
            np.stack(
                matrix,
                axis=0,
            ),
            TRAJECTORY_STEPS,
        )
    )

    if resampled is None:
        return None

    return resampled.reshape(
        -1
    )


def coverage(
    signature,
):
    if signature is None:
        return 0.0

    return float(
        np.isfinite(
            signature
        ).mean()
    )


def masked_rms(
    first,
    second,
):
    if (
        first is None
        or second is None
    ):
        return float(
            "nan"
        )

    if (
        first.shape
        != second.shape
    ):
        return float(
            "nan"
        )

    mask = (
        np.isfinite(
            first
        )
        &
        np.isfinite(
            second
        )
    )

    if int(
        mask.sum()
    ) < 10:
        return float(
            "nan"
        )

    delta = (
        first[
            mask
        ]
        - second[
            mask
        ]
    )

    return float(
        np.sqrt(
            np.mean(
                delta ** 2
            )
        )
    )


def prototype(
    signatures,
):
    valid = [
        item
        for item
        in signatures
        if item is not None
    ]

    if not valid:
        return None

    return safe_nanmean(
        np.stack(
            valid,
            axis=0,
        ),
        axis=0,
    )


def analyse_sample(
    record,
    catalog_entry,
):
    path = resolve_sample_path(
        record
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    frames = payload.get(
        "raw_frames",
        []
    )

    if not frames:
        raise RuntimeError(
            "Missing raw_frames: "
            + record[
                "sample_id"
            ]
        )

    policy = catalog_entry[
        "handedness_policy"
    ]

    selected_hand = (
        "both"
        if policy
        == "both_hands"
        else select_active_hand(
            frames
        )
    )

    handshape_frames = []
    trajectory_frames = []

    for frame in frames:

        landmarks = frame.get(
            "landmarks",
            []
        )

        if len(
            landmarks
        ) < 54:

            handshape_frames.append(
                None
            )

            trajectory_frames.append(
                None
            )

            continue

        if selected_hand == "right":

            shape = (
                normalized_handshape(
                    landmarks,
                    21,
                )
            )

            trajectory = (
                body_trajectory_points(
                    landmarks,
                    21,
                )
            )

        elif selected_hand == "left":

            shape = (
                normalized_handshape(
                    landmarks,
                    0,
                )
            )

            trajectory = (
                body_trajectory_points(
                    landmarks,
                    0,
                )
            )

        else:

            left_shape = (
                normalized_handshape(
                    landmarks,
                    0,
                )
            )

            right_shape = (
                normalized_handshape(
                    landmarks,
                    21,
                )
            )

            if (
                left_shape is None
                and right_shape is None
            ):
                shape = None
            else:

                if left_shape is None:
                    left_shape = np.full(
                        (
                            21,
                            2,
                        ),
                        np.nan,
                    )

                if right_shape is None:
                    right_shape = np.full(
                        (
                            21,
                            2,
                        ),
                        np.nan,
                    )

                shape = np.concatenate(
                    (
                        left_shape,
                        right_shape,
                    ),
                    axis=0,
                )

            left_trajectory = (
                body_trajectory_points(
                    landmarks,
                    0,
                )
            )

            right_trajectory = (
                body_trajectory_points(
                    landmarks,
                    21,
                )
            )

            if (
                left_trajectory is None
                and right_trajectory is None
            ):
                trajectory = None
            else:

                if (
                    left_trajectory
                    is None
                ):
                    left_trajectory = (
                        np.full(
                            (
                                len(
                                    TRAJECTORY_POINTS
                                ),
                                2,
                            ),
                            np.nan,
                        )
                    )

                if (
                    right_trajectory
                    is None
                ):
                    right_trajectory = (
                        np.full(
                            (
                                len(
                                    TRAJECTORY_POINTS
                                ),
                                2,
                            ),
                            np.nan,
                        )
                    )

                trajectory = (
                    np.concatenate(
                        (
                            left_trajectory,
                            right_trajectory,
                        ),
                        axis=0,
                    )
                )

        handshape_frames.append(
            shape
        )

        trajectory_frames.append(
            trajectory
        )

    shape_signature = (
        phase_signature(
            handshape_frames
        )
    )

    trajectory_sig = (
        trajectory_signature(
            trajectory_frames
        )
    )

    return {
        "sample_id":
            record[
                "sample_id"
            ],

        "signer_id":
            record[
                "signer_id"
            ],

        "sign_id":
            record[
                "sign_id"
            ],

        "policy":
            policy,

        "selected_hand":
            selected_hand,

        "frame_count":
            len(
                frames
            ),

        "shape_coverage":
            coverage(
                shape_signature
            ),

        "trajectory_coverage":
            coverage(
                trajectory_sig
            ),

        "_shape":
            shape_signature,

        "_trajectory":
            trajectory_sig,
    }


def write_csv(
    path,
    rows,
    fields,
):
    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()

        for row in rows:

            writer.writerow({
                field:
                    row.get(
                        field
                    )
                for field
                in fields
            })


def feature_prototype(
    rows,
    key,
):
    return prototype(
        [
            row[
                key
            ]
            for row
            in rows
        ]
    )


def reshape_trajectory(
    signature,
    policy,
):
    if signature is None:
        return None

    point_count = (
        len(
            TRAJECTORY_POINTS
        )
        if policy
        == "dominant_either"
        else 2
        * len(
            TRAJECTORY_POINTS
        )
    )

    expected = (
        TRAJECTORY_STEPS
        * point_count
        * 2
    )

    if signature.size != expected:
        return None

    return signature.reshape(
        TRAJECTORY_STEPS,
        point_count,
        2,
    )


def make_plot(
    signer_id,
    target_sign,
    target_trajectory,
    train_target,
    competitor_sign,
    competitor_trajectory,
    policy,
):
    try:
        import matplotlib.pyplot as plt

    except Exception:
        return False

    target = reshape_trajectory(
        target_trajectory,
        policy,
    )

    train = reshape_trajectory(
        train_target,
        policy,
    )

    competitor = reshape_trajectory(
        competitor_trajectory,
        policy,
    )

    if (
        target is None
        or train is None
        or competitor is None
    ):
        return False

    PLOT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(
            7.5,
            7.0,
        )
    )

    if policy == "dominant_either":

        point_index = 2

        plt.plot(
            target[
                :,
                point_index,
                0,
            ],
            target[
                :,
                point_index,
                1,
            ],
            marker="o",
            markersize=2.5,
            label=(
                f"{signer_id} "
                f"{target_sign}"
            ),
        )

        plt.plot(
            train[
                :,
                point_index,
                0,
            ],
            train[
                :,
                point_index,
                1,
            ],
            linestyle="--",
            label=(
                f"train "
                f"{target_sign}"
            ),
        )

        plt.plot(
            competitor[
                :,
                point_index,
                0,
            ],
            competitor[
                :,
                point_index,
                1,
            ],
            linestyle=":",
            label=(
                f"train "
                f"{competitor_sign}"
            ),
        )

    else:

        left_index = 2

        right_index = (
            len(
                TRAJECTORY_POINTS
            )
            + 2
        )

        plt.plot(
            target[
                :,
                left_index,
                0,
            ],
            target[
                :,
                left_index,
                1,
            ],
            marker="o",
            markersize=2,
            label=(
                f"{signer_id} "
                f"{target_sign} L"
            ),
        )

        plt.plot(
            target[
                :,
                right_index,
                0,
            ],
            target[
                :,
                right_index,
                1,
            ],
            marker="x",
            markersize=3,
            label=(
                f"{signer_id} "
                f"{target_sign} R"
            ),
        )

        plt.plot(
            train[
                :,
                left_index,
                0,
            ],
            train[
                :,
                left_index,
                1,
            ],
            linestyle="--",
            label=(
                f"train "
                f"{target_sign} L"
            ),
        )

        plt.plot(
            train[
                :,
                right_index,
                0,
            ],
            train[
                :,
                right_index,
                1,
            ],
            linestyle="--",
            label=(
                f"train "
                f"{target_sign} R"
            ),
        )

    plt.gca().invert_yaxis()

    plt.xlabel(
        "Shoulder-normalized X"
    )

    plt.ylabel(
        "Shoulder-normalized Y"
    )

    plt.title(
        f"{signer_id} / "
        f"{target_sign}\n"
        "Index fingertip trajectory"
    )

    plt.legend()

    plt.grid(
        alpha=0.25
    )

    plt.tight_layout()

    path = (
        PLOT_DIR
        / (
            signer_id
            + "_"
            + target_sign
            + "_index_tip.png"
        )
    )

    plt.savefig(
        path,
        dpi=180,
    )

    plt.close()

    return True


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    catalog = (
        load_catalog()
    )

    manifest = (
        load_manifest()
    )

    active_signs = {
        sign_id
        for sign_id
        in catalog
        if sign_id
        not in INACTIVE_SIGNS
    }

    records = [
        row
        for row in manifest
        if row.get(
            "signer_id"
        ) in ALL_SIGNERS
        and row.get(
            "sign_id"
        ) in active_signs
    ]

    analysed = []

    print()
    print(
        "Analysing fine-grained "
        "handshape / trajectory..."
    )

    for index, record in enumerate(
        records,
        start=1,
    ):

        analysed.append(
            analyse_sample(
                record,
                catalog[
                    record[
                        "sign_id"
                    ]
                ],
            )
        )

        if (
            index % 100
            == 0
        ):
            print(
                f"  {index}/"
                f"{len(records)}"
            )

    by_signer_sign = defaultdict(
        list
    )

    for row in analysed:

        by_signer_sign[
            (
                row[
                    "signer_id"
                ],
                row[
                    "sign_id"
                ],
            )
        ].append(
            row
        )

    quality_rows = []

    print()
    print(
        "=" * 110
    )
    print(
        "FINE FEATURE COVERAGE"
    )
    print(
        "=" * 110
    )

    print(
        "sign             signer   n "
        "hands                 "
        "shape_cov traj_cov"
    )

    for sign_id in sorted(
        FOCUS_SIGNS
    ):

        for signer_id in (
            ALL_SIGNERS
        ):

            rows = (
                by_signer_sign.get(
                    (
                        signer_id,
                        sign_id,
                    ),
                    [],
                )
            )

            if not rows:
                continue

            shape_cov = float(
                np.mean(
                    [
                        row[
                            "shape_coverage"
                        ]
                        for row in rows
                    ]
                )
            )

            traj_cov = float(
                np.mean(
                    [
                        row[
                            "trajectory_coverage"
                        ]
                        for row in rows
                    ]
                )
            )

            hands = Counter(
                row[
                    "selected_hand"
                ]
                for row in rows
            )

            hand_text = ",".join(
                f"{key}:{value}"
                for key, value
                in sorted(
                    hands.items()
                )
            )

            print(
                f"{sign_id:<16} "
                f"{signer_id:<7} "
                f"{len(rows):>2} "
                f"{hand_text:<21} "
                f"{shape_cov:>8.3f} "
                f"{traj_cov:>8.3f}"
            )

            quality_rows.append({
                "sign_id":
                    sign_id,

                "signer_id":
                    signer_id,

                "samples":
                    len(
                        rows
                    ),

                "selected_hands":
                    hand_text,

                "shape_coverage":
                    shape_cov,

                "trajectory_coverage":
                    traj_cov,
            })

    quality_csv = (
        OUTPUT_DIR
        / "fine_feature_coverage.csv"
    )

    write_csv(
        quality_csv,
        quality_rows,
        [
            "sign_id",
            "signer_id",
            "samples",
            "selected_hands",
            "shape_coverage",
            "trajectory_coverage",
        ],
    )

    train_prototypes = {}

    for sign_id in (
        active_signs
    ):

        rows = []

        for signer_id in (
            TRAIN_SIGNERS
        ):

            rows.extend(
                by_signer_sign.get(
                    (
                        signer_id,
                        sign_id,
                    ),
                    [],
                )
            )

        train_prototypes[
            sign_id
        ] = {
            "shape":
                feature_prototype(
                    rows,
                    "_shape",
                ),

            "trajectory":
                feature_prototype(
                    rows,
                    "_trajectory",
                ),
        }

    print()
    print(
        "=" * 110
    )
    print(
        "DISTANCE TO SAME-SIGN TRAIN REFERENCE"
    )
    print(
        "=" * 110
    )

    print(
        "sign             signer "
        "handshape_dist trajectory_dist"
    )

    distance_rows = []

    for sign_id in sorted(
        FOCUS_SIGNS
    ):

        for signer_id in (
            ALL_SIGNERS
        ):

            rows = (
                by_signer_sign.get(
                    (
                        signer_id,
                        sign_id,
                    ),
                    [],
                )
            )

            if not rows:
                continue

            test_shape = (
                feature_prototype(
                    rows,
                    "_shape",
                )
            )

            test_trajectory = (
                feature_prototype(
                    rows,
                    "_trajectory",
                )
            )

            if signer_id in (
                TRAIN_SIGNERS
            ):

                ref_rows = []

                for other in (
                    TRAIN_SIGNERS
                ):

                    if (
                        other
                        == signer_id
                    ):
                        continue

                    ref_rows.extend(
                        by_signer_sign.get(
                            (
                                other,
                                sign_id,
                            ),
                            [],
                        )
                    )

                ref_shape = (
                    feature_prototype(
                        ref_rows,
                        "_shape",
                    )
                )

                ref_trajectory = (
                    feature_prototype(
                        ref_rows,
                        "_trajectory",
                    )
                )

            else:

                ref_shape = (
                    train_prototypes[
                        sign_id
                    ][
                        "shape"
                    ]
                )

                ref_trajectory = (
                    train_prototypes[
                        sign_id
                    ][
                        "trajectory"
                    ]
                )

            shape_distance = (
                masked_rms(
                    test_shape,
                    ref_shape,
                )
            )

            trajectory_distance = (
                masked_rms(
                    test_trajectory,
                    ref_trajectory,
                )
            )

            print(
                f"{sign_id:<16} "
                f"{signer_id:<7} "
                f"{fmt(shape_distance):>14} "
                f"{fmt(trajectory_distance):>15}"
            )

            distance_rows.append({
                "sign_id":
                    sign_id,

                "signer_id":
                    signer_id,

                "handshape_distance":
                    shape_distance,

                "trajectory_distance":
                    trajectory_distance,
            })

    distance_csv = (
        OUTPUT_DIR
        / "fine_distance_to_train_reference.csv"
    )

    write_csv(
        distance_csv,
        distance_rows,
        [
            "sign_id",
            "signer_id",
            "handshape_distance",
            "trajectory_distance",
        ],
    )

    print()
    print(
        "=" * 110
    )
    print(
        "TARGET CASE CLASS RANKINGS"
    )
    print(
        "=" * 110
    )

    ranking_rows = []

    for signer_id, target_sign in (
        TARGET_CASES
    ):

        rows = (
            by_signer_sign.get(
                (
                    signer_id,
                    target_sign,
                ),
                [],
            )
        )

        if not rows:
            continue

        target_shape = (
            feature_prototype(
                rows,
                "_shape",
            )
        )

        target_trajectory = (
            feature_prototype(
                rows,
                "_trajectory",
            )
        )

        policy = (
            catalog[
                target_sign
            ][
                "handedness_policy"
            ]
        )

        print()
        print(
            f"{signer_id} / "
            f"{target_sign}"
        )

        feature_results = {}

        for feature_name, test_feature in (
            (
                "handshape",
                target_shape,
            ),
            (
                "trajectory",
                target_trajectory,
            ),
        ):

            candidates = []

            for candidate_sign in (
                active_signs
            ):

                if (
                    catalog[
                        candidate_sign
                    ][
                        "handedness_policy"
                    ]
                    != policy
                ):
                    continue

                reference = (
                    train_prototypes[
                        candidate_sign
                    ][
                        "shape"
                        if feature_name
                        == "handshape"
                        else "trajectory"
                    ]
                )

                distance = (
                    masked_rms(
                        test_feature,
                        reference,
                    )
                )

                if math.isfinite(
                    distance
                ):
                    candidates.append(
                        (
                            distance,
                            candidate_sign,
                        )
                    )

            candidates.sort(
                key=lambda item:
                    item[0]
            )

            feature_results[
                feature_name
            ] = candidates

            print(
                f"  [{feature_name}]"
            )

            target_rank = None

            for rank, (
                distance,
                candidate_sign,
            ) in enumerate(
                candidates,
                start=1,
            ):

                if (
                    candidate_sign
                    == target_sign
                ):
                    target_rank = rank

                if rank <= 5:

                    marker = (
                        " <-- target"
                        if candidate_sign
                        == target_sign
                        else ""
                    )

                    print(
                        f"    #{rank:<2} "
                        f"{candidate_sign:<18} "
                        f"{fmt(distance)}"
                        f"{marker}"
                    )

                ranking_rows.append({
                    "signer_id":
                        signer_id,

                    "target_sign":
                        target_sign,

                    "feature":
                        feature_name,

                    "candidate_sign":
                        candidate_sign,

                    "rank":
                        rank,

                    "distance":
                        distance,
                })

            print(
                "    target rank: "
                + (
                    str(
                        target_rank
                    )
                    if target_rank
                    is not None
                    else "NA"
                )
            )

        trajectory_candidates = (
            feature_results.get(
                "trajectory",
                [],
            )
        )

        competitor = None

        for _, candidate in (
            trajectory_candidates
        ):
            if candidate != target_sign:
                competitor = candidate
                break

        if competitor is not None:

            made = make_plot(
                signer_id,
                target_sign,
                target_trajectory,
                train_prototypes[
                    target_sign
                ][
                    "trajectory"
                ],
                competitor,
                train_prototypes[
                    competitor
                ][
                    "trajectory"
                ],
                policy,
            )

            if made:
                print(
                    "    plot: generated"
                )

    ranking_csv = (
        OUTPUT_DIR
        / "fine_class_rankings.csv"
    )

    write_csv(
        ranking_csv,
        ranking_rows,
        [
            "signer_id",
            "target_sign",
            "feature",
            "candidate_sign",
            "rank",
            "distance",
        ],
    )

    print()
    print(
        "=" * 110
    )
    print(
        "OUTPUT"
    )
    print(
        "=" * 110
    )

    print(
        quality_csv
    )

    print(
        distance_csv
    )

    print(
        ranking_csv
    )

    if PLOT_DIR.exists():

        print(
            PLOT_DIR
        )

    print()
    print(
        "READ ONLY: dataset and models "
        "were not modified."
    )


if __name__ == "__main__":
    main()
