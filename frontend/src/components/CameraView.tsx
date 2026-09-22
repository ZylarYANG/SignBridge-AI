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

import {
  prepareSequence,
} from "../services/sequenceProcessor";

import {
  saveDatasetSample,
  submitPractice,
  type DatasetSampleResponse,
  type PracticeResponse,
} from "../services/api";

import {
  buildSampleId,
  calculateDatasetQuality,
  COLLECTION_SIGNS,
  getCaptureDurationMs,
  getLiveInputReadiness,
  toDatasetRawFrames,
} from "../services/collection";

import type {
  LandmarkFrame,
} from "../types/landmark";


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
  | "processing"
  | "done"
  | "error";

type WorkMode =
  | "practice"
  | "collection";


const COUNTDOWN_MS = 1000;
const CAPTURE_DURATION_MS = 2000;


const BODY_INDICES = [
  0,
  9,
  10,
  11,
  12,
  13,
  14,
  15,
  16,
  23,
  24,
];


const BODY_CONNECTIONS:
  Array<[number, number]> = [
    [11, 12],
    [11, 13],
    [13, 15],
    [12, 14],
    [14, 16],
    [11, 23],
    [12, 24],
    [23, 24],
  ];


const HAND_CONNECTIONS:
  Array<[number, number]> = [
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
  a: {
    x: number;
    y: number;
  },
  b: {
    x: number;
    y: number;
  },
  width: number,
  height: number
) {
  ctx.beginPath();

  ctx.moveTo(
    a.x * width,
    a.y * height
  );

  ctx.lineTo(
    b.x * width,
    b.y * height
  );

  ctx.stroke();
}


