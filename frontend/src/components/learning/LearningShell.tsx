import {
  Link,
  Outlet,
  useLocation,
} from "react-router-dom";

import {
  motion,
} from "motion/react";

export function LearningShell() {
  const location = useLocation();

  const inLab =
    location.pathname.startsWith("/lab");

  const inLearn =
    location.pathname.startsWith("/learn") ||
    location.pathname.startsWith("/practice");

  return (
    <div
      className={
        inLab
          ? "pq-shell pq-shell-lab"
          : "pq-shell"
      }
    >
      <header
        className={
          inLearn
            ? "pq-hud"
            : "pq-hud pq-hud-muted"
        }
      >
        <Link
          className="pq-brand"
          to="/learn"
        >
          <motion.span
            className="pq-brand-chip"
            whileHover={{
              y: -2,
              rotate: -2,
            }}
            whileTap={{
              y: 3,
              scale: 0.96,
            }}
          >
            SB
          </motion.span>

          <span className="pq-brand-copy">
            <strong>
              SIGNBRIDGE
            </strong>

            <small>
              语桥智教
            </small>
          </span>
        </Link>

        {!inLab && (
          <div className="pq-hud-center">
            <div className="pq-hud-stat">
              <span>
                🔥
              </span>
              <b>
                1
              </b>
            </div>

            <div className="pq-hud-stat">
              <span>
                ★
              </span>
              <b>
                0
              </b>
            </div>

            <div className="pq-hud-stat pq-hud-stat-wide">
              <span>
                ⚡
              </span>
              <b>
                0/3
              </b>
            </div>
          </div>
        )}

        <Link
          className="pq-lab-link"
          to={
            inLab
              ? "/learn"
              : "/lab"
          }
        >
          {
            inLab
              ? "BACK"
              : "LAB"
          }
        </Link>
      </header>

      <Outlet />
    </div>
  );
}
