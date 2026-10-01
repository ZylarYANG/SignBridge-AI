import {
  MotionConfig,
} from "motion/react";

import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import {
  LearningShell,
} from "./components/learning/LearningShell";

import {
  LearnHome,
} from "./pages/learn/LearnHome";

import {
  SignLesson,
} from "./pages/learn/SignLesson";

import {
  PracticeStage,
} from "./pages/learn/PracticeStage";

import {
  LabWorkbench,
} from "./pages/lab/LabWorkbench";

import "./styles/learning-v6.css";

function App() {
  return (
    <BrowserRouter>
      <MotionConfig
        reducedMotion="user"
      >
        <Routes>
          <Route
            element={
              <LearningShell />
            }
          >
            <Route
              path="/"
              element={
                <Navigate
                  to="/learn"
                  replace
                />
              }
            />

            <Route
              path="/learn"
              element={
                <LearnHome />
              }
            />

            <Route
              path="/learn/:signId"
              element={
                <SignLesson />
              }
            />

            <Route
              path="/practice/:signId"
              element={
                <PracticeStage />
              }
            />

            <Route
              path="/lab"
              element={
                <LabWorkbench />
              }
            />

            <Route
              path="*"
              element={
                <Navigate
                  to="/learn"
                  replace
                />
              }
            />
          </Route>
        </Routes>
      </MotionConfig>
    </BrowserRouter>
  );
}

export default App;
