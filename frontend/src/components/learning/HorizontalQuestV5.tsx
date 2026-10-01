import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import type {
  CollectionSign,
} from "../../services/catalog";

import {
  ShaderField,
} from "./ShaderField";

import {
  CompanionV5,
} from "./CompanionV5";

import {
  PortalGateV5,
} from "./PortalGateV5";

import {
  QuestLevelNodeV5,
} from "./QuestLevelNodeV5";


type HorizontalQuestV5Props = {
  signs: CollectionSign[];
};


type SceneSpec = {
  id: string;
  className: string;
  worldNo: string;
  title: string;
  accent: string;
  signs: CollectionSign[];
  positions: {
    left: number;
    bottom: number;
    tilt: number;
  }[];
};


const SCENE_POSITIONS = [
  [
    {
      left: 16,
      bottom: 23,
      tilt: -5,
    },
    {
      left: 39,
      bottom: 50,
      tilt: 7,
    },
    {
      left: 64,
      bottom: 27,
      tilt: -3,
    },
    {
      left: 84,
      bottom: 55,
      tilt: 4,
    },
  ],

  [
    {
      left: 14,
      bottom: 45,
      tilt: 6,
    },
    {
      left: 36,
      bottom: 22,
      tilt: -4,
    },
    {
      left: 61,
      bottom: 54,
      tilt: 5,
    },
    {
      left: 84,
      bottom: 29,
      tilt: -7,
    },
  ],

  [
    {
      left: 13,
      bottom: 27,
      tilt: -6,
    },
    {
      left: 36,
      bottom: 59,
      tilt: 3,
    },
    {
      left: 62,
      bottom: 31,
      tilt: -4,
    },
    {
      left: 84,
      bottom: 61,
      tilt: 7,
    },
  ],
];


