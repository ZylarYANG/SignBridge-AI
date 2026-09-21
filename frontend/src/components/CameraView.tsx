import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  detectFrame,
  initializeMediaPipe,
  type VisionFrameResult,
} from "../services/mediapipe";

import {
  canonicalizeFrame,
} from "../services/landmarkProcessor";

import type {
  LandmarkFrame,
} from "../types/landmark";

import {
  prepareSequence,
} from "../services/sequenceProcessor";

type CameraStatus =
  | "initializing"
  | "ready"
  | "permission-denied"
  | "error";

type VisionStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error";

type CaptureStatus =
  | "idle"
  | "countdown"
  | "capturing"
  | "done";

const COUNTDOWN_MS = 1000;

const CAPTURE_DURATION_MS = 2000;

const BODY_INDICES = [
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
];

const BODY_CONNECTIONS: Array<[number, number]> = [
  [11, 12],
  [11, 13],
  [13, 15],
  [12, 14],
  [14, 16],
  [11, 23],
  [12, 24],
  [23, 24],
];

const HAND_CONNECTIONS: Array<[number, number]> = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],

  [0, 5],
  [5, 6],
  [6, 7],
  [7, 8],

  [5, 9],
  [9, 10],
  [10, 11],
  [11, 12],

  [9, 13],
  [13, 14],
  [14, 15],
  [15, 16],

  [13, 17],
  [17, 18],
  [18, 19],
  [19, 20],

  [0, 17],
];

function drawPoint(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius = 4
) {
  ctx.beginPath();
  ctx.arc(
    x * width,
    y * height,
    radius,
    0,
    Math.PI * 2
  );
  ctx.fill();
}

function drawConnection(
  ctx: CanvasRenderingContext2D,
  a: { x: number; y: number },
  b: { x: number; y: number },
  width: number,
  height: number
) {
  ctx.beginPath();
  ctx.moveTo(a.x * width, a.y * height);
  ctx.lineTo(b.x * width, b.y * height);
  ctx.stroke();
}

function drawResults(
  canvas: HTMLCanvasElement,
  result: VisionFrameResult
) {
  const ctx = canvas.getContext("2d");

  if (!ctx) {
    return;
  }

  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);

  ctx.lineWidth = 3;
  ctx.strokeStyle = "#69e6ff";
  ctx.fillStyle = "#ffffff";

  const pose = result.poseLandmarks;

  if (pose.length > 0) {
    for (const [aIndex, bIndex] of BODY_CONNECTIONS) {
      const a = pose[aIndex];
      const b = pose[bIndex];

      if (a && b) {
        drawConnection(
          ctx,
          a,
          b,
          width,
          height
        );
      }
    }

    for (const index of BODY_INDICES) {
      const point = pose[index];

      if (point) {
        drawPoint(
          ctx,
          point.x,
          point.y,
          width,
          height,
          5
        );
      }
    }

    const leftShoulder = pose[11];
    const rightShoulder = pose[12];

    if (leftShoulder && rightShoulder) {
      const center = {
        x:
          (leftShoulder.x +
            rightShoulder.x) /
          2,
        y:
          (leftShoulder.y +
            rightShoulder.y) /
          2,
      };

      ctx.fillStyle = "#ffd166";

      drawPoint(
        ctx,
        center.x,
        center.y,
        width,
        height,
        6
      );

      ctx.fillStyle = "#ffffff";
    }
  }

  result.handLandmarks.forEach(
    (hand, handIndex) => {
      ctx.strokeStyle =
        handIndex === 0
          ? "#7cf29a"
          : "#ff9bd5";

      ctx.fillStyle =
        handIndex === 0
          ? "#7cf29a"
          : "#ff9bd5";

      for (const [aIndex, bIndex] of HAND_CONNECTIONS) {
        const a = hand[aIndex];
        const b = hand[bIndex];

        if (a && b) {
          drawConnection(
            ctx,
            a,
            b,
            width,
            height
          );
        }
      }

      for (const point of hand) {
        drawPoint(
          ctx,
          point.x,
          point.y,
          width,
          height,
          3
        );
      }
    }
  );
}