function drawResults(
  canvas: HTMLCanvasElement,
  result: VisionFrameResult
) {
  const ctx =
    canvas.getContext("2d");

  if (!ctx) {
    return;
  }

  const width =
    canvas.width;

  const height =
    canvas.height;

  ctx.clearRect(
    0,
    0,
    width,
    height
  );

  ctx.lineWidth = 3;

  ctx.strokeStyle =
    "#69e6ff";

  ctx.fillStyle =
    "#ffffff";

  const pose =
    result.poseLandmarks;

  if (pose.length > 0) {
    for (
      const [
        aIndex,
        bIndex,
      ] of BODY_CONNECTIONS
    ) {
      const a =
        pose[aIndex];

      const b =
        pose[bIndex];

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

    for (
      const index
      of BODY_INDICES
    ) {
      const point =
        pose[index];

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

    const leftShoulder =
      pose[11];

    const rightShoulder =
      pose[12];

    if (
      leftShoulder &&
      rightShoulder
    ) {
      const center = {
        x:
          (
            leftShoulder.x +
            rightShoulder.x
          ) / 2,

        y:
          (
            leftShoulder.y +
            rightShoulder.y
          ) / 2,
      };

      ctx.fillStyle =
        "#ffd166";

      drawPoint(
        ctx,
        center.x,
        center.y,
        width,
        height,
        6
      );

      ctx.fillStyle =
        "#ffffff";
    }
  }

  result.handLandmarks.forEach(
    (
      hand,
      handIndex
    ) => {
      ctx.strokeStyle =
        handIndex === 0
          ? "#7cf29a"
          : "#ff9bd5";

      ctx.fillStyle =
        handIndex === 0
          ? "#7cf29a"
          : "#ff9bd5";

      for (
        const [
          aIndex,
          bIndex,
        ] of HAND_CONNECTIONS
      ) {
        const a =
          hand[aIndex];

        const b =
          hand[bIndex];

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

      for (
        const point
        of hand
      ) {
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
  /*
   * =========================
   * Refs
   * =========================
   */

  const videoRef =
    useRef<HTMLVideoElement | null>(
      null
    );

  const canvasRef =
    useRef<HTMLCanvasElement | null>(
      null
    );

  const streamRef =
    useRef<MediaStream | null>(
      null
    );

  const animationFrameRef =
    useRef<number | null>(
      null
    );

  const lastVideoTimeRef =
    useRef(-1);

  const isCapturingRef =
    useRef(false);

  const capturedFramesRef =
    useRef<LandmarkFrame[]>([]);

  const countdownTimerRef =
    useRef<number | null>(
      null
    );

  const captureTimerRef =
    useRef<number | null>(
      null
    );


  /*
   * =========================
   * Camera / Vision State
   * =========================
   */

  const [
    cameraStatus,
    setCameraStatus,
  ] =
    useState<CameraStatus>(
      "initializing"
    );

  const [
    visionStatus,
    setVisionStatus,
  ] =
    useState<VisionStatus>(
      "idle"
    );

  const [
    captureStatus,
    setCaptureStatus,
  ] =
    useState<CaptureStatus>(
      "idle"
    );

  const [
    errorMessage,
    setErrorMessage,
  ] =
    useState("");

  const [
    poseDetected,
    setPoseDetected,
  ] =
    useState(false);

  const [
    handsDetected,
    setHandsDetected,
  ] =
    useState(0);

  const [
    handedness,
    setHandedness,
  ] =
    useState<string[]>([]);

  const [
    canonicalValidCount,
    setCanonicalValidCount,
  ] =
    useState(0);

  const [
    canonicalValidRatio,
    setCanonicalValidRatio,
  ] =
    useState(0);

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


  /*
   * =========================
   * Work Mode State
   * =========================
   */

  const [
    workMode,
    setWorkMode,
  ] =
    useState<WorkMode>(
      "practice"
    );

  const [
    signerId,
    setSignerId,
  ] =
    useState("S001");

  const [
    selectedSignId,
    setSelectedSignId,
  ] =
    useState(
      COLLECTION_SIGNS[0].signId
    );

  const [
    takeId,
    setTakeId,
  ] =
    useState(1);


  /*
   * =========================
   * API Result State
   * =========================
   */

  const [
    practiceResult,
    setPracticeResult,
  ] =
    useState<
      PracticeResponse | null
    >(null);

  const [
    datasetResult,
    setDatasetResult,
  ] =
    useState<
      DatasetSampleResponse | null
    >(null);


  /*
   * =========================
   * Derived Data
   * =========================
   */

  const selectedSign =
    COLLECTION_SIGNS.find(
      (sign) =>
        sign.signId ===
        selectedSignId
    ) ??
    COLLECTION_SIGNS[0];

  const previewSampleId =
    buildSampleId(
      signerId || "S001",
      selectedSign.signId,
      takeId
    );


  const liveInputReadiness =
    getLiveInputReadiness(
      selectedSign,
      poseDetected,
      handsDetected
    );


  /*
   * =========================
   * Camera Effect
   * =========================
   */

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      try {
        setCameraStatus(
          "initializing"
        );

        const stream =
          await navigator
            .mediaDevices
            .getUserMedia({
              video: {
                width: {
                  ideal: 1280,
                },

                height: {
                  ideal: 720,
                },

                frameRate: {
                  ideal: 30,
                },

                facingMode:
                  "user",
              },

              audio: false,
            });

        if (cancelled) {
          stream
            .getTracks()
            .forEach(
              (track) =>
                track.stop()
            );

          return;
        }

        streamRef.current =
          stream;

        const video =
          videoRef.current;

        if (!video) {
          throw new Error(
            "Video element not available."
          );
        }

        video.srcObject =
          stream;

        await video.play();

        setCameraStatus(
          "ready"
        );
      } catch (error) {
        console.error(
          "Camera initialization failed:",
          error
        );

        if (
          error instanceof
            DOMException &&
          error.name ===
            "NotAllowedError"
        ) {
          setCameraStatus(
            "permission-denied"
          );

          setErrorMessage(
            "摄像头权限被拒绝，请允许浏览器访问摄像头。"
          );
        } else {
          setCameraStatus(
            "error"
          );

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
        .forEach(
          (track) =>
            track.stop()
        );
    };
  }, []);


  /*
   * =========================
   * MediaPipe Effect
   * =========================
   */

  useEffect(() => {
    if (
      cameraStatus !==
      "ready"
    ) {
      return;
    }

    let cancelled = false;

    async function startVision() {
      try {
        setVisionStatus(
          "loading"
        );

        await initializeMediaPipe();

        if (cancelled) {
          return;
        }

        setVisionStatus(
          "ready"
        );

        runDetectionLoop();
      } catch (error) {
        console.error(
          "MediaPipe initialization failed:",
          error
        );

        setVisionStatus(
          "error"
        );

        setErrorMessage(
          "MediaPipe 初始化失败，请检查网络或浏览器 Console。"
        );
      }
    }

    function runDetectionLoop() {
      if (cancelled) {
        return;
      }

      const video =
        videoRef.current;

      const canvas =
        canvasRef.current;

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

            const result =
              detectFrame(
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
              result
                .handLandmarks
                .length
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
              capturedFramesRef
                .current
                .push(
                  canonical.frame
                );

              setCapturedFrameCount(
                capturedFramesRef
                  .current
                  .length
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
        animationFrameRef
          .current !== null
      ) {
        cancelAnimationFrame(
          animationFrameRef
            .current
        );

        animationFrameRef
          .current = null;
      }
    };
  }, [cameraStatus]);


  /*
   * =========================
   * Timer Cleanup
   * =========================
   */

  useEffect(() => {
    return () => {
      if (
        countdownTimerRef
          .current !== null
      ) {
        window.clearTimeout(
          countdownTimerRef
            .current
        );
      }

      if (
        captureTimerRef
          .current !== null
      ) {
        window.clearTimeout(
          captureTimerRef
            .current
        );
      }
    };
  }, []);


  /*
   * =========================
   * Process Finished Capture
   * =========================
   */

  async function processCapture(
    frames: LandmarkFrame[],
    modeAtCapture: WorkMode
  ) {
    try {
      setCaptureStatus(
        "processing"
      );

      setErrorMessage("");

      if (
        frames.length < 10
      ) {
        throw new Error(
          `采集帧数过少：${frames.length}`
        );
      }

      const processed =
        prepareSequence(
          frames
        );

      const durationMs =
        getCaptureDurationMs(
          frames
        );

      setLastCaptureDuration(
        durationMs / 1000
      );

      console.log(
        "===== SignBridge Capture ====="
      );

      console.log(
        "Mode:",
        modeAtCapture
      );

      console.log(
        "Raw frames:",
        frames.length
      );

      console.log(
        "Model shape:",
        `[${processed.modelInput.length}, ${processed.modelInput[0]?.length}, ${processed.modelInput[0]?.[0]?.length}]`
      );


      /*
       * =====================
       * PRACTICE MODE
       * =====================
       */

      if (
        modeAtCapture ===
        "practice"
      ) {
        setPracticeResult(
          null
        );

        setDatasetResult(
          null
        );

        const response =
          await submitPractice({
            request_id:
              `practice_${Date.now()}`,

            target_sign_id:
              selectedSign.signId,

            raw_frame_count:
              frames.length,

            sequence_length:
              processed
                .modelInput
                .length,

            landmarks:
              processed.modelInput,
          });

        setPracticeResult(
          response
        );

        setCaptureStatus(
          "done"
        );

        return;
      }


      /*
       * =====================
       * COLLECTION MODE
       * =====================
       */

      const normalizedSigner =
        signerId
          .trim()
          .toUpperCase();

      if (
        !/^S\d{3,}$/.test(
          normalizedSigner
        )
      ) {
        throw new Error(
          "Signer ID 格式错误，请使用 S001、S002 等格式。"
        );
      }

      const sampleId =
        buildSampleId(
          normalizedSigner,
          selectedSign.signId,
          takeId
        );

      const quality =
        calculateDatasetQuality(
          frames,
          selectedSign
        );

      const rawFrames =
        toDatasetRawFrames(
          frames
        );

      console.log(
        "Sample ID:",
        sampleId
      );

      console.log(
        "Dataset quality:",
        quality
      );

      setPracticeResult(
        null
      );

      setDatasetResult(
        null
      );

      const response =
        await saveDatasetSample({
          schema_version:
            "1.0",

          sample_id:
            sampleId,

          signer_id:
            normalizedSigner,

          sign_id:
            selectedSign.signId,

          take_id:
            takeId,

          label:
            selectedSign.label,

          capture: {
            duration_ms:
              durationMs,

            raw_frame_count:
              frames.length,
          },

          quality: {
            input_usable:
              quality.inputUsable,

            landmark_valid_ratio:
              quality
                .landmarkValidRatio,

            shoulder_usable_ratio:
              quality
                .shoulderUsableRatio,

            left_hand_usable_ratio:
              quality
                .leftHandUsableRatio,

            right_hand_usable_ratio:
              quality
                .rightHandUsableRatio,

            both_hands_usable_ratio:
              quality
                .bothHandsUsableRatio,

            active_hand:
              quality
                .activeHand,
          },

          raw_frames:
            rawFrames,

          model_input:
            processed.modelInput,
        });

      setDatasetResult(
        response
      );

      /*
       * 保存成功以后，
       * 自动进入下一 Take。
       */
      setTakeId(
        (current) =>
          current + 1
      );

      setCaptureStatus(
        "done"
      );
    } catch (error) {
      console.error(
        "Capture processing failed:",
        error
      );

      setCaptureStatus(
        "error"
      );

      setErrorMessage(
        error instanceof Error
          ? error.message
          : "动作处理失败。"
      );
    }
  }


  /*
   * =========================
   * Start Capture
   * =========================
   */

  function startCapture() {
    if (
      cameraStatus !==
        "ready" ||
      visionStatus !==
        "ready"
    ) {
      return;
    }

    if (
      captureStatus ===
        "countdown" ||
      captureStatus ===
        "capturing" ||
      captureStatus ===
        "processing"
    ) {
      return;
    }

    if (
      workMode ===
        "collection" &&
      !signerId.trim()
    ) {
      setErrorMessage(
        "请先填写 Signer ID。"
      );

      return;
    }

    const modeAtCapture =
      workMode;

    capturedFramesRef.current =
      [];

    isCapturingRef.current =
      false;

    setCapturedFrameCount(
      0
    );

    setLastCaptureDuration(
      0
    );

    setPracticeResult(
      null
    );

    setDatasetResult(
      null
    );

    setErrorMessage("");

    setCaptureStatus(
      "countdown"
    );

    countdownTimerRef.current =
      window.setTimeout(
        () => {
          capturedFramesRef
            .current = [];

          setCapturedFrameCount(
            0
          );

          isCapturingRef.current =
            true;

          setCaptureStatus(
            "capturing"
          );

          captureTimerRef.current =
            window.setTimeout(
              () => {
                isCapturingRef
                  .current =
                  false;

                const frames = [
                  ...capturedFramesRef
                    .current,
                ];

                void processCapture(
                  frames,
                  modeAtCapture
                );
              },

              CAPTURE_DURATION_MS
            );
        },

        COUNTDOWN_MS
      );
  }


  /*
   * =========================
   * Mode Change
   * =========================
   */

  function changeMode(
    nextMode: WorkMode
  ) {
    if (
      captureStatus ===
        "countdown" ||
      captureStatus ===
        "capturing" ||
      captureStatus ===
        "processing"
    ) {
      return;
    }

    setWorkMode(
      nextMode
    );

    setPracticeResult(
      null
    );

    setDatasetResult(
      null
    );

    setErrorMessage("");

    setCaptureStatus(
      "idle"
    );
  }


  /*
   * =========================
   * Labels
   * =========================
   */

  const cameraLabel =
    cameraStatus ===
    "initializing"
      ? "正在初始化"
      : cameraStatus ===
          "ready"
        ? "摄像头已就绪"
        : cameraStatus ===
            "permission-denied"
          ? "权限被拒绝"
          : "摄像头异常";


  const visionLabel =
    visionStatus ===
    "idle"
      ? "等待摄像头"
      : visionStatus ===
          "loading"
        ? "正在加载 MediaPipe"
        : visionStatus ===
            "ready"
          ? "MediaPipe 已就绪"
          : "MediaPipe 异常";


  const captureLabel =
    captureStatus ===
    "idle"
      ? "准备就绪"
      : captureStatus ===
          "countdown"
        ? "1 秒后开始"
        : captureStatus ===
            "capturing"
          ? "正在采集"
          : captureStatus ===
              "processing"
            ? "正在处理 / 保存"
            : captureStatus ===
                "done"
              ? "完成"
              : "失败";


  const captureBusy =
    captureStatus ===
      "countdown" ||
    captureStatus ===
      "capturing" ||
    captureStatus ===
      "processing";


  /*
   * =========================
   * JSX
   * =========================
   */

  return (
    <section className="camera-panel">
      <div className="mode-switch">
        <button
          type="button"
          className={
            workMode ===
            "practice"
              ? "mode-button mode-button-active"
              : "mode-button"
          }
          onClick={() =>
            changeMode(
              "practice"
            )
          }
          disabled={
            captureBusy
          }
        >
          练习模式
        </button>

        <button
          type="button"
          className={
            workMode ===
            "collection"
              ? "mode-button mode-button-active"
              : "mode-button"
          }
          onClick={() =>
            changeMode(
              "collection"
            )
          }
          disabled={
            captureBusy
          }
        >
          数据采集模式
        </button>
      </div>


      {workMode ===
        "collection" && (
        <div className="collection-panel">
          <div className="collection-field">
            <label
              htmlFor="signer-id"
            >
              Signer ID
            </label>

            <input
              id="signer-id"
              value={signerId}
              onChange={(
                event
              ) =>
                setSignerId(
                  event.target
                    .value
                )
              }
              disabled={
                captureBusy
              }
              placeholder="S001"
            />

            <small>
              每位采集者使用固定编号，例如 S001、S002。
            </small>
          </div>


          <div className="collection-field">
            <label
              htmlFor="sign-select"
            >
              Sign
            </label>

            <select
              id="sign-select"
              value={
                selectedSignId
              }
              disabled={
                captureBusy
              }
              onChange={(
                event
              ) => {
                setSelectedSignId(
                  event.target
                    .value
                );

                /*
                 * 换词后从 Take 1
                 * 重新开始。
                 */
                setTakeId(1);

                setDatasetResult(
                  null
                );

                setErrorMessage(
                  ""
                );
              }}
            >
              {COLLECTION_SIGNS.map(
                (sign) => (
                  <option
                    key={
                      sign.signId
                    }
                    value={
                      sign.signId
                    }
                  >
                    {sign.classId}
                    {" · "}
                    {sign.label}
                    {" · "}
                    {sign.signId}
                  </option>
                )
              )}
            </select>

            <small>
              Class：
              {selectedSign.classId}
            </small>
          </div>


          <div className="collection-field">
            <label
              htmlFor="take-id"
            >
              Take
            </label>

            <input
              id="take-id"
              type="number"
              min={1}
              value={takeId}
              disabled={
                captureBusy
              }
              onChange={(
                event
              ) => {
                const value =
                  Number(
                    event.target
                      .value
                  );

                setTakeId(
                  Number.isFinite(
                    value
                  )
                    ?
                      Math.max(
                        1,
                        Math.floor(
                          value
                        )
                      )
                    : 1
                );
              }}
            />

            <small>
              保存成功后自动 +1
            </small>
          </div>


          <div className="sample-preview">
            <span>
              Sample ID
            </span>

            <code>
              {previewSampleId}
            </code>
          </div>
        </div>
      )}


      {workMode ===
        "practice" && (
        <div className="practice-target">
          <span>
            当前练习词
          </span>

          <strong>
            {selectedSign.label}
          </strong>

          <code>
            {selectedSign.signId}
          </code>

          <select
            value={
              selectedSignId
            }
            disabled={
              captureBusy
            }
            onChange={(
              event
            ) =>
              setSelectedSignId(
                event.target
                  .value
              )
            }
          >
            {COLLECTION_SIGNS.map(
              (sign) => (
                <option
                  key={
                    sign.signId
                  }
                  value={
                    sign.signId
                  }
                >
                  {sign.label}
                  {" · "}
                  {sign.signId}
                </option>
              )
            )}
          </select>
        </div>
      )}


      <div className="camera-header">
        <div>
          <h2>
            {workMode ===
            "collection"
              ? "训练数据采集"
              : "实时练习画面"}
          </h2>

          <p>
            请保持上半身和手部完整进入画面
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
          <div className="capture-overlay capture-overlay-recording">
            ● REC
          </div>
        )}


        {captureStatus ===
          "processing" && (
          <div className="capture-overlay">
            处理中
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
            {handsDetected}
            {" / 2"}
          </strong>
        </div>

        <div className="vision-metric">
          <span>
            Handedness
          </span>

          <strong>
            {handedness.length >
            0
              ?
                handedness.join(
                  " / "
                )
              : "—"}
          </strong>
        </div>

        <div className="vision-metric">
          <span>
            Canonical
          </span>

          <strong>
            {
              canonicalValidCount
            }
            {" / 54 · "}
            {(
              canonicalValidRatio *
              100
            ).toFixed(1)}
            %
          </strong>
        </div>
      </div>


      <div className="capture-controls">
        <div>
          <span className="capture-label">
            Status
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
          onClick={
            startCapture
          }
          disabled={
            visionStatus !==
              "ready" ||
            captureBusy ||
            (
              workMode ===
                "collection" &&
              !liveInputReadiness
                .ready
            )
          }
        >
          {captureBusy
            ? captureLabel
            : workMode ===
                "collection"
              ?
                "采集并保存样本"
              :
                "开始练习"}
        </button>
      </div>


      {practiceResult && (
        <div className="api-result">
          <strong>
            FastAPI 练习接口成功
          </strong>

          <p>
            Status：
            {
              practiceResult.status
            }
          </p>

          <p>
            Mode：
            {
              practiceResult.mode
            }
          </p>

          <p>
            Shape：
            {
              practiceResult
                .received_shape
                .join(
                  " × "
                )
            }
          </p>
        </div>
      )}


      {datasetResult && (
        <div className="dataset-result">
          <strong>
            数据集样本保存成功
          </strong>

          <p>
            Sample：
            {
              datasetResult.sample_id
            }
          </p>

          <p>
            File：
            {
              datasetResult.file_path
            }
          </p>

          <p>
            Manifest：
            {
              datasetResult
                .manifest_updated
                ? "Updated"
                : "Not updated"
            }
          </p>

          <p>
            下一 Take：
            {takeId}
          </p>
        </div>
      )}


      {errorMessage && (
        <div className="api-error">
          <strong>
            操作失败
          </strong>

          <p>
            {errorMessage}
          </p>
        </div>
      )}
    </section>
  );
}
