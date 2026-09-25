import {
  useEffect,
  useState,
} from "react";


type WorkMode =
  | "practice"
  | "collection";


type CaptureStatus =
  | "idle"
  | "countdown"
  | "capturing"
  | "processing"
  | "done"
  | "error";


type WorkbenchStatusDetail = {
  workMode: WorkMode;

  signLabel: string;
  signId: string;

  signerId: string;

  profileName: string;
  targetTakes: number;

  usableCount: number;
  takeId: number;

  poseDetected: boolean;
  handsDetected: number;

  readinessReady: boolean;
  readinessMessage: string;

  captureStatus:
    CaptureStatus;

  countdownValue: number;

  cameraStatus: string;
  visionStatus: string;

  canCapture: boolean;
};


const INITIAL_STATUS:
  WorkbenchStatusDetail = {
    workMode:
      "practice",

    signLabel:
      "加载中",

    signId:
      "—",

    signerId:
      "—",

    profileName:
      "—",

    targetTakes:
      0,

    usableCount:
      0,

    takeId:
      1,

    poseDetected:
      false,

    handsDetected:
      0,

    readinessReady:
      false,

    readinessMessage:
      "等待视觉系统",

    captureStatus:
      "idle",

    countdownValue:
      0,

    cameraStatus:
      "initializing",

    visionStatus:
      "idle",

    canCapture:
      false,
  };


function getCaptureStatusLabel(
  status:
    WorkbenchStatusDetail
): string {
  switch (
    status.captureStatus
  ) {
    case "countdown":
      return (
        `倒计时 ${status.countdownValue}s`
      );

    case "capturing":
      return "正在采集";

    case "processing":
      return "正在处理";

    case "done":
      return "最近一次完成";

    case "error":
      return "采集失败";

    default:
      return status.readinessReady
        ?
          "待开始"
        :
          "等待就位";
  }
}


function getVisionLabel(
  status:
    WorkbenchStatusDetail
): string {
  if (
    status.visionStatus ===
    "ready"
  ) {
    return "MediaPipe Ready";
  }

  if (
    status.visionStatus ===
    "loading"
  ) {
    return "MediaPipe Loading";
  }

  if (
    status.cameraStatus ===
    "ready"
  ) {
    return "Camera Ready";
  }

  return "初始化中";
}


export function WorkbenchStatusPanel() {
  const [
    status,
    setStatus,
  ] =
    useState<
      WorkbenchStatusDetail
    >(
      INITIAL_STATUS
    );


  useEffect(() => {
    function handleStatus(
      rawEvent: Event
    ) {
      const event = rawEvent as CustomEvent<WorkbenchStatusDetail>;

      setStatus(
        event.detail
      );
    }


    window.addEventListener(
      "signbridge:workbench-status",
      handleStatus
    );


    return () => {
      window.removeEventListener(
        "signbridge:workbench-status",
        handleStatus
      );
    };
  }, []);


  function startCapture() {
    window.dispatchEvent(
      new CustomEvent(
        "signbridge:start-capture"
      )
    );
  }


  const collectionMode =
    status.workMode ===
    "collection";


  const captureLabel =
    getCaptureStatusLabel(
      status
    );


  return (
    <aside className="workbench-sidebar-card">

      <div className="workbench-sidebar-eyebrow">
        {
          collectionMode
            ?
              "当前采集"
            :
              "当前练习"
        }
      </div>


      <div className="workbench-sidebar-target">

        <h2>
          {
            status.signLabel
          }
        </h2>

        <code>
          {
            status.signId
          }
        </code>

      </div>


      {collectionMode ? (
        <>
          <div className="workbench-sidebar-section">

            <div className="workbench-status-row">
              <span>
                采集者
              </span>

              <strong>
                {
                  status.signerId
                }
              </strong>
            </div>


            <div className="workbench-status-row">
              <span>
                采集计划
              </span>

              <strong>
                {
                  status.profileName
                }
              </strong>
            </div>


            <div className="workbench-status-row">
              <span>
                当前进度
              </span>

              <strong>
                {
                  status.usableCount
                }
                {" / "}
                {
                  status.targetTakes
                }
              </strong>
            </div>


            <div className="workbench-status-row">
              <span>
                Next Take
              </span>

              <strong>
                {
                  status.takeId
                }
              </strong>
            </div>

          </div>


          <div className="workbench-sidebar-section">

            <div className="workbench-status-row">
              <span>
                Vision
              </span>

              <strong>
                {
                  getVisionLabel(
                    status
                  )
                }
              </strong>
            </div>


            <div className="workbench-status-row">
              <span>
                Pose
              </span>

              <strong
                className={
                  status.poseDetected
                    ?
                      "workbench-status-good"
                    :
                      "workbench-status-warning"
                }
              >
                {
                  status.poseDetected
                    ?
                      "Detected ✓"
                    :
                      "Not detected"
                }
              </strong>
            </div>


            <div className="workbench-status-row">
              <span>
                Hands
              </span>

              <strong>
                {
                  status.handsDetected
                }
                {" / 2"}
              </strong>
            </div>


            <div className="workbench-status-row">
              <span>
                Required Input
              </span>

              <strong
                className={
                  status.readinessReady
                    ?
                      "workbench-status-good"
                    :
                      "workbench-status-warning"
                }
              >
                {
                  status.readinessReady
                    ?
                      "Ready ✓"
                    :
                      "Warning"
                }
              </strong>
            </div>

          </div>


          <div
            className={
              status.readinessReady
                ?
                  "workbench-sidebar-readiness workbench-sidebar-readiness-good"
                :
                  "workbench-sidebar-readiness workbench-sidebar-readiness-warning"
            }
          >
            {
              status.readinessMessage
            }
          </div>


          <div className="workbench-capture-state">

            <span>
              采集状态
            </span>

            <strong>
              {
                captureLabel
              }
            </strong>

          </div>


          <button
            type="button"
            className="workbench-sidebar-primary"
            disabled={
              !status.canCapture
            }
            onClick={
              startCapture
            }
          >
            {
              status.captureStatus ===
              "countdown"
                ?
                  `准备中 ${status.countdownValue}`
                :
                  status.captureStatus ===
                  "capturing"
                    ?
                      "● 正在采集"
                    :
                      status.captureStatus ===
                      "processing"
                        ?
                          "正在处理"
                        :
                          "开始采集"
            }
          </button>


          <p className="workbench-sidebar-tip">
            Required Input 为 Warning
            时仍允许开始采集，可在倒计时期间完成就位。
          </p>

        </>
      ) : (
        <>
          <div className="workbench-sidebar-section">

            <div className="workbench-status-row">
              <span>
                系统阶段
              </span>

              <strong>
                {
                  getVisionLabel(
                    status
                  )
                }
              </strong>
            </div>


            <div className="workbench-status-row">
              <span>
                Pose
              </span>

              <strong>
                {
                  status.poseDetected
                    ?
                      "Detected ✓"
                    :
                      "等待检测"
                }
              </strong>
            </div>


            <div className="workbench-status-row">
              <span>
                Hands
              </span>

              <strong>
                {
                  status.handsDetected
                }
                {" / 2"}
              </strong>
            </div>

          </div>


          <button
            type="button"
            className="workbench-sidebar-primary"
            disabled={
              !status.canCapture
            }
            onClick={
              startCapture
            }
          >
            {
              status.captureStatus ===
              "capturing"
                ?
                  "正在练习"
                :
                  "开始练习"
            }
          </button>

        </>
      )}

    </aside>
  );
}
