import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  motion,
} from "motion/react";

import {
  fetchSignCatalog,
  type CollectionSign,
} from "../../services/catalog";

import {
  PixelHandGlyph,
} from "../../components/learning/PixelHandGlyph";

export function SignLesson() {
  const {
    signId,
  } =
    useParams();

  const [
    sign,
    setSign,
  ] =
    useState<CollectionSign | null>(
      null
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const catalog =
          await fetchSignCatalog();

        if (cancelled) {
          return;
        }

        setSign(
          catalog.signs.find(
            (item) =>
              item.signId ===
              signId
          ) ?? null
        );
      }
      finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [
    signId,
  ]);

  if (
    loading ||
    !sign
  ) {
    return (
      <main className="pq-state">
        <strong>
          {
            loading
              ? "..."
              : "?"
          }
        </strong>
      </main>
    );
  }

  const bothHands =
    sign.handednessPolicy ===
      "both_hands";

  return (
    <main className="pq-lesson">
      <div className="pq-stage-progress">
        <Link
          className="pq-stage-close"
          to="/learn"
        >
          ×
        </Link>

        <div className="pq-stage-bars">
          <motion.i
            initial={{
              scaleX: 0,
            }}
            animate={{
              scaleX: 1,
            }}
          />
          <i />
          <i />
        </div>

        <strong>
          1/3
        </strong>
      </div>

      <section className="pq-lesson-frame">
        <aside className="pq-lesson-side">
          <span className="pq-pixel-tag">
            LOOK
          </span>

          <motion.h1
            initial={{
              opacity: 0,
              x: -28,
            }}
            animate={{
              opacity: 1,
              x: 0,
            }}
          >
            {sign.label}
          </motion.h1>

          <div className="pq-lesson-icons">
            <span>
              {
                bothHands
                  ? "II"
                  : "I"
              }
            </span>

            {
              sign.directionSensitive &&
              (
                <span>
                  ↗
                </span>
              )
            }
          </div>

          <div className="pq-look-cue">
            <i />
            <i />
            <b>
              →
            </b>
          </div>
        </aside>

        <div className="pq-lesson-stage">
          <div className="pq-stage-sky">
            <span className="pq-stage-cloud pq-stage-cloud-a" />
            <span className="pq-stage-cloud pq-stage-cloud-b" />
          </div>

          <div className="pq-stage-platform" />

          <motion.div
            className="pq-demo-character"
            animate={{
              y: [
                0,
                -6,
                0,
              ],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <span className="pq-demo-head" />
            <span className="pq-demo-body" />

            <motion.span
              className="pq-demo-arm pq-demo-arm-left"
              animate={{
                rotate: [
                  -18,
                  -54,
                  -30,
                  -18,
                ],
              }}
              transition={{
                duration: 1.8,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

            <motion.span
              className="pq-demo-arm pq-demo-arm-right"
              animate={{
                rotate: [
                  18,
                  54,
                  30,
                  18,
                ],
              }}
              transition={{
                duration: 1.8,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

            <motion.span
              className="pq-demo-hand pq-demo-hand-left"
              animate={{
                x: [
                  0,
                  18,
                  6,
                  0,
                ],
                y: [
                  0,
                  -24,
                  -8,
                  0,
                ],
              }}
              transition={{
                duration: 1.8,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              <PixelHandGlyph
                variant={1}
              />
            </motion.span>

            <motion.span
              className="pq-demo-hand pq-demo-hand-right"
              animate={{
                x: [
                  0,
                  -18,
                  -6,
                  0,
                ],
                y: [
                  0,
                  -24,
                  -8,
                  0,
                ],
              }}
              transition={{
                duration: 1.8,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              <PixelHandGlyph
                variant={2}
              />
            </motion.span>
          </motion.div>

          <svg
            className="pq-demo-path"
            viewBox="0 0 640 420"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <motion.path
              d="
                M110 325
                C180 190 270 145 320 145
                C370 145 465 195 530 325
              "
              initial={{
                pathLength: 0,
              }}
              animate={{
                pathLength: 1,
                strokeDashoffset: [
                  0,
                  -96,
                ],
              }}
              transition={{
                pathLength: {
                  duration: 1.1,
                },
                strokeDashoffset: {
                  duration: 2.4,
                  repeat: Infinity,
                  ease: "linear",
                },
              }}
            />
          </svg>

          <motion.button
            type="button"
            className="pq-replay"
            whileTap={{
              y: 4,
            }}
            aria-label="重新播放"
          >
            ↻
          </motion.button>

          <Link
            className="pq-stage-next"
            to={
              `/practice/${
                encodeURIComponent(
                  sign.signId
                )
              }`
            }
            aria-label="开始练习"
          >
            <motion.span
              whileHover={{
                x: 6,
              }}
              whileTap={{
                y: 5,
              }}
            >
              ▶
            </motion.span>
          </Link>
        </div>
      </section>
    </main>
  );
}
