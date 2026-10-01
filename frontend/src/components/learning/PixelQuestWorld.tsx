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
  PixelCompanion,
} from "./PixelCompanion";

import {
  PixelLandmark,
} from "./PixelLandmark";

type PixelQuestWorldProps = {
  signs: CollectionSign[];
};

type SceneSpec = {
  id: string;
  className: string;
  number: string;
  title: string;
  signs: CollectionSign[];
  points: {
    left: number;
    bottom: number;
  }[];
};

const POINTS = [
  [
    { left: 19, bottom: 26 },
    { left: 41, bottom: 46 },
    { left: 65, bottom: 28 },
    { left: 84, bottom: 49 },
  ],
  [
    { left: 15, bottom: 43 },
    { left: 37, bottom: 24 },
    { left: 63, bottom: 50 },
    { left: 84, bottom: 30 },
  ],
  [
    { left: 16, bottom: 25 },
    { left: 39, bottom: 53 },
    { left: 64, bottom: 31 },
    { left: 84, bottom: 55 },
  ],
];

export function PixelQuestWorld({
  signs,
}: PixelQuestWorldProps) {
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
    useMemo<SceneSpec[]>(
      () => [
        {
          id: "pq-world-01",
          className:
            "pq-scene-meadow",
          number: "01",
          title: "常用表达",
          signs:
            signs.slice(0, 4),
          points:
            POINTS[0],
        },
        {
          id: "pq-world-02",
          className:
            "pq-scene-town",
          number: "02",
          title: "日常交流",
          signs:
            signs.slice(4, 8),
          points:
            POINTS[1],
        },
        {
          id: "pq-world-03",
          className:
            "pq-scene-night",
          number: "03",
          title: "星光挑战",
          signs:
            signs.slice(8, 12),
          points:
            POINTS[2],
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
      behavior: "smooth",
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

    function updateScene() {
      const width =
        Math.max(
          scrollerElement.clientWidth,
          1
        );

      setSceneIndex(
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

    function handleWheel(
      event: WheelEvent
    ) {
      if (
        Math.abs(event.deltaY) <=
        Math.abs(event.deltaX)
      ) {
        return;
      }

      event.preventDefault();

      scrollerElement.scrollBy({
        left: event.deltaY * 1.35,
        behavior: "auto",
      });
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

    scrollerElement.addEventListener(
      "scroll",
      updateScene,
      {
        passive: true,
      }
    );

    scrollerElement.addEventListener(
      "wheel",
      handleWheel,
      {
        passive: false,
      }
    );

    window.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      scrollerElement.removeEventListener(
        "scroll",
        updateScene
      );

      scrollerElement.removeEventListener(
        "wheel",
        handleWheel
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
    <main className="pq-world">
      <div
        className="pq-world-scroller"
        ref={scrollerRef}
      >
        {scenes.map(
          (
            scene,
            worldIndex
          ) => (
            <section
              className={
                `pq-scene ${
                  scene.className
                }`
              }
              key={scene.id}
            >
              <div className="pq-pixel-sky">

                <div className="pq-cloud pq-cloud-a" />
                <div className="pq-cloud pq-cloud-b" />
                <div className="pq-cloud pq-cloud-c" />

                <div className="pq-mountain pq-mountain-a" />
                <div className="pq-mountain pq-mountain-b" />
                <div className="pq-mountain pq-mountain-c" />

                <div className="pq-distant-city">
                  {Array.from({
                    length: 9,
                  }).map(
                    (
                      _,
                      index
                    ) => (
                      <span
                        key={index}
                        style={{
                          height:
                            `${34 + (index % 4) * 14}px`,
                        }}
                      />
                    )
                  )}
                </div>
              </div>

              <div className="pq-world-title">
                <small>
                  WORLD
                </small>

                <strong>
                  {scene.number}
                </strong>

                <span>
                  {scene.title}
                </span>
              </div>

              <div className="pq-world-track">

                <svg
                  className="pq-route"
                  viewBox="0 0 1000 540"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <path
                    className="pq-route-shadow"
                    d="
                      M35 420
                      C150 410 195 260 335 260
                      C485 260 465 440 620 430
                      C760 420 770 255 965 230
                    "
                  />

                  <path
                    className="pq-route-floor"
                    d="
                      M35 420
                      C150 410 195 260 335 260
                      C485 260 465 440 620 430
                      C760 420 770 255 965 230
                    "
                  />

                  <path
                    className="pq-route-light"
                    d="
                      M35 420
                      C150 410 195 260 335 260
                      C485 260 465 440 620 430
                      C760 420 770 255 965 230
                    "
                  >
                    <animate
                      attributeName="stroke-dashoffset"
                      from="0"
                      to="-128"
                      dur="3.2s"
                      repeatCount="indefinite"
                    />
                  </path>
                </svg>

                <div className="pq-grass pq-grass-back" />
                <div className="pq-grass pq-grass-mid" />
                <div className="pq-grass pq-grass-front" />

                {scene.signs.map(
                  (
                    sign,
                    index
                  ) => {
                    const point =
                      scene.points[index];

                    return (
                      <PixelLandmark
                        key={sign.signId}
                        sign={sign}
                        index={
                          worldIndex *
                          4 +
                          index
                        }
                        active={
                          worldIndex === 0 &&
                          index === 0
                        }
                        left={point.left}
                        bottom={point.bottom}
                      />
                    );
                  }
                )}

                {worldIndex === 0 && (
                  <div className="pq-companion-slot">
                    <PixelCompanion />
                  </div>
                )}

                <button
                  type="button"
                  className="pq-scene-gate"
                  onClick={() =>
                    goToScene(
                      worldIndex ===
                        scenes.length - 1
                        ? 0
                        : worldIndex + 1
                    )
                  }
                  aria-label={
                    worldIndex ===
                      scenes.length - 1
                      ? "返回第一世界"
                      : "前往下一世界"
                  }
                >
                  <span className="pq-gate-tower pq-gate-tower-left" />
                  <span className="pq-gate-tower pq-gate-tower-right" />

                  <span className="pq-gate-top" />

                  <span className="pq-gate-light">
                    {
                      worldIndex ===
                        scenes.length - 1
                        ? "★"
                        : "→"
                    }
                  </span>
                </button>
              </div>

              <div className="pq-foreground-block pq-foreground-block-a" />
              <div className="pq-foreground-block pq-foreground-block-b" />
              <div className="pq-foreground-block pq-foreground-block-c" />
            </section>
          )
        )}
      </div>

      <div className="pq-world-dots">
        {scenes.map(
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
                  ? "pq-world-dot pq-world-dot-active"
                  : "pq-world-dot"
              }
              onClick={() =>
                goToScene(index)
              }
              aria-label={
                `世界${index + 1}`
              }
            />
          )
        )}
      </div>

      <div className="pq-world-keyhint">
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
