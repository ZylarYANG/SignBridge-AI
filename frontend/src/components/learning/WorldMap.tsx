import {
  motion,
} from "motion/react";

import {
  Link,
} from "react-router-dom";

import type {
  CollectionSign,
} from "../../services/catalog";

type WorldMapProps = {
  signs: CollectionSign[];
  theme:
    | "lime"
    | "violet";
  activeFirst?: boolean;
  startIndex?: number;
};

const POSITIONS = [
  { x: 48, y: 11 },
  { x: 70, y: 27 },
  { x: 46, y: 42 },
  { x: 24, y: 57 },
  { x: 49, y: 72 },
  { x: 73, y: 87 },
];

const ICONS = [
  "👋",
  "🤟",
  "🤝",
  "👍",
  "💬",
  "✨",
  "🫶",
  "🙌",
  "👌",
  "🖐️",
  "💡",
  "🌟",
];

export function WorldMap({
  signs,
  theme,
  activeFirst = false,
  startIndex = 0,
}: WorldMapProps) {
  return (
    <div
      className={
        `world-map world-map-${theme}`
      }
    >
      <motion.div
        className="world-orb world-orb-a"
        animate={{
          x: [0, 16, 0],
          y: [0, -13, 0],
          rotate: [0, 7, 0],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <motion.div
        className="world-orb world-orb-b"
        animate={{
          x: [0, -10, 0],
          y: [0, 12, 0],
          rotate: [0, -9, 0],
        }}
        transition={{
          duration: 7,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <svg
        className="world-route"
        viewBox="0 0 760 720"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <motion.path
          d="
            M365 78
            C500 115 565 155 540 215
            C520 265 395 285 350 325
            C300 370 205 390 190 445
            C175 505 295 530 365 560
            C450 595 565 610 555 675
          "
          className="world-route-shadow"
        />

        <motion.path
          d="
            M365 78
            C500 115 565 155 540 215
            C520 265 395 285 350 325
            C300 370 205 390 190 445
            C175 505 295 530 365 560
            C450 595 565 610 555 675
          "
          className="world-route-line"
          initial={{
            pathLength: 0,
          }}
          whileInView={{
            pathLength: 1,
          }}
          viewport={{
            once: true,
            amount: 0.25,
          }}
          transition={{
            duration: 1.4,
            ease: "easeOut",
          }}
        />

        <motion.path
          d="
            M365 78
            C500 115 565 155 540 215
            C520 265 395 285 350 325
            C300 370 205 390 190 445
            C175 505 295 530 365 560
            C450 595 565 610 555 675
          "
          className="world-route-energy"
          animate={{
            strokeDashoffset: [
              0,
              -160,
            ],
          }}
          transition={{
            duration: 3.8,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      </svg>


      {signs.map(
        (
          sign,
          index
        ) => {
          const position =
            POSITIONS[
              index %
              POSITIONS.length
            ];

          const active =
            activeFirst &&
            index === 0;

          const globalIndex =
            startIndex +
            index;

          return (
            <motion.div
              key={
                sign.signId
              }
              className={
                active
                  ? "world-node-wrap world-node-wrap-active"
                  : "world-node-wrap"
              }
              style={{
                left:
                  `${position.x}%`,
                top:
                  `${position.y}%`,
              }}
              initial={{
                opacity: 0,
                scale: 0.72,
                y: 24,
              }}
              whileInView={{
                opacity: 1,
                scale: 1,
                y: 0,
              }}
              viewport={{
                once: true,
              }}
              transition={{
                delay:
                  index * 0.07,
                type: "spring",
                stiffness: 250,
                damping: 18,
              }}
            >
              {active && (
                <motion.div
                  className="world-start-label"
                  animate={{
                    y: [0, -5, 0],
                  }}
                  transition={{
                    duration: 1.9,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                >
                  START
                </motion.div>
              )}

              <Link
                to={
                  `/learn/${encodeURIComponent(
                    sign.signId
                  )}`
                }
                className="world-node-link"
              >
                <motion.div
                  className={
                    `world-node world-node-${globalIndex % 4}`
                  }
                  whileHover={{
                    scale: 1.12,
                    rotate:
                      globalIndex %
                      2 === 0
                        ? 4
                        : -4,
                    y: -8,
                  }}
                  whileTap={{
                    scale: 0.9,
                    y: 7,
                  }}
                  animate={
                    active
                      ? {
                          y: [
                            0,
                            -7,
                            0,
                          ],
                        }
                      : undefined
                  }
                  transition={
                    active
                      ? {
                          duration: 2,
                          repeat: Infinity,
                          ease: "easeInOut",
                        }
                      : {
                          type: "spring",
                          stiffness: 320,
                          damping: 18,
                        }
                  }
                >
                  <span className="world-node-gloss" />

                  <span className="world-node-icon">
                    {
                      ICONS[
                        globalIndex %
                        ICONS.length
                      ]
                    }
                  </span>
                </motion.div>
              </Link>

              <div className="world-node-copy">
                <strong>
                  {sign.label}
                </strong>

                <small>
                  {
                    active
                      ? "开始这一关"
                      : "点击挑战"
                  }
                </small>
              </div>
            </motion.div>
          );
        }
      )}


      <motion.div
        className="world-comet"
        animate={{
          x: [
            -10,
            12,
            -10,
          ],
          y: [
            0,
            -18,
            0,
          ],
          rotate: [
            -12,
            8,
            -12,
          ],
        }}
        transition={{
          duration: 5.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        ✦
      </motion.div>
    </div>
  );
}
