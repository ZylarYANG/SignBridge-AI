from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
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
    / "trajectory_diagnosis"
)

FOCUS_SIGNS = {
    "CSL_bye",
    "CSL_hello",
    "CSL_what",
}

INACTIVE_SIGNS = {
    "CSL_me",
    "CSL_please",
    "CSL_you",
}

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

TARGET_CASES = [
    ("S004", "CSL_bye"),
    ("S005", "CSL_bye"),
    ("S004", "CSL_hello"),
    ("S005", "CSL_hello"),
    ("S004", "CSL_what"),
    ("S005", "CSL_what"),
]

HAND_READY_RATIO = 0.75
SIGNATURE_STEPS = 32


def mean_or_nan(values):
    clean = [
        float(v)
        for v in values
        if v is not None
        and math.isfinite(float(v))
    ]

    if not clean:
        return float("nan")

    return float(
        np.mean(clean)
    )


def fmt(value, digits=3):
    if value is None:
        return "nan"

    value = float(value)

    if not math.isfinite(value):
        return "nan"

    return f"{value:.{digits}f}"


def load_catalog():
    data = json.loads(
        CATALOG_PATH.read_text(
            encoding="utf-8"
        )
    )

    signs = data.get(
        "signs",
        []
    )

    return {
        sign["sign_id"]: sign
        for sign in signs
    }


def load_manifest():
    records = []

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:

        for line in handle:
            line = line.strip()

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


def sample_path(record):
    raw = record.get(
        "sample_path"
    )

    if raw:
        path = Path(raw)

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
            record["sample_id"]
            + ".json"
        )
    )

    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        record["sample_id"]
    )


def point_valid(point):
    return bool(
        point
        and point.get(
            "valid",
            False,
        )
    )


def hand_usable(
    landmarks,
    start,
):
    hand = landmarks[
        start:start + 21
    ]

    if len(hand) != 21:
        return False

    valid = sum(
        1
        for point in hand
        if point_valid(point)
    )

    return (
        valid / 21.0
        >= HAND_READY_RATIO
    )


def shoulder_transform(
    landmarks,
):
    if len(landmarks) < 54:
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

    center_x = (
        lx + rx
    ) / 2.0

    center_y = (
        ly + ry
    ) / 2.0

    return (
        center_x,
        center_y,
        width,
    )


def hand_centroid(
    landmarks,
    start,
    transform,
):
    if transform is None:
        return None

    if not hand_usable(
        landmarks,
        start,
    ):
        return None

    cx, cy, scale = (
        transform
    )

    coords = []

    for point in landmarks[
        start:start + 21
    ]:

        if not point_valid(
            point
        ):
            continue

        x = (
            float(point["x"])
            - cx
        ) / scale

        y = (
            float(point["y"])
            - cy
        ) / scale

        coords.append(
            (x, y)
        )

    if not coords:
        return None

    arr = np.asarray(
        coords,
        dtype=np.float64,
    )

    return arr.mean(
        axis=0
    )


def max_missing_run(
    ready,
):
    best = 0
    current = 0

    for item in ready:
        if item:
            current = 0
        else:
            current += 1
            best = max(
                best,
                current,
            )

    return best


def max_internal_gap(
    ready,
):
    true_indices = [
        i
        for i, item
        in enumerate(ready)
        if item
    ]

    if len(true_indices) < 2:
        return 0

    start = true_indices[0]
    end = true_indices[-1]

    best = 0
    current = 0

    for item in ready[
        start:end + 1
    ]:
        if item:
            current = 0
        else:
            current += 1
            best = max(
                best,
                current,
            )

    return best


