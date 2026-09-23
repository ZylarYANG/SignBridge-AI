import { CameraView } from "./components/CameraView";
import { WorkbenchStatusPanel } from "./components/WorkbenchStatusPanel";


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

        <WorkbenchStatusPanel />
      </section>
    </main>
  );
}

export default App;
