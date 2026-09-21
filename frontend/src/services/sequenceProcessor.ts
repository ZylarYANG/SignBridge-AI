import type {
  LandmarkFrame,
  LandmarkPoint,
} from "../types/landmark";

export const MODEL_SEQUENCE_LENGTH = 64;

export type ProcessedSequence = {
  rawFrameCount: number;

  normalizedFrames: LandmarkFrame[];

  resampledFrames: LandmarkFrame[];

  /**
   * 最终模型输入：
   * [64, 54, 2]
   */
  modelInput: number[][][];
};


/**
 * 创建一个无效点。
 *
 * 注意：
 * x = 0 / y = 0 只是占位。
 * valid = false 才表示该点没有被检测到。
 */
function invalidPoint(): LandmarkPoint {
  return {
    x: 0,
    y: 0,
    valid: false,
  };
}


/**
 * 克隆一个 LandmarkPoint，
 * 防止不同 frame 共用同一个对象。
 */
function clonePoint(
  point: LandmarkPoint
): LandmarkPoint {
  return {
    x: point.x,
    y: point.y,
    valid: point.valid,
  };
}


/**
 * 对单帧做空间归一化：
 *
 * 1. 肩中心移动到 (0, 0)
 * 2. 以肩宽作为尺度 1
 *
 * Canonical index:
 *
 * 45 = left shoulder
 * 46 = right shoulder
 * 53 = shoulder center
 */
function normalizeFrame(
  frame: LandmarkFrame
): LandmarkFrame {
  const leftShoulder =
    frame.landmarks[45];

  const rightShoulder =
    frame.landmarks[46];

  if (
    !leftShoulder ||
    !rightShoulder ||
    !leftShoulder.valid ||
    !rightShoulder.valid
  ) {
    return {
      timestampMs: frame.timestampMs,

      landmarks:
        frame.landmarks.map(
          () => invalidPoint()
        ),
    };
  }

  const centerX =
    (
      leftShoulder.x +
      rightShoulder.x
    ) / 2;

  const centerY =
    (
      leftShoulder.y +
      rightShoulder.y
    ) / 2;

  const dx =
    rightShoulder.x -
    leftShoulder.x;

  const dy =
    rightShoulder.y -
    leftShoulder.y;

  const shoulderWidth =
    Math.sqrt(
      dx * dx +
      dy * dy
    );

  if (
    !Number.isFinite(shoulderWidth) ||
    shoulderWidth < 1e-6
  ) {
    return {
      timestampMs: frame.timestampMs,

      landmarks:
        frame.landmarks.map(
          () => invalidPoint()
        ),
    };
  }

  const landmarks =
    frame.landmarks.map(
      (
        point
      ): LandmarkPoint => {
        if (!point.valid) {
          return invalidPoint();
        }

        return {
          x:
            (point.x - centerX) /
            shoulderWidth,

          y:
            (point.y - centerY) /
            shoulderWidth,

          valid: true,
        };
      }
    );

  return {
    timestampMs: frame.timestampMs,
    landmarks,
  };
}


/**
 * 对完整序列做空间归一化。
 */
export function normalizeSequence(
  frames: LandmarkFrame[]
): LandmarkFrame[] {
  return frames.map(
    normalizeFrame
  );
}


/**
 * 在两个 LandmarkPoint 之间进行线性插值。
 *
 * 只有两个端点都有效时才进行插值。
 *
 * 如果某一端无效，
 * 暂时保持 invalid，
 * 避免人为“创造”不存在的手部位置。
 */
function interpolatePoint(
  a: LandmarkPoint,
  b: LandmarkPoint,
  alpha: number
): LandmarkPoint {
  if (
    !a.valid ||
    !b.valid
  ) {
    return invalidPoint();
  }

  return {
    x:
      a.x +
      (
        b.x -
        a.x
      ) * alpha,

    y:
      a.y +
      (
        b.y -
        a.y
      ) * alpha,

    valid: true,
  };
}


/**
 * 按真实 timestamp 重采样。
 *
 * 例如：
 *
 * 30 frames
 * ↓
 * 64 frames
 *
 * 不是简单复制帧，
 * 而是在真实时间轴上插值。
 */
export function resampleSequence(
  frames: LandmarkFrame[],
  targetLength =
    MODEL_SEQUENCE_LENGTH
): LandmarkFrame[] {
  if (frames.length < 2) {
    throw new Error(
      "At least 2 frames are required for resampling."
    );
  }

  if (targetLength < 2) {
    throw new Error(
      "targetLength must be at least 2."
    );
  }

  const startTime =
    frames[0].timestampMs;

  const endTime =
    frames[
      frames.length - 1
    ].timestampMs;

  const duration =
    endTime - startTime;

  if (
    !Number.isFinite(duration) ||
    duration <= 0
  ) {
    throw new Error(
      "Invalid capture timestamps."
    );
  }

  const result:
    LandmarkFrame[] = [];

  let sourceIndex = 0;

  for (
    let targetIndex = 0;
    targetIndex < targetLength;
    targetIndex += 1
  ) {
    const ratio =
      targetIndex /
      (targetLength - 1);

    const targetTime =
      startTime +
      ratio * duration;

    while (
      sourceIndex <
        frames.length - 2 &&
      frames[
        sourceIndex + 1
      ].timestampMs <
        targetTime
    ) {
      sourceIndex += 1;
    }

    const before =
      frames[sourceIndex];

    const after =
      frames[
        Math.min(
          sourceIndex + 1,
          frames.length - 1
        )
      ];

    const interval =
      after.timestampMs -
      before.timestampMs;

    const alpha =
      interval <= 0
        ? 0
        :
          (
            targetTime -
            before.timestampMs
          ) /
          interval;

    const landmarks =
      before.landmarks.map(
        (
          beforePoint,
          pointIndex
        ) =>
          interpolatePoint(
            beforePoint,
            after.landmarks[
              pointIndex
            ],
            alpha
          )
      );

    result.push({
      timestampMs:
        targetTime,

      landmarks,
    });
  }

  return result;
}


/**
 * LandmarkFrame[]
 *
 * ↓
 *
 * [T, 54, 2]
 *
 * 无效点使用 [0, 0]。
 */
function framesToModelInput(
  frames: LandmarkFrame[]
): number[][][] {
  return frames.map(
    (frame) =>
      frame.landmarks.map(
        (point) => {
          if (!point.valid) {
            return [0, 0];
          }

          return [
            point.x,
            point.y,
          ];
        }
      )
  );
}


/**
 * 整个模型预处理入口。
 */
export function prepareSequence(
  rawFrames: LandmarkFrame[]
): ProcessedSequence {
  if (rawFrames.length < 2) {
    throw new Error(
      "Not enough frames."
    );
  }

  const normalizedFrames =
    normalizeSequence(
      rawFrames
    );

  const resampledFrames =
    resampleSequence(
      normalizedFrames,
      MODEL_SEQUENCE_LENGTH
    );

  const modelInput =
    framesToModelInput(
      resampledFrames
    );

  return {
    rawFrameCount:
      rawFrames.length,

    normalizedFrames,

    resampledFrames,

    modelInput,
  };
}