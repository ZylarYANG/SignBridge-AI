import { CameraView } from "./components/CameraView";

function App() {
  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <span className="eyebrow">
            AI Chinese Sign Language Tutor
          </span>

          <h1>SignBridge AI · 语桥智教</h1>

          <p>
            Day 1 · Camera → MediaPipe → Landmark
          </p>
        </div>
      </header>

      <section className="workspace">
        <CameraView />

        <aside className="practice-panel">
          <span className="panel-label">
            当前练习
          </span>

          <h2>谢谢</h2>

          <code>CSL_THANKS</code>

          <div className="metric">
            <span>系统阶段</span>
            <strong>Camera Test</strong>
          </div>

          <div className="metric">
            <span>Landmark</span>
            <strong>等待接入</strong>
          </div>

          <button disabled>
            开始练习
          </button>

          <p className="hint">
            当前只验证浏览器摄像头。下一步接入
            MediaPipe Pose + Hands。
          </p>
        </aside>
      </section>
    </main>
  );
}

export default App;