export function CameraView() {
  const videoRef =
    useRef<HTMLVideoElement | null>(null);

  const canvasRef =
    useRef<HTMLCanvasElement | null>(null);

  const streamRef =
    useRef<MediaStream | null>(null);

  const animationFrameRef =
    useRef<number | null>(null);

  const lastVideoTimeRef =
    useRef<number>(-1);

  const isCapturingRef =
    useRef(false);

  const capturedFramesRef =
    useRef<LandmarkFrame[]>([]);

  const [cameraStatus, setCameraStatus] =
    useState<CameraStatus>("initializing");

  const [visionStatus, setVisionStatus] =
    useState<VisionStatus>("idle");

  const [errorMessage, setErrorMessage] =
    useState("");

  const [poseDetected, setPoseDetected] =
    useState(false);

  const [handsDetected, setHandsDetected] =
    useState(0);

  const [
    canonicalValidCount,
    setCanonicalValidCount,
  ] = useState(0);
  
  const [
    canonicalValidRatio,
    setCanonicalValidRatio,
  ] = useState(0);

  const [
    captureStatus,
    setCaptureStatus,
  ] =
    useState<CaptureStatus>(
      "idle"
    );

  const [
    capturedFrameCount,
    setCapturedFrameCount,
  ] =
    useState(0);

  const [
    lastCaptureDuration,
    setLastCaptureDuration,
  ] =
    useState(0);

  const [handedness, setHandedness] =
    useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      try {
        setCameraStatus("initializing");

        const stream =
          await navigator.mediaDevices.getUserMedia({
            video: {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              frameRate: { ideal: 30 },
              facingMode: "user",
            },
            audio: false,
          });

        if (cancelled) {
          stream
            .getTracks()
            .forEach((track) => track.stop());

          return;
        }

        streamRef.current = stream;

        const video = videoRef.current;

        if (!video) {
          throw new Error(
            "Video element not available."
          );
        }

        video.srcObject = stream;

        await video.play();

        setCameraStatus("ready");
      } catch (error) {
        console.error(
          "Camera initialization failed:",
          error
        );

        if (
          error instanceof DOMException &&
          error.name === "NotAllowedError"
        ) {
          setCameraStatus(
            "permission-denied"
          );

          setErrorMessage(
            "摄像头权限被拒绝，请允许浏览器访问摄像头。"
          );
        } else {
          setCameraStatus("error");

          setErrorMessage(
            "无法打开摄像头，请检查摄像头是否被其他程序占用。"
          );
        }
      }
    }

    startCamera();

    return () => {
      cancelled = true;

      streamRef.current
        ?.getTracks()
        .forEach((track) => track.stop());
    };
  }, []);

  useEffect(() => {
    if (cameraStatus !== "ready") {
      return;
    }

    let cancelled = false;

    async function startVision() {
      try {
        setVisionStatus("loading");

        await initializeMediaPipe();

        if (cancelled) {
          return;
        }

        setVisionStatus("ready");

        runDetectionLoop();
      } catch (error) {
        console.error(
          "MediaPipe initialization failed:",
          error
        );

        setVisionStatus("error");

        setErrorMessage(
          "MediaPipe 初始化失败，请检查网络或浏览器 Console。"
        );
      }
    }

    function runDetectionLoop() {
      if (cancelled) {
        return;
      }

      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (
        video &&
        canvas &&
        video.readyState >= 2
      ) {
        if (
          video.currentTime !==
          lastVideoTimeRef.current
        ) {
          lastVideoTimeRef.current =
            video.currentTime;

          if (
            video.videoWidth > 0 &&
            video.videoHeight > 0
          ) {
            if (
              canvas.width !==
              video.videoWidth
            ) {
              canvas.width =
                video.videoWidth;
            }

            if (
              canvas.height !==
              video.videoHeight
            ) {
              canvas.height =
                video.videoHeight;
            }
          }

          try {
            const timestampMs =
              performance.now();

            const result = detectFrame(
              video,
              timestampMs
            );

            const canonical =
              canonicalizeFrame(
                result,
                timestampMs
              );

            drawResults(
              canvas,
              result
            );

            setPoseDetected(
              canonical.poseDetected
            );

            setHandsDetected(
              result.handLandmarks.length
            );

            setHandedness(
              result.handedness
            );

            setCanonicalValidCount(
              canonical.validCount
            );

            setCanonicalValidRatio(
              canonical.validRatio
            );

            if (
              isCapturingRef.current
            ) {
              capturedFramesRef.current.push(
                canonical.frame
              );

              setCapturedFrameCount(
                capturedFramesRef.current.length
              );
            }

          } catch (error) {
            console.error(
              "MediaPipe frame detection failed:",
              error
            );
          }
        }
      }

      animationFrameRef.current =
        requestAnimationFrame(
          runDetectionLoop
        );
    }

    startVision();

    return () => {
      cancelled = true;

      if (
        animationFrameRef.current !==
        null
      ) {
        cancelAnimationFrame(
          animationFrameRef.current
        );

        animationFrameRef.current =
          null;
      }
    };
  }, [cameraStatus]);

  function startCapture() {
    if (
      cameraStatus !== "ready" ||
      visionStatus !== "ready"
    ) {
     return;
    }

    if (
      captureStatus ===
       "countdown" ||
      captureStatus ===
        "capturing"
   ) {
      return;
    }

    /*
    * 清空上一次动作
    */
    capturedFramesRef.current = [];

    setCapturedFrameCount(0);

    setLastCaptureDuration(0);

    isCapturingRef.current =
      false;

    /*
    * 进入倒计时
    */
    setCaptureStatus(
      "countdown"
    );

    window.setTimeout(
      () => {
        /*
        * 正式开始采集
        */
        capturedFramesRef.current = [];

        setCapturedFrameCount(0);

        const captureStartTime =
          performance.now();

        isCapturingRef.current =
          true;

        setCaptureStatus(
          "capturing"
        );

        window.setTimeout(
          () => {
            /*
            * 结束采集
            */
            isCapturingRef.current =
              false;

            const captureEndTime =
              performance.now();

            const duration =
              (
                captureEndTime -
                captureStartTime
              ) /
              1000;

            setLastCaptureDuration(
              duration
            );

            setCaptureStatus(
              "done"
            );

            const frames =
              capturedFramesRef.current;

            console.log(
              "===== SignBridge Raw Capture ====="
            );

            console.log(
              "Frames:",
              frames.length
            );

            console.log(
              "Canonical shape:",
              `[${frames.length}, 54, 2]`
            );

            console.log(
              "Duration:",
              duration.toFixed(3),
              "seconds"
            );

            console.log(
              "Raw sequence:",
              frames
            );

            const processed =
              prepareSequence(
                frames
              );

            console.log(
              "===== SignBridge Preprocessing ====="
            );

            console.log(
              "Normalized frames:",
              processed
                .normalizedFrames
                .length
            );

            console.log(
              "Resampled frames:",
              processed
                .resampledFrames
                .length
            );

            console.log(
              "Model shape:",
              `[${processed.modelInput.length}, ${
                processed.modelInput[0]?.length
              }, ${
                processed.modelInput[0]?.[0]?.length
              }]`
            );

            console.log(
              "Model input:",
              processed.modelInput
            );

            console.log(
              "Normalized first frame:",
              processed
                .normalizedFrames[0]
            );

            const firstNormalizedFrame =
              processed
                .normalizedFrames[0];

            const leftShoulder =
              firstNormalizedFrame
                .landmarks[45];

            const rightShoulder =
              firstNormalizedFrame
                .landmarks[46];

            const shoulderCenter =
              firstNormalizedFrame
                .landmarks[53];

            const shoulderDistance =
              Math.sqrt(
                (
                  rightShoulder.x -
                  leftShoulder.x
                ) ** 2 +
                (
                  rightShoulder.y -
                  leftShoulder.y
                ) ** 2
              );

            console.log(
              "Shoulder center:",
              shoulderCenter
            );

            console.log(
              "Normalized shoulder distance:",
              shoulderDistance
            );

          },
          CAPTURE_DURATION_MS
        );
      },
      COUNTDOWN_MS
    );
  }

  const cameraLabel =
    cameraStatus === "initializing"
      ? "正在初始化"
      : cameraStatus === "ready"
        ? "摄像头已就绪"
        : cameraStatus ===
            "permission-denied"
          ? "权限被拒绝"
          : "摄像头异常";

  const visionLabel =
    visionStatus === "idle"
      ? "等待摄像头"
      : visionStatus === "loading"
        ? "正在加载 MediaPipe"
        : visionStatus === "ready"
          ? "MediaPipe 已就绪"
          : "MediaPipe 异常";

  const captureLabel =
    captureStatus === "idle"
      ? "准备练习"
      : captureStatus ===
          "countdown"
        ? "1 秒后开始"
        : captureStatus ===
            "capturing"
          ? "正在采集"
          : "采集完成";

  return (
    <section className="camera-panel">
      <div className="camera-header">
        <div>
          <h2>实时练习画面</h2>

          <p>
            请保持上半身和双手完整进入画面
          </p>
        </div>

        <div className="status-stack">
          <span
            className={`status status-${cameraStatus}`}
          >
            {cameraLabel}
          </span>

          <span className="status">
            {visionLabel}
          </span>
        </div>
      </div>

      <div className="video-shell">
        <video
          ref={videoRef}
          className="camera-video"
          autoPlay
          muted
          playsInline
        />

        <canvas
          ref={canvasRef}
          className="landmark-canvas"
        />

        {captureStatus ===
          "countdown" && (
          <div className="capture-overlay">
            1
          </div>
        )}

        {captureStatus ===
          "capturing" && (
          <div
            className="
              capture-overlay
              capture-overlay-recording
            "
          >
            ● REC
          </div>
        )}

      </div>

      <div className="vision-metrics">
        <div className="vision-metric">
          <span>Pose</span>

          <strong>
            {poseDetected
              ? "Detected"
              : "Not detected"}
          </strong>
        </div>

        <div className="vision-metric">
          <span>Hands</span>

          <strong>
            {handsDetected} / 2
          </strong>
        </div>

        <div className="vision-metric">
          <span>Handedness</span>

          <strong>
            {handedness.length > 0
              ? handedness.join(" / ")
              : "—"}
          </strong>
        </div>

        <div className="vision-metric">
          <span>Canonical</span>

          <strong>
            {canonicalValidCount}
            {" / 54 · "}
            {(
              canonicalValidRatio * 100
            ).toFixed(1)}
            %
          </strong>
        </div>

      </div>

      <div className="capture-controls">
        <div>
          <span className="capture-label">
            Capture
          </span>

          <strong>
            {captureLabel}
          </strong>
        </div>

        <div>
          <span className="capture-label">
            Frames
          </span>

          <strong>
            {capturedFrameCount}
          </strong>
        </div>

        <div>
          <span className="capture-label">
            Duration
          </span>

          <strong>
            {lastCaptureDuration >
            0
              ?
                `${lastCaptureDuration.toFixed(
                  2
                )} s`
              : "—"}
          </strong>
        </div>

        <button
          className="primary-button"
          onClick={startCapture}
          disabled={
            visionStatus !==
              "ready" ||
            captureStatus ===
              "countdown" ||
            captureStatus ===
              "capturing"
          }
        >
          {captureStatus ===
            "capturing"
            ? "正在采集..."
            : "开始练习"}
        </button>
      </div>

      {errorMessage && (
        <p className="error-message">
          {errorMessage}
        </p>
      )}
    </section>
  );
}
