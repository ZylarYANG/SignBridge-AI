import {
  CameraView,
} from "../../components/CameraView";

export function LabWorkbench() {
  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <span className="eyebrow">
            SignBridge Research Workbench
          </span>

          <h1>
            研发工作台
          </h1>

          <p>
            数据采集 · MediaPipe ·
            Recognition · Assessment
          </p>
        </div>
      </header>

      <section className="workspace">
        <CameraView />
      </section>
    </main>
  );
}
