import {
  Link,
  useParams,
} from "react-router-dom";

import {
  motion,
} from "motion/react";

export function PracticeStage() {
  const {
    signId,
  } =
    useParams();

  return (
    <main className="pq-practice">
      <div className="pq-stage-progress">
        <Link
          className="pq-stage-close"
          to={
            signId
              ? `/learn/${
                  encodeURIComponent(
                    signId
                  )
                }`
              : "/learn"
          }
        >
          ×
        </Link>

        <div className="pq-stage-bars">
          <i />
          <motion.i
            initial={{
              scaleX: 0,
            }}
            animate={{
              scaleX: 1,
            }}
          />
          <i />
        </div>

        <strong>
          2/3
        </strong>
      </div>

      <section className="pq-practice-frame">
        <aside className="pq-practice-side">
          <span className="pq-pixel-tag">
            YOUR TURN
          </span>

          <h1>
            GO
          </h1>

          <div className="pq-practice-rules">
            <div>
              <span className="pq-rule-frame">
                <i />
              </span>

              <b>
                01
              </b>
            </div>

            <div>
              <span className="pq-rule-motion">
                <i />
                <i />
                <i />
              </span>

              <b>
                02
              </b>
            </div>
          </div>

          <Link
            className="pq-mini-lab"
            to="/lab"
          >
            LAB →
          </Link>
        </aside>

        <div className="pq-camera-room">
          <div className="pq-camera-grid" />

          <motion.div
            className="pq-camera-scan"
            animate={{
              y: [
                "-80%",
                "80%",
                "-80%",
              ],
            }}
            transition={{
              duration: 3.6,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.div
            className="pq-camera-target"
            animate={{
              boxShadow: [
                "0 0 0 0 rgba(140,255,47,.22)",
                "0 0 0 20px rgba(140,255,47,0)",
                "0 0 0 0 rgba(140,255,47,.22)",
              ],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
            }}
          >
            <span className="pq-camera-corner pq-camera-corner-a" />
            <span className="pq-camera-corner pq-camera-corner-b" />
            <span className="pq-camera-corner pq-camera-corner-c" />
            <span className="pq-camera-corner pq-camera-corner-d" />

            <div className="pq-camera-person">
              <span className="pq-camera-head" />
              <span className="pq-camera-body" />
              <span className="pq-camera-arm pq-camera-arm-left" />
              <span className="pq-camera-arm pq-camera-arm-right" />
            </div>
          </motion.div>

          <motion.div
            className="pq-camera-target-label"
            animate={{
              y: [
                0,
                -4,
                0,
              ],
            }}
            transition={{
              duration: 2.2,
              repeat: Infinity,
            }}
          >
            {
              signId ??
              "TARGET"
            }
          </motion.div>

          <div className="pq-camera-ready">
            <span />
          </div>
        </div>
      </section>
    </main>
  );
}