export function HorizontalQuestV5({
  signs,
}: HorizontalQuestV5Props) {
  const scrollerRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const [
    activeScene,
    setActiveScene,
  ] =
    useState(0);


  const scenes =
    useMemo<SceneSpec[]>(
      () => [
        {
          id:
            "v5-world-01",
          className:
            "v5-scene-world-1",
          worldNo:
            "01",
          title:
            "常用表达",
          accent:
            "START",
          signs:
            signs.slice(
              0,
              4
            ),
          positions:
            SCENE_POSITIONS[0],
        },

        {
          id:
            "v5-world-02",
          className:
            "v5-scene-world-2",
          worldNo:
            "02",
          title:
            "日常交流",
          accent:
            "FLOW",
          signs:
            signs.slice(
              4,
              8
            ),
          positions:
            SCENE_POSITIONS[1],
        },

        {
          id:
            "v5-world-03",
          className:
            "v5-scene-world-3",
          worldNo:
            "03",
          title:
            "星光挑战",
          accent:
            "FINAL",
          signs:
            signs.slice(
              8,
              12
            ),
          positions:
            SCENE_POSITIONS[2],
        },
      ],
      [
        signs,
      ]
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

    const scrollerElement =
      scroller;


    function updateActiveScene() {
      const width =
        Math.max(
          scrollerElement.clientWidth,
          1
        );

      setActiveScene(
        Math.max(
          0,
          Math.min(
            scenes.length - 1,
            Math.round(
              scrollerElement.scrollLeft /
              width
            )
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
          activeScene + 1
        );
      }

      if (
        event.key ===
        "ArrowLeft"
      ) {
        event.preventDefault();

        goToScene(
          activeScene - 1
        );
      }
    }


    scrollerElement.addEventListener(
      "scroll",
      updateActiveScene,
      {
        passive: true,
      }
    );

    window.addEventListener(
      "keydown",
      handleKeyDown
    );


    return () => {
      scrollerElement.removeEventListener(
        "scroll",
        updateActiveScene
      );

      window.removeEventListener(
        "keydown",
        handleKeyDown
      );
    };
  }, [
    activeScene,
    scenes.length,
  ]);


  return (
    <main className="v5-world-root">

      <div
        className="v5-world-scroller"
        ref={scrollerRef}
      >
        {
          scenes.map(
            (
              scene,
              sceneIndex
            ) => (
              <section
                className={
                  `v5-scene ${
                    scene.className
                  }`
                }
                key={scene.id}
              >
                <ShaderField
                  className="v5-scene-shader"
                />


                <div className="v5-scene-backdrop">

                  <div className="v5-back-sun" />

                  <div className="v5-back-arc v5-back-arc-a" />

                  <div className="v5-back-arc v5-back-arc-b" />

                  <div className="v5-back-block v5-back-block-a" />

                  <div className="v5-back-block v5-back-block-b" />

                  <div className="v5-back-haze" />

                </div>


                <div className="v5-scene-title">
                  <span>
                    {
                      scene.accent
                    }
                  </span>

                  <strong>
                    {
                      scene.worldNo
                    }
                  </strong>

                  <h1>
                    {
                      scene.title
                    }
                  </h1>
                </div>


                <div className="v5-parallax-layer v5-parallax-back">

                  <div className="v5-back-island v5-back-island-a" />

                  <div className="v5-back-island v5-back-island-b" />

                  <div className="v5-back-island v5-back-island-c" />

                </div>


                <div className="v5-track-shell">

                  <svg
                    className="v5-track-svg"
                    viewBox="0 0 1000 620"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                  >
                    <path
                      className="v5-track-shadow"
                      d="
                        M60 450
                        C150 405 190 245 340 250
                        C475 255 465 470 610 455
                        C740 440 760 245 950 220
                      "
                    />

                    <path
                      className="v5-track-base"
                      d="
                        M60 450
                        C150 405 190 245 340 250
                        C475 255 465 470 610 455
                        C740 440 760 245 950 220
                      "
                    />

                    <path
                      className="v5-track-energy"
                      d="
                        M60 450
                        C150 405 190 245 340 250
                        C475 255 465 470 610 455
                        C740 440 760 245 950 220
                      "
                    >
                      <animate
                        attributeName="stroke-dashoffset"
                        from="0"
                        to="-180"
                        dur="4s"
                        repeatCount="indefinite"
                      />
                    </path>
                  </svg>


                  <div className="v5-ground v5-ground-far" />

                  <div className="v5-ground v5-ground-mid" />

                  <div className="v5-ground v5-ground-near" />


                  {
                    scene.signs.map(
                      (
                        sign,
                        index
                      ) => {
                        const position =
                          scene.positions[
                            index
                          ];

                        return (
                          <QuestLevelNodeV5
                            key={
                              sign.signId
                            }
                            sign={
                              sign
                            }
                            index={
                              sceneIndex *
                              4 +
                              index
                            }
                            active={
                              sceneIndex ===
                                0 &&
                              index ===
                                0
                            }
                            left={
                              position.left
                            }
                            bottom={
                              position.bottom
                            }
                            tilt={
                              position.tilt
                            }
                          />
                        );
                      }
                    )
                  }


                  {
                    sceneIndex ===
                      0 && (
                      <div className="v5-companion-slot">
                        <CompanionV5 />
                      </div>
                    )
                  }


                  <div className="v5-scene-mark v5-scene-mark-a" />

                  <div className="v5-scene-mark v5-scene-mark-b" />

                  <div className="v5-scene-mark v5-scene-mark-c" />


                  <div className="v5-scene-portal-next">
                    {
                      sceneIndex <
                        scenes.length -
                          1 ? (
                        <PortalGateV5
                          onActivate={() =>
                            goToScene(
                              sceneIndex +
                                1
                            )
                          }
                        />
                      ) : (
                        <div className="v5-final-crown">
                          <span>
                            ★
                          </span>

                          <i />
                          <i />
                          <i />
                        </div>
                      )
                    }
                  </div>


                  {
                    sceneIndex >
                      0 && (
                      <div className="v5-scene-portal-prev">
                        <PortalGateV5
                          reverse
                          onActivate={() =>
                            goToScene(
                              sceneIndex -
                                1
                            )
                          }
                        />
                      </div>
                    )
                  }

                </div>


                <div className="v5-foreground-strip">
                  <div className="v5-foreground-shape v5-foreground-shape-a" />
                  <div className="v5-foreground-shape v5-foreground-shape-b" />
                  <div className="v5-foreground-shape v5-foreground-shape-c" />
                </div>

              </section>
            )
          )
        }
      </div>


      <div className="v5-world-indicator">
        {
          scenes.map(
            (
              scene,
              index
            ) => (
              <button
                key={
                  scene.id
                }
                type="button"
                className={
                  index ===
                    activeScene
                    ? "v5-world-dot v5-world-dot-active"
                    : "v5-world-dot"
                }
                onClick={() =>
                  goToScene(
                    index
                  )
                }
                aria-label={
                  `切换到世界 ${
                    index + 1
                  }`
                }
              />
            )
          )
        }
      </div>


      <div className="v5-world-gesture-hint">
        <span>
          ←
        </span>

        <i />

        <span>
          →
        </span>
      </div>

    </main>
  );
}