def build_signature(
    track,
):
    valid_indices = [
        i
        for i, value
        in enumerate(track)
        if value is not None
    ]

    if len(
        valid_indices
    ) < 3:
        return None

    total_frames = len(
        track
    )

    if total_frames < 2:
        return None

    progress = (
        np.asarray(
            valid_indices,
            dtype=np.float64,
        )
        / (
            total_frames - 1
        )
    )

    values = np.asarray(
        [
            track[i]
            for i in valid_indices
        ],
        dtype=np.float64,
    )

    grid = np.linspace(
        0.0,
        1.0,
        SIGNATURE_STEPS,
    )

    channels = []

    for dim in range(
        values.shape[1]
    ):
        channels.append(
            np.interp(
                grid,
                progress,
                values[:, dim],
            )
        )

    return np.stack(
        channels,
        axis=1,
    ).reshape(-1)


def analyse_sample(
    record,
    sign_info,
):
    path = sample_path(
        record
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    frames = data.get(
        "raw_frames",
        []
    )

    if not frames:
        raise RuntimeError(
            "No raw_frames: "
            + record["sample_id"]
        )

    policy = sign_info[
        "handedness_policy"
    ]

    frame_count = len(
        frames
    )

    valid_points = 0
    shoulder_ready = 0
    left_ready = 0
    right_ready = 0
    both_ready = 0

    frame_cache = []

    for frame in frames:
        landmarks = frame.get(
            "landmarks",
            []
        )

        valid_points += sum(
            1
            for point in landmarks
            if point_valid(point)
        )

        transform = (
            shoulder_transform(
                landmarks
            )
        )

        if transform is not None:
            shoulder_ready += 1

        left_ok = hand_usable(
            landmarks,
            0,
        )

        right_ok = hand_usable(
            landmarks,
            21,
        )

        if left_ok:
            left_ready += 1

        if right_ok:
            right_ready += 1

        if (
            left_ok
            and right_ok
        ):
            both_ready += 1

        left_centroid = (
            hand_centroid(
                landmarks,
                0,
                transform,
            )
        )

        right_centroid = (
            hand_centroid(
                landmarks,
                21,
                transform,
            )
        )

        frame_cache.append({
            "timestamp_ms":
                float(
                    frame.get(
                        "timestamp_ms",
                        0.0,
                    )
                ),

            "left":
                left_centroid,

            "right":
                right_centroid,
        })

    left_ratio = (
        left_ready
        / frame_count
    )

    right_ratio = (
        right_ready
        / frame_count
    )

    both_ratio = (
        both_ready
        / frame_count
    )

    if policy == "both_hands":
        selected_hand = "both"
    else:
        selected_hand = (
            "left"
            if left_ratio
            >= right_ratio
            else "right"
        )

    track = []

    for cached in frame_cache:
        left = cached["left"]
        right = cached["right"]

        if selected_hand == "left":
            if left is None:
                track.append(
                    None
                )
            else:
                track.append(
                    np.asarray(
                        left,
                        dtype=np.float64,
                    )
                )

        elif selected_hand == "right":
            if right is None:
                track.append(
                    None
                )
            else:
                track.append(
                    np.asarray(
                        right,
                        dtype=np.float64,
                    )
                )

        else:
            if (
                left is None
                or right is None
            ):
                track.append(
                    None
                )
            else:
                center = (
                    left + right
                ) / 2.0

                separation = float(
                    np.linalg.norm(
                        left - right
                    )
                )

                track.append(
                    np.asarray(
                        [
                            center[0],
                            center[1],
                            separation,
                        ],
                        dtype=np.float64,
                    )
                )

    ready = [
        item is not None
        for item in track
    ]

    valid_track = [
        item
        for item in track
        if item is not None
    ]

    if valid_track:
        positions = np.asarray(
            [
                item[:2]
                for item
                in valid_track
            ],
            dtype=np.float64,
        )

        amplitude_x = float(
            np.ptp(
                positions[:, 0]
            )
        )

        amplitude_y = float(
            np.ptp(
                positions[:, 1]
            )
        )

        start_x = float(
            positions[0, 0]
        )
        start_y = float(
            positions[0, 1]
        )

        end_x = float(
            positions[-1, 0]
        )
        end_y = float(
            positions[-1, 1]
        )

    else:
        amplitude_x = float(
            "nan"
        )
        amplitude_y = float(
            "nan"
        )

        start_x = float(
            "nan"
        )
        start_y = float(
            "nan"
        )

        end_x = float(
            "nan"
        )
        end_y = float(
            "nan"
        )

    path_length = 0.0
    speeds = []
    jumps = []

    for i in range(
        1,
        frame_count,
    ):
        previous = track[
            i - 1
        ]

        current = track[
            i
        ]

        if (
            previous is None
            or current is None
        ):
            continue

        delta = float(
            np.linalg.norm(
                current[:2]
                - previous[:2]
            )
        )

        dt_ms = (
            frame_cache[i][
                "timestamp_ms"
            ]
            - frame_cache[
                i - 1
            ][
                "timestamp_ms"
            ]
        )

        path_length += (
            delta
        )

        jumps.append(
            delta
        )

        if dt_ms > 0:
            speeds.append(
                delta
                / (
                    dt_ms
                    / 1000.0
                )
            )

    separations = [
        float(item[2])
        for item in valid_track
        if len(item) >= 3
    ]

    signature = (
        build_signature(
            track
        )
    )

    result = {
        "sample_id":
            record["sample_id"],

        "signer_id":
            record["signer_id"],

        "sign_id":
            record["sign_id"],

        "policy":
            policy,

        "frame_count":
            frame_count,

        "valid_ratio":
            valid_points
            / (
                frame_count
                * 54
            ),

        "shoulder_ratio":
            shoulder_ready
            / frame_count,

        "left_ratio":
            left_ratio,

        "right_ratio":
            right_ratio,

        "both_ratio":
            both_ratio,

        "selected_hand":
            selected_hand,

        "track_ratio":
            sum(ready)
            / frame_count,

        "max_missing_run":
            max_missing_run(
                ready
            ),

        "max_internal_gap":
            max_internal_gap(
                ready
            ),

        "path_length":
            path_length,

        "avg_speed":
            mean_or_nan(
                speeds
            ),

        "max_jump":
            max(
                jumps
            )
            if jumps
            else float("nan"),

        "amplitude_x":
            amplitude_x,

        "amplitude_y":
            amplitude_y,

        "start_x":
            start_x,

        "start_y":
            start_y,

        "end_x":
            end_x,

        "end_y":
            end_y,

        "mean_separation":
            mean_or_nan(
                separations
            ),

        "separation_range":
            (
                max(separations)
                - min(separations)
            )
            if separations
            else float("nan"),

        "_signature":
            signature,
    }

    return result


def signature_mean(
    rows,
):
    signatures = [
        row["_signature"]
        for row in rows
        if row[
            "_signature"
        ] is not None
    ]

    if not signatures:
        return None

    return np.mean(
        np.stack(
            signatures,
            axis=0,
        ),
        axis=0,
    )


def signature_distance(
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

    if first.shape != second.shape:
        return float(
            "nan"
        )

    return float(
        np.sqrt(
            np.mean(
                (
                    first
                    - second
                )
                ** 2
            )
        )
    )


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
                for field in fields
            })


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    catalog = load_catalog()

    records = load_manifest()

    active_signs = {
        sign_id
        for sign_id
        in catalog
        if sign_id
        not in INACTIVE_SIGNS
    }

    records = [
        row
        for row in records
        if row.get(
            "sign_id"
        ) in active_signs
        and row.get(
            "signer_id"
        ) in ALL_SIGNERS
    ]

    analysed = []

    print()
    print(
        "Loading samples..."
    )

    for index, record in enumerate(
        records,
        start=1,
    ):
        sign_id = record[
            "sign_id"
        ]

        analysed.append(
            analyse_sample(
                record,
                catalog[
                    sign_id
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

    focus_rows = [
        row
        for row in analysed
        if row[
            "sign_id"
        ] in FOCUS_SIGNS
    ]

    sample_fields = [
        "sample_id",
        "signer_id",
        "sign_id",
        "policy",
        "frame_count",
        "valid_ratio",
        "shoulder_ratio",
        "left_ratio",
        "right_ratio",
        "both_ratio",
        "selected_hand",
        "track_ratio",
        "max_missing_run",
        "max_internal_gap",
        "path_length",
        "avg_speed",
        "max_jump",
        "amplitude_x",
        "amplitude_y",
        "start_x",
        "start_y",
        "end_x",
        "end_y",
        "mean_separation",
        "separation_range",
    ]

    sample_csv = (
        OUTPUT_DIR
        / "abnormal_sign_sample_metrics.csv"
    )

    write_csv(
        sample_csv,
        focus_rows,
        sample_fields,
    )

    grouped = defaultdict(
        list
    )

    for row in focus_rows:
        grouped[
            (
                row[
                    "sign_id"
                ],
                row[
                    "signer_id"
                ],
            )
        ].append(
            row
        )

    summary_rows = []

    mean_fields = [
        "valid_ratio",
        "shoulder_ratio",
        "left_ratio",
        "right_ratio",
        "both_ratio",
        "track_ratio",
        "max_missing_run",
        "max_internal_gap",
        "path_length",
        "avg_speed",
        "max_jump",
        "amplitude_x",
        "amplitude_y",
        "mean_separation",
        "separation_range",
    ]

    for sign_id in sorted(
        FOCUS_SIGNS
    ):
        for signer_id in (
            ALL_SIGNERS
        ):
            rows = grouped.get(
                (
                    sign_id,
                    signer_id,
                ),
                [],
            )

            if not rows:
                continue

            summary = {
                "sign_id":
                    sign_id,

                "signer_id":
                    signer_id,

                "samples":
                    len(rows),
            }

            for field in mean_fields:
                summary[field] = (
                    mean_or_nan(
                        [
                            row[field]
                            for row
                            in rows
                        ]
                    )
                )

            summary_rows.append(
                summary
            )

    summary_fields = [
        "sign_id",
        "signer_id",
        "samples",
        *mean_fields,
    ]

    summary_csv = (
        OUTPUT_DIR
        / "abnormal_sign_signer_summary.csv"
    )

    write_csv(
        summary_csv,
        summary_rows,
        summary_fields,
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

    print()
    print(
        "=" * 118
    )
    print(
        "FOCUS SIGN QUALITY / MOTION SUMMARY"
    )
    print(
        "=" * 118
    )

    header = (
        "sign             signer   n "
        "valid  shldr  left  right both  "
        "track gap  igap speed  jump   "
        "ampX   ampY   sep"
    )

    print(
        header
    )

    for row in summary_rows:
        print(
            f"{row['sign_id']:<16} "
            f"{row['signer_id']:<7} "
            f"{row['samples']:>2} "
            f"{fmt(row['valid_ratio']):>5} "
            f"{fmt(row['shoulder_ratio']):>5} "
            f"{fmt(row['left_ratio']):>5} "
            f"{fmt(row['right_ratio']):>5} "
            f"{fmt(row['both_ratio']):>5} "
            f"{fmt(row['track_ratio']):>5} "
            f"{fmt(row['max_missing_run'],1):>4} "
            f"{fmt(row['max_internal_gap'],1):>5} "
            f"{fmt(row['avg_speed']):>6} "
            f"{fmt(row['max_jump']):>6} "
            f"{fmt(row['amplitude_x']):>6} "
            f"{fmt(row['amplitude_y']):>6} "
            f"{fmt(row['mean_separation']):>6}"
        )

    print()
    print(
        "=" * 118
    )
    print(
        "DISTANCE TO TRAIN-SIGNER REFERENCE"
    )
    print(
        "Lower = trajectory is closer to "
        "the corresponding training-sign pattern."
    )
    print(
        "=" * 118
    )

    distance_rows = []

    for sign_id in sorted(
        FOCUS_SIGNS
    ):

        print()
        print(
            sign_id
        )

        for signer_id in ALL_SIGNERS:

            own_rows = (
                by_signer_sign.get(
                    (
                        signer_id,
                        sign_id,
                    ),
                    [],
                )
            )

            own_signature = (
                signature_mean(
                    own_rows
                )
            )

            if signer_id in TRAIN_SIGNERS:
                reference_rows = []

                for other in TRAIN_SIGNERS:
                    if other == signer_id:
                        continue

                    reference_rows.extend(
                        by_signer_sign.get(
                            (
                                other,
                                sign_id,
                            ),
                            [],
                        )
                    )
            else:
                reference_rows = []

                for other in TRAIN_SIGNERS:
                    reference_rows.extend(
                        by_signer_sign.get(
                            (
                                other,
                                sign_id,
                            ),
                            [],
                        )
                    )

            reference_signature = (
                signature_mean(
                    reference_rows
                )
            )

            distance = (
                signature_distance(
                    own_signature,
                    reference_signature,
                )
            )

            distance_rows.append({
                "sign_id":
                    sign_id,

                "signer_id":
                    signer_id,

                "samples":
                    len(
                        own_rows
                    ),

                "distance_to_train_reference":
                    distance,
            })

            print(
                f"  {signer_id}: "
                f"n={len(own_rows):>2} "
                f"distance="
                f"{fmt(distance,4)}"
            )

    distance_csv = (
        OUTPUT_DIR
        / "distance_to_train_reference.csv"
    )

    write_csv(
        distance_csv,
        distance_rows,
        [
            "sign_id",
            "signer_id",
            "samples",
            "distance_to_train_reference",
        ],
    )

    train_prototypes = {}

    for sign_id in sorted(
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

        prototype = (
            signature_mean(
                rows
            )
        )

        if prototype is not None:
            train_prototypes[
                sign_id
            ] = prototype

    print()
    print(
        "=" * 118
    )
    print(
        "NEAREST TRAINING-CLASS TRAJECTORIES"
    )
    print(
        "Only classes with the same handedness "
        "policy are compared."
    )
    print(
        "=" * 118
    )

    nearest_rows = []

    for signer_id, target_sign in (
        TARGET_CASES
    ):

        target_rows = (
            by_signer_sign.get(
                (
                    signer_id,
                    target_sign,
                ),
                [],
            )
        )

        target_signature = (
            signature_mean(
                target_rows
            )
        )

        target_policy = (
            catalog[
                target_sign
            ][
                "handedness_policy"
            ]
        )

        candidates = []

        for candidate_sign, prototype in (
            train_prototypes.items()
        ):

            if (
                catalog[
                    candidate_sign
                ][
                    "handedness_policy"
                ]
                != target_policy
            ):
                continue

            distance = (
                signature_distance(
                    target_signature,
                    prototype,
                )
            )

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

        print()
        print(
            f"{signer_id} / "
            f"{target_sign} "
            f"(n={len(target_rows)})"
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
                    "  <-- target"
                    if candidate_sign
                    == target_sign
                    else ""
                )

                print(
                    f"  #{rank:<2} "
                    f"{candidate_sign:<18} "
                    f"distance="
                    f"{fmt(distance,4)}"
                    f"{marker}"
                )

            nearest_rows.append({
                "signer_id":
                    signer_id,

                "target_sign":
                    target_sign,

                "candidate_sign":
                    candidate_sign,

                "rank":
                    rank,

                "distance":
                    distance,
            })

        print(
            "  target rank: "
            + (
                str(
                    target_rank
                )
                if target_rank
                is not None
                else "NA"
            )
        )

    nearest_csv = (
        OUTPUT_DIR
        / "nearest_training_classes.csv"
    )

    write_csv(
        nearest_csv,
        nearest_rows,
        [
            "signer_id",
            "target_sign",
            "candidate_sign",
            "rank",
            "distance",
        ],
    )

    print()
    print(
        "=" * 118
    )
    print(
        "OUTPUT FILES"
    )
    print(
        "=" * 118
    )

    print(
        sample_csv
    )

    print(
        summary_csv
    )

    print(
        distance_csv
    )

    print(
        nearest_csv
    )

    print()
    print(
        "READ ONLY: no dataset files "
        "were modified."
    )


if __name__ == "__main__":
    main()
