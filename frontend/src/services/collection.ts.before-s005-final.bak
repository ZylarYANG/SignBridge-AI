import type {
  LandmarkFrame,
} from "../types/landmark";

import type {
  RawDatasetFrame,
} from "./api";

import type {
  CollectionSign,
  QualityPolicy,
} from "./catalog";


export type ActiveHand =
  | "left"
  | "right"
  | "both"
  | "none";


export type DatasetQualityResult = {
  inputUsable:
    boolean;

  landmarkValidRatio:
    number;

  shoulderUsableRatio:
    number;

  leftHandUsableRatio:
    number;

  rightHandUsableRatio:
    number;

  bothHandsUsableRatio:
    number;

  activeHand:
    ActiveHand;
};


export function buildSampleId(
  signerId: string,
  signId: string,
  takeId: number
): string {
  const normalizedSigner =
    signerId
      .trim()
      .toUpperCase();


  if (!normalizedSigner) {
    throw new Error(
      "signerId cannot be empty."
    );
  }


  if (
    !Number.isInteger(
      takeId
    )
    ||
    takeId < 1
  ) {
    throw new Error(
      "takeId must be "
      +
      "a positive integer."
    );
  }


  return [
    normalizedSigner,

    signId,

    String(
      takeId
    ).padStart(
      4,
      "0"
    ),
  ].join("_");
}


export function toDatasetRawFrames(
  frames:
    LandmarkFrame[]
): RawDatasetFrame[] {
  if (
    frames.length === 0
  ) {
    return [];
  }


  const startTime =
    frames[0]
      .timestampMs;


  return frames.map(
    (frame) => ({
      timestamp_ms:
        frame.timestampMs
        -
        startTime,

      landmarks:
        frame.landmarks.map(
          (point) => ({
            x:
              point.x,

            y:
              point.y,

            valid:
              point.valid,
          })
        ),
    })
  );
}


export function getCaptureDurationMs(
  frames:
    LandmarkFrame[]
): number {
  if (
    frames.length < 2
  ) {
    return 1;
  }


  return Math.max(
    1,

    frames[
      frames.length - 1
    ].timestampMs
    -
    frames[0]
      .timestampMs
  );
}


/**
 * 判断一帧中的指定手是否可用。
 *
 * 阈值由 sign_catalog.json
 * quality_policy 提供，
 * 不再在前端硬编码。
 */
function isHandUsable(
  frame:
    LandmarkFrame,

  startIndex:
    number,

  minimumLandmarkRatio:
    number
): boolean {
  const hand =
    frame.landmarks.slice(
      startIndex,
      startIndex + 21
    );


  const validCount =
    hand.filter(
      (point) =>
        point.valid
    ).length;


  return (
    validCount / 21
    >=
    minimumLandmarkRatio
  );
}


/**
 * 当前实时画面只负责给出提示。
 *
 * 不阻止用户点击采集。
 *
 * 真正的数据质量判定发生在
 * calculateDatasetQuality。
 */
export function getLiveInputReadiness(
  sign:
    CollectionSign,

  poseDetected:
    boolean,

  handsDetected:
    number
): {
  ready:
    boolean;

  message:
    string;
} {
  if (!poseDetected) {
    return {
      ready:
        false,

      message:
        "请保持上半身进入画面",
    };
  }


  if (
    sign.handednessPolicy ===
    "both_hands"
  ) {
    if (
      handsDetected < 2
    ) {
      return {
        ready:
          false,

        message:
          "该词需要双手完整进入画面",
      };
    }


    return {
      ready:
        true,

      message:
        "Required Input Ready",
    };
  }


  if (
    handsDetected < 1
  ) {
    return {
      ready:
        false,

      message:
        "请至少保持一只有效手进入画面",
    };
  }


  return {
    ready:
      true,

    message:
      "Required Input Ready",
  };
}


/**
 * 对一次完整采集进行质量判断。
 *
 * 所有阈值来自
 * config/sign_catalog.json。
 *
 * 前端不再维护第二套规则。
 */
export function calculateDatasetQuality(
  frames:
    LandmarkFrame[],

  sign:
    CollectionSign,

  qualityPolicy:
    QualityPolicy
): DatasetQualityResult {
  if (
    frames.length === 0
  ) {
    return {
      inputUsable:
        false,

      landmarkValidRatio:
        0,

      shoulderUsableRatio:
        0,

      leftHandUsableRatio:
        0,

      rightHandUsableRatio:
        0,

      bothHandsUsableRatio:
        0,

      activeHand:
        "none",
    };
  }


  let validPointCount =
    0;

  let shoulderUsableFrames =
    0;

  let leftHandUsableFrames =
    0;

  let rightHandUsableFrames =
    0;

  let bothHandsUsableFrames =
    0;


  for (
    const frame
    of frames
  ) {
    validPointCount +=
      frame.landmarks.filter(
        (point) =>
          point.valid
      ).length;


    const leftShoulder =
      frame.landmarks[
        45
      ];

    const rightShoulder =
      frame.landmarks[
        46
      ];


    if (
      leftShoulder?.valid
      &&
      rightShoulder?.valid
    ) {
      shoulderUsableFrames +=
        1;
    }


    const leftReady =
      isHandUsable(
        frame,

        0,

        qualityPolicy
          .minimumHandLandmarkRatioPerFrame
      );


    const rightReady =
      isHandUsable(
        frame,

        21,

        qualityPolicy
          .minimumHandLandmarkRatioPerFrame
      );


    if (
      leftReady
    ) {
      leftHandUsableFrames +=
        1;
    }


    if (
      rightReady
    ) {
      rightHandUsableFrames +=
        1;
    }


    if (
      leftReady
      &&
      rightReady
    ) {
      bothHandsUsableFrames +=
        1;
    }
  }


  const frameCount =
    frames.length;


  const landmarkValidRatio =
    validPointCount
    /
    (
      frameCount
      *
      54
    );


  const shoulderUsableRatio =
    shoulderUsableFrames
    /
    frameCount;


  const leftHandUsableRatio =
    leftHandUsableFrames
    /
    frameCount;


  const rightHandUsableRatio =
    rightHandUsableFrames
    /
    frameCount;


  const bothHandsUsableRatio =
    bothHandsUsableFrames
    /
    frameCount;


  let activeHand:
    ActiveHand =
      "none";


  let handRequirementReady =
    false;


  if (
    sign.handednessPolicy ===
    "both_hands"
  ) {
    if (
      bothHandsUsableRatio
      >=
      qualityPolicy
        .minimumBothHandsUsableRatio
    ) {
      activeHand =
        "both";

      handRequirementReady =
        true;
    }
  }
  else {
    const bestRatio =
      Math.max(
        leftHandUsableRatio,
        rightHandUsableRatio
      );


    if (
      bestRatio
      >=
      qualityPolicy
        .minimumSingleHandUsableRatio
    ) {
      activeHand =
        leftHandUsableRatio
        >=
        rightHandUsableRatio
          ?
            "left"
          :
            "right";


      handRequirementReady =
        true;
    }
  }


  const inputUsable =
    frameCount
      >=
      qualityPolicy
        .minimumRawFrames
    &&
    shoulderUsableRatio
      >=
      qualityPolicy
        .minimumShoulderUsableRatio
    &&
    handRequirementReady;


  return {
    inputUsable,

    landmarkValidRatio,

    shoulderUsableRatio,

    leftHandUsableRatio,

    rightHandUsableRatio,

    bothHandsUsableRatio,

    activeHand,
  };
}
