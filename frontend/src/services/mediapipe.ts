import {
  FilesetResolver,
  HandLandmarker,
  PoseLandmarker,
} from "@mediapipe/tasks-vision";

export type VisionFrameResult = {
  poseLandmarks: Array<{ x: number; y: number; z?: number }>;
  handLandmarks: Array<Array<{ x: number; y: number; z?: number }>>;
  handedness: string[];
};

let poseLandmarker: PoseLandmarker | null = null;
let handLandmarker: HandLandmarker | null = null;

let initializationPromise: Promise<void> | null = null;

const WASM_URL =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm";

const POSE_MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task";

const HAND_MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task";

export async function initializeMediaPipe(): Promise<void> {
  if (poseLandmarker && handLandmarker) {
    return;
  }

  if (initializationPromise) {
    return initializationPromise;
  }

  initializationPromise = (async () => {
    const vision = await FilesetResolver.forVisionTasks(WASM_URL);

    poseLandmarker = await PoseLandmarker.createFromOptions(
      vision,
      {
        baseOptions: {
          modelAssetPath: POSE_MODEL_URL,
        },
        runningMode: "VIDEO",
        numPoses: 1,
        minPoseDetectionConfidence: 0.5,
        minPosePresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
      }
    );

    handLandmarker = await HandLandmarker.createFromOptions(
      vision,
      {
        baseOptions: {
          modelAssetPath: HAND_MODEL_URL,
        },
        runningMode: "VIDEO",
        numHands: 2,
        minHandDetectionConfidence: 0.5,
        minHandPresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
      }
    );
  })();

  try {
    await initializationPromise;
  } catch (error) {
    initializationPromise = null;
    poseLandmarker = null;
    handLandmarker = null;
    throw error;
  }
}

export function detectFrame(
  video: HTMLVideoElement,
  timestampMs: number
): VisionFrameResult {
  if (!poseLandmarker || !handLandmarker) {
    throw new Error("MediaPipe has not been initialized.");
  }

  const poseResult =
    poseLandmarker.detectForVideo(video, timestampMs);

  const handResult =
    handLandmarker.detectForVideo(video, timestampMs);

  const poseLandmarks =
    poseResult.landmarks?.[0] ?? [];

  const handLandmarks =
    handResult.landmarks ?? [];

  const handedness = (handResult.handedness ?? []).map(
    (categories) =>
      categories?.[0]?.categoryName ?? "Unknown"
  );

  return {
    poseLandmarks,
    handLandmarks,
    handedness,
  };
}
