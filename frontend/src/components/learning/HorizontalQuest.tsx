import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  motion,
} from "motion/react";

import type {
  CollectionSign,
} from "../../services/catalog";

import {
  ShaderField,
} from "./ShaderField";

type HorizontalQuestProps = {
  signs: CollectionSign[];
};

type Scene = {
  id: string;
  eyebrow: string;
  title: string;
  subtitle: string;
  className: string;
  signs: CollectionSign[];
};

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

const NODE_POSITIONS = [
  {
    left: 12,
    bottom: 23,
  },
  {
    left: 35,
    bottom: 41,
  },
  {
    left: 61,
    bottom: 25,
  },
  {
    left: 84,
    bottom: 45,
  },
];

export function HorizontalQuest({
  signs,
}: HorizontalQuestProps) {
  const scrollerRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const [
    sceneIndex,
    setSceneIndex,
  ] =
    useState(0);

  const scenes =
    useMemo<Scene[]>(
      () => [
        {
          id: "world-01",
          eyebrow:
            "WORLD 01 · 常用表达",
          title:
            "从第一座桥出发",
          subtitle:
            "先掌握最常见的动作，用四个小关卡建立手语节奏感。",
          className:
            "quest-scene-green",
          signs:
            signs.slice(
              0,
              4
            ),
        },
        {
          id: "world-02",
          eyebrow:
            "WORLD 02 · 日常交流",
          title:
            "穿过彩色云谷",
          subtitle:
            "动作开始变得更丰富，留意双手配合与运动方向。",
          className:
            "quest-scene-blue",
          signs:
            signs.slice(
              4,
              8
            ),
        },
        {
          id: "world-03",
          eyebrow:
            "WORLD 03 · 挑战区",
          title:
            "抵达星光终点",
          subtitle:
            "把最后几组动作练稳，完成今天的手语冒险。",
          className:
            "quest-scene-purple",
          signs:
            signs.slice(
              8,
              12
            ),
        },
      ],
      [signs]
    );

  function goToScene(
    index: number
  ) {
    const scroller =
      scrollerRef.current;

    if (!scroller) {
      return;
    }

    const safeIndex =
      Math.max(
        0,
        Math.min(
          scenes.length - 1,
          index
        )
      );

    scroller.scrollTo({
      left:
        safeIndex *
        scroller.clientWidth,
      behavior:
        "smooth",
    });
  }

  useEffect(() => {
    const scroller =
      scrollerRef.current;

    if (!scroller) {
      return;
    }

    function handleScroll() {
      const current =
        scrollerRef.current;

      if (!current) {
        return;
      }

      const width =
        Math.max(
          current.clientWidth,
          1
        );

      const nextIndex =
        Math.round(
          current.scrollLeft /
          width
        );

      setSceneIndex(
        Math.max(
          0,
          Math.min(
            scenes.length - 1,
            nextIndex
          )
        )
      );
    }

    function handleKeyDown(
      event: KeyboardEvent
    ) {
      if (
        event.key ===
        "ArrowRight"
      ) {
        event.preventDefault();

        goToScene(
          sceneIndex + 1
        );
      }

      if (
        event.key ===
        "ArrowLeft"
      ) {
        event.preventDefault();

        goToScene(
          sceneIndex - 1
        );
      }
    }

    scroller.addEventListener(
      "scroll",
      handleScroll,
      {
        passive: true,
      }
    );

    window.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      scroller.removeEventListener(
        "scroll",
        handleScroll
      );

      window.removeEventListener(
        "keydown",
        handleKeyDown
      );
    };
  }, [
    sceneIndex,
    scenes.length,
  ]);

  return (
    <section className="horizontal-quest">
      <div
        className="quest-progress-rail"
        aria-label="世界进度"
      >
        {
          scenes.map(
            (
              scene,
              index
            ) => (
              <button
                key={scene.id}
                type="button"
                className={
                  index ===
                    sceneIndex
                    ? "quest-progress-dot quest-progress-dot-active"
                    : "quest-progress-dot"
                }
                onClick={() =>
                  goToScene(
                    index
                  )
                }
                aria-label={
                  `前往第 ${
                    index + 1
                  } 个世界`
                }
              />
            )
          )
        }
      </div>

      <div
        className="quest-scroller"
        ref={scrollerRef}
      >
        {
          scenes.map(
            (
              scene,
              sceneNumber
            ) => {
              const firstActive =
                sceneNumber === 0;

              return (
                <article
                  key={scene.id}
                  className={
                    `quest-scene ${
                      scene.className
                    }`
                  }
                >
                  <ShaderField
                    className="quest-scene-shader"
                  />

                  <div className="quest-sky-grid" />

                  <motion.div
                    className="quest-cloud quest-cloud-a"
                    animate={{
                      x: [
                        0,
                        28,
                        0,
                      ],
                      y: [
                        0,
                        -8,
                        0,
                      ],
                    }}
                    transition={{
                      duration: 8,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  />

                  <motion.div
                    className="quest-cloud quest-cloud-b"
                    animate={{
                      x: [
                        0,
                        -24,
                        0,
                      ],
                    }}
                    transition={{
                      duration: 10,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  />

                  <div className="quest-scene-copy">
                    <motion.span
                      className="quest-world-tag"
                      initial={{
                        opacity: 0,
                        y: 14,
                        rotate: -4,
                      }}
                      whileInView={{
                        opacity: 1,
                        y: 0,
                        rotate: -2,
                      }}
                      viewport={{
                        once: true,
                      }}
                    >
                      {
                        scene.eyebrow
                      }
                    </motion.span>

                    <motion.h1
                      initial={{
                        opacity: 0,
                        x: -32,
                      }}
                      whileInView={{
                        opacity: 1,
                        x: 0,
                      }}
                      viewport={{
                        once: true,
                      }}
                      transition={{
                        type: "spring",
                        stiffness: 170,
                        damping: 20,
                      }}
                    >
                      {
                        scene.title
                      }
                    </motion.h1>

                    <motion.p
                      initial={{
                        opacity: 0,
                        y: 15,
                      }}
                      whileInView={{
                        opacity: 1,
                        y: 0,
                      }}
                      viewport={{
                        once: true,
                      }}
                      transition={{
                        delay: 0.08,
                      }}
                    >
                      {
                        scene.subtitle
                      }
                    </motion.p>
                  </div>

                  <div className="quest-ground-back" />
                  <div className="quest-ground-mid" />
                  <div className="quest-ground-front" />

                  <svg
                    className="quest-route"
                    viewBox="0 0 1000 520"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                  >
                    <motion.path
                      className="quest-route-shadow"
                      d="
                        M70 385
                        C180 350 245 245 350 250
                        C455 255 485 385 610 388
                        C735 390 765 245 930 230
                      "
                    />

                    <motion.path
                      className="quest-route-main"
                      d="
                        M70 385
                        C180 350 245 245 350 250
                        C455 255 485 385 610 388
                        C735 390 765 245 930 230
                      "
                      initial={{
                        pathLength: 0,
                      }}
                      whileInView={{
                        pathLength: 1,
                      }}
                      viewport={{
                        once: true,
                        amount: 0.35,
                      }}
                      transition={{
                        duration: 1.2,
                        ease: "easeOut",
                      }}
                    />

                    <motion.path
                      className="quest-route-energy"
                      d="
                        M70 385
                        C180 350 245 245 350 250
                        C455 255 485 385 610 388
                        C735 390 765 245 930 230
                      "
                      animate={{
                        strokeDashoffset: [
                          0,
                          -150,
                        ],
                      }}
                      transition={{
                        duration: 3.5,
                        repeat: Infinity,
                        ease: "linear",
                      }}
                    />
                  </svg>

                  {
                    scene.signs.map(
                      (
                        sign,
                        nodeIndex
                      ) => {
                        const position =
                          NODE_POSITIONS[
                            nodeIndex %
                            NODE_POSITIONS.length
                          ];

                        const globalIndex =
                          sceneNumber *
                          4 +
                          nodeIndex;

                        const active =
                          firstActive &&
                          nodeIndex === 0;

                        return (
                          <motion.div
                            key={
                              sign.signId
                            }
                            className={
                              active
                                ? "quest-level quest-level-active"
                                : "quest-level"
                            }
                            style={{
                              left:
                                `${
                                  position.left
                                }%`,
                              bottom:
                                `${
                                  position.bottom
                                }%`,
                            }}
                            initial={{
                              opacity: 0,
                              scale: 0.78,
                              y: 30,
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
                                0.14 +
                                nodeIndex *
                                0.08,
                              type: "spring",
                              stiffness: 250,
                              damping: 18,
                            }}
                          >
                            {
                              active &&
                              (
                                <motion.div
                                  className="quest-level-start"
                                  animate={{
                                    y: [
                                      0,
                                      -6,
                                      0,
                                    ],
                                  }}
                                  transition={{
                                    duration: 1.8,
                                    repeat: Infinity,
                                    ease: "easeInOut",
                                  }}
                                >
                                  从这里开始
                                </motion.div>
                              )
                            }

                            <Link
                              to={
                                `/learn/${
                                  encodeURIComponent(
                                    sign.signId
                                  )
                                }`
                              }
                              className="quest-level-link"
                            >
                              <motion.div
                                className={
                                  `quest-level-button quest-level-button-${
                                    globalIndex %
                                    4
                                  }`
                                }
                                whileHover={{
                                  y: -10,
                                  scale: 1.1,
                                  rotate:
                                    globalIndex %
                                    2 === 0
                                      ? -3
                                      : 3,
                                }}
                                whileTap={{
                                  y: 7,
                                  scale: 0.92,
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
                                        stiffness: 330,
                                        damping: 17,
                                      }
                                }
                              >
                                <span className="quest-level-shine" />

                                <span className="quest-level-icon">
                                  {
                                    ICONS[
                                      globalIndex %
                                      ICONS.length
                                    ]
                                  }
                                </span>
                              </motion.div>
                            </Link>

                            <div className="quest-level-copy">
                              <strong>
                                {
                                  sign.label
                                }
                              </strong>

                              <small>
                                {
                                  active
                                    ? "第一关"
                                    : "点击挑战"
                                }
                              </small>
                            </div>
                          </motion.div>
                        );
                      }
                    )
                  }

                  <motion.div
                    className="quest-mascot"
                    animate={{
                      y: [
                        0,
                        -9,
                        0,
                      ],
                      rotate: [
                        -2,
                        2,
                        -2,
                      ],
                    }}
                    transition={{
                      duration: 2.6,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  >
                    <span className="quest-mascot-eye quest-mascot-eye-left" />
                    <span className="quest-mascot-eye quest-mascot-eye-right" />
                    <span className="quest-mascot-mouth" />

                    <motion.span
                      className="quest-mascot-hand"
                      animate={{
                        rotate: [
                          0,
                          20,
                          -9,
                          20,
                          0,
                        ],
                      }}
                      transition={{
                        duration: 1.6,
                        repeat: Infinity,
                        repeatDelay: 2,
                      }}
                    >
                      👋
                    </motion.span>
                  </motion.div>

                  <motion.div
                    className="quest-side-tip"
                    initial={{
                      opacity: 0,
                      x: 30,
                      rotate: 3,
                    }}
                    whileInView={{
                      opacity: 1,
                      x: 0,
                      rotate: 2,
                    }}
                    viewport={{
                      once: true,
                    }}
                  >
                    <span>
                      GAME TIP
                    </span>

                    <strong>
                      {
                        sceneNumber === 0
                          ? "每关只有 3 步"
                          : sceneNumber === 1
                            ? "注意动作方向"
                            : "最后一段，稳住节奏"
                      }
                    </strong>

                    <p>
                      看动作 → 跟着做 → 看反馈。
                    </p>
                  </motion.div>

                  <motion.div
                    className="quest-finish-portal"
                    animate={{
                      rotate: [
                        0,
                        360,
                      ],
                    }}
                    transition={{
                      duration: 18,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                  >
                    <i />
                    <i />
                    <i />
                    <span>✦</span>
                  </motion.div>

                  {
                    sceneNumber <
                    scenes.length - 1 && (
                      <button
                        type="button"
                        className="quest-next-scene"
                        onClick={() =>
                          goToScene(
                            sceneNumber + 1
                          )
                        }
                      >
                        <span>
                          下一地图
                        </span>
                        <b>→</b>
                      </button>
                    )
                  }

                  {
                    sceneNumber >
                    0 && (
                      <button
                        type="button"
                        className="quest-prev-scene"
                        onClick={() =>
                          goToScene(
                            sceneNumber - 1
                          )
                        }
                      >
                        ←
                      </button>
                    )
                  }
                </article>
              );
            }
          )
        }
      </div>

      <div className="quest-bottom-help">
        <span>← →</span>

        <p>
          使用左右方向键，
          或拖动页面探索地图
        </p>
      </div>
    </section>
  );
}
