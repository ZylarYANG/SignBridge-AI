import type {
  LandmarkFrame,
} from "../types/landmark";

import type {
  RawDatasetFrame,
} from "./api";


export type HandednessPolicy =
  | "dominant_either"
  | "both_hands";

export type DirectionReference =
  | "body_relative"
  | "self_relative"
  | "interlocutor_relative";

export type RequiredPart =
  | "upper_body"
  | "active_hand"
  | "both_hands";

export type ActiveHand =
  | "left"
  | "right"
  | "both"
  | "none";


export type CollectionSign = {
  classId: number;
  signId: string;
  label: string;

  handednessPolicy:
    HandednessPolicy;

  requiredParts:
    RequiredPart[];

  directionReference:
    DirectionReference;

  directionSensitive:
    boolean;
};


export type DatasetQualityResult = {
  inputUsable: boolean;

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


export const COLLECTION_TARGET_TAKES = 5;

export const COLLECTION_SIGNS:
  CollectionSign[] = [
    {
      classId: 0,
      signId: "CSL_thanks",
      label: "谢谢",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 1,
      signId: "CSL_bye",
      label: "再见",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 2,
      signId: "CSL_friend",
      label: "朋友",
      handednessPolicy:
        "both_hands",
      requiredParts: [
        "upper_body",
        "both_hands",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 3,
      signId: "CSL_hello",
      label: "你好",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "interlocutor_relative",
      directionSensitive:
        true,
    },
    {
      classId: 4,
      signId: "CSL_help",
      label: "帮助",
      handednessPolicy:
        "both_hands",
      requiredParts: [
        "upper_body",
        "both_hands",
      ],
      directionReference:
        "interlocutor_relative",
      directionSensitive:
        true,
    },
    {
      classId: 5,
      signId: "CSL_like",
      label: "喜欢",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 6,
      signId: "CSL_me",
      label: "我",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "self_relative",
      directionSensitive:
        true,
    },
    {
      classId: 7,
      signId: "CSL_name",
      label: "名字",
      handednessPolicy:
        "both_hands",
      requiredParts: [
        "upper_body",
        "both_hands",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 8,
      signId: "CSL_never_mind",
      label: "没关系",
      handednessPolicy:
        "both_hands",
      requiredParts: [
        "upper_body",
        "both_hands",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 9,
      signId: "CSL_no",
      label: "不",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 10,
      signId: "CSL_please",
      label: "请",
      handednessPolicy:
        "both_hands",
      requiredParts: [
        "upper_body",
        "both_hands",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 11,
      signId: "CSL_sorry",
      label: "对不起",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "self_relative",
      directionSensitive:
        false,
    },
    {
      classId: 12,
      signId: "CSL_what",
      label: "什么",
      handednessPolicy:
        "both_hands",
      requiredParts: [
        "upper_body",
        "both_hands",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 13,
      signId: "CSL_yes",
      label: "是",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "body_relative",
      directionSensitive:
        false,
    },
    {
      classId: 14,
      signId: "CSL_you",
      label: "你",
      handednessPolicy:
        "dominant_either",
      requiredParts: [
        "upper_body",
        "active_hand",
      ],
      directionReference:
        "interlocutor_relative",
      directionSensitive:
        true,
    },
  ];


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
    !Number.isInteger(takeId) ||
    takeId < 1
  ) {
    throw new Error(
      "takeId must be a positive integer."
    );
  }

  return [
    normalizedSigner,
    signId,
    String(takeId).padStart(
      4,
      "0"
    ),
  ].join("_");
}


export function toDatasetRawFrames(
  frames: LandmarkFrame[]
): RawDatasetFrame[] {
  if (frames.length === 0) {
    return [];
  }

  const startTime =
    frames[0].timestampMs;

  return frames.map(
    (frame) => ({
      timestamp_ms:
        frame.timestampMs -
        startTime,

      landmarks:
        frame.landmarks.map(
          (point) => ({
            x: point.x,
            y: point.y,
            valid: point.valid,
          })
        ),
    })
  );
}


export function getCaptureDurationMs(
  frames: LandmarkFrame[]
): number {
  if (frames.length < 2) {
    return 1;
  }

  return Math.max(
    1,

    frames[
      frames.length - 1
    ].timestampMs -
      frames[0].timestampMs
  );
}


/**
 * 一只手 21 个点。
 *
 * 至少 75% 的关键点有效，
 * 认为这一帧该手可用。
 */
function isHandUsable(
  frame: LandmarkFrame,
  startIndex: number
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
    validCount / 21 >=
    0.75
  );
}


/**
 * 当前实时画面是否满足
 * 该词最基本的输入要求。
 *
 * Canonical 54/54 不参与判断。
 */
export function getLiveInputReadiness(
  sign: CollectionSign,
  poseDetected: boolean,
  handsDetected: number
): {
  ready: boolean;
  message: string;
} {
  if (!poseDetected) {
    return {
      ready: false,
      message:
        "请保持上半身进入画面",
    };
  }

  if (
    sign.handednessPolicy ===
    "both_hands"
  ) {
    if (handsDetected < 2) {
      return {
        ready: false,
        message:
          "该词需要双手完整进入画面",
      };
    }

    return {
      ready: true,
      message:
        "Required Input Ready",
    };
  }

  if (handsDetected < 1) {
    return {
      ready: false,
      message:
        "请至少保持一只有效手进入画面",
    };
  }

  return {
    ready: true,
    message:
      "Required Input Ready",
  };
}


/**
 * 对一次完整采集做真正的数据质量判断。
 *
 * 单手词：
 * 左右任一只手持续稳定即可。
 *
 * 双手词：
 * 必须双手同时稳定。
 *
 * Canonical 54/54 只保留为
 * 调试/检测指标，不作为保存门槛。
 */
export function calculateDatasetQuality(
  frames: LandmarkFrame[],
  sign: CollectionSign
): DatasetQualityResult {
  if (frames.length === 0) {
    return {
      inputUsable: false,

      landmarkValidRatio: 0,
      shoulderUsableRatio: 0,

      leftHandUsableRatio: 0,
      rightHandUsableRatio: 0,
      bothHandsUsableRatio: 0,

      activeHand: "none",
    };
  }

  let validPointCount = 0;

  let shoulderUsableFrames = 0;

  let leftHandUsableFrames = 0;

  let rightHandUsableFrames = 0;

  let bothHandsUsableFrames = 0;


  for (const frame of frames) {
    validPointCount +=
      frame.landmarks.filter(
        (point) =>
          point.valid
      ).length;


    const leftShoulder =
      frame.landmarks[45];

    const rightShoulder =
      frame.landmarks[46];


    if (
      leftShoulder?.valid &&
      rightShoulder?.valid
    ) {
      shoulderUsableFrames += 1;
    }


    const leftReady =
      isHandUsable(
        frame,
        0
      );

    const rightReady =
      isHandUsable(
        frame,
        21
      );


    if (leftReady) {
      leftHandUsableFrames += 1;
    }

    if (rightReady) {
      rightHandUsableFrames += 1;
    }

    if (
      leftReady &&
      rightReady
    ) {
      bothHandsUsableFrames += 1;
    }
  }


  const frameCount =
    frames.length;


  const landmarkValidRatio =
    validPointCount /
    (frameCount * 54);


  const shoulderUsableRatio =
    shoulderUsableFrames /
    frameCount;


  const leftHandUsableRatio =
    leftHandUsableFrames /
    frameCount;


  const rightHandUsableRatio =
    rightHandUsableFrames /
    frameCount;


  const bothHandsUsableRatio =
    bothHandsUsableFrames /
    frameCount;


  let activeHand:
    ActiveHand = "none";

  let handRequirementReady =
    false;


  if (
    sign.handednessPolicy ===
    "both_hands"
  ) {
    if (
      bothHandsUsableRatio >=
      0.6
    ) {
      activeHand = "both";

      handRequirementReady =
        true;
    }
  } else {
    const bestRatio =
      Math.max(
        leftHandUsableRatio,
        rightHandUsableRatio
      );


    if (
      bestRatio >=
      0.5
    ) {
      activeHand =
        leftHandUsableRatio >=
        rightHandUsableRatio
          ? "left"
          : "right";

      handRequirementReady =
        true;
    }
  }


  const inputUsable =
    frameCount >= 10 &&
    shoulderUsableRatio >=
      0.8 &&
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
