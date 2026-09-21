import type { VisionFrameResult } from "./mediapipe";
import type {
  LandmarkFrame,
  LandmarkPoint,
} from "../types/landmark";

/**
 * SignBridge canonical landmark order
 *
 * 0-20   : left hand
 * 21-41  : right hand
 * 42     : nose
 * 43     : mouth_left
 * 44     : mouth_right
 * 45     : left_shoulder
 * 46     : right_shoulder
 * 47     : left_elbow
 * 48     : right_elbow
 * 49     : left_wrist
 * 50     : right_wrist
 * 51     : left_hip
 * 52     : right_hip
 * 53     : shoulder_center
 */
export const CANONICAL_LANDMARK_COUNT = 54;

export const BODY_POSE_INDICES = [
  0,   // nose
  9,   // mouth_left
  10,  // mouth_right
  11,  // left_shoulder
  12,  // right_shoulder
  13,  // left_elbow
  14,  // right_elbow
  15,  // left_wrist
  16,  // right_wrist
  23,  // left_hip
  24,  // right_hip
] as const;

export type CanonicalFrameResult = {
  frame: LandmarkFrame;
  validCount: number;
  validRatio: number;
  leftHandDetected: boolean;
  rightHandDetected: boolean;
  poseDetected: boolean;
};

function invalidPoint(): LandmarkPoint {
  return {
    x: 0,
    y: 0,
    valid: false,
  };
}

function toPoint(
  point:
    | {
        x: number;
        y: number;
      }
    | undefined
): LandmarkPoint {
  if (
    !point ||
    !Number.isFinite(point.x) ||
    !Number.isFinite(point.y)
  ) {
    return invalidPoint();
  }

  return {
    x: point.x,
    y: point.y,
    valid: true,
  };
}

function emptyHand(): LandmarkPoint[] {
  return Array.from(
    { length: 21 },
    () => invalidPoint()
  );
}

function findHand(
  result: VisionFrameResult,
  target: "Left" | "Right"
): LandmarkPoint[] {
  const targetIndex =
    result.handedness.findIndex(
      (label) =>
        label.toLowerCase() ===
        target.toLowerCase()
    );

  if (targetIndex < 0) {
    return emptyHand();
  }

  const hand =
    result.handLandmarks[targetIndex];

  if (!hand || hand.length !== 21) {
    return emptyHand();
  }

  return hand.map(toPoint);
}

function calculateShoulderCenter(
  leftShoulder: LandmarkPoint,
  rightShoulder: LandmarkPoint
): LandmarkPoint {
  if (
    !leftShoulder.valid ||
    !rightShoulder.valid
  ) {
    return invalidPoint();
  }

  return {
    x:
      (leftShoulder.x +
        rightShoulder.x) /
      2,
    y:
      (leftShoulder.y +
        rightShoulder.y) /
      2,
    valid: true,
  };
}

export function canonicalizeFrame(
  result: VisionFrameResult,
  timestampMs: number
): CanonicalFrameResult {
  const leftHand =
    findHand(result, "Left");

  const rightHand =
    findHand(result, "Right");

  const body = BODY_POSE_INDICES.map(
    (index) =>
      toPoint(
        result.poseLandmarks[index]
      )
  );

  // body[3] = pose 11 left shoulder
  // body[4] = pose 12 right shoulder
  const shoulderCenter =
    calculateShoulderCenter(
      body[3],
      body[4]
    );

  const landmarks = [
    ...leftHand,
    ...rightHand,
    ...body,
    shoulderCenter,
  ];

  if (
    landmarks.length !==
    CANONICAL_LANDMARK_COUNT
  ) {
    throw new Error(
      `Canonical landmark count mismatch: ${landmarks.length}`
    );
  }

  const validCount =
    landmarks.filter(
      (point) => point.valid
    ).length;

  const validRatio =
    validCount /
    CANONICAL_LANDMARK_COUNT;

  return {
    frame: {
      timestampMs,
      landmarks,
    },

    validCount,

    validRatio,

    leftHandDetected:
      leftHand.some(
        (point) => point.valid
      ),

    rightHandDetected:
      rightHand.some(
        (point) => point.valid
      ),

    poseDetected:
      body.some(
        (point) => point.valid
      ),
  };
}
