import {
  motion,
} from "motion/react";

import {
  Link,
} from "react-router-dom";

import type {
  CollectionSign,
} from "../../services/catalog";

import {
  PixelHandGlyph,
} from "./PixelHandGlyph";

type PixelLandmarkProps = {
  sign: CollectionSign;
  index: number;
  active: boolean;
  left: number;
  bottom: number;
};

const VARIANTS = [
  "gate",
  "tower",
  "terminal",
  "flag",
];

export function PixelLandmark({
  sign,
  index,
  active,
  left,
  bottom,
}: PixelLandmarkProps) {
  const variant =
    VARIANTS[
      index %
      VARIANTS.length
    ];

  return (
    <motion.div
      className={
        active
          ? "pq-landmark pq-landmark-active"
          : "pq-landmark"
      }
      style={{
        left: `${left}%`,
        bottom: `${bottom}%`,
      }}
      initial={{
        opacity: 0,
        y: 22,
      }}
      whileInView={{
        opacity: 1,
        y: 0,
      }}
      viewport={{
        once: true,
      }}
      transition={{
        delay:
          0.08 +
          index * 0.07,
        type: "spring",
        stiffness: 240,
        damping: 19,
      }}
    >
      {active && (
        <>
          <motion.div
            className="pq-landmark-beacon"
            animate={{
              opacity: [
                0.35,
                1,
                0.35,
              ],
              scaleY: [
                0.8,
                1.15,
                0.8,
              ],
            }}
            transition={{
              duration: 1.4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.div
            className="pq-landmark-floor-ring"
            animate={{
              scale: [
                0.9,
                1.35,
                0.9,
              ],
              opacity: [
                0.5,
                0,
                0.5,
              ],
            }}
            transition={{
              duration: 1.7,
              repeat: Infinity,
            }}
          />
        </>
      )}

      <Link
        to={
          `/learn/${
            encodeURIComponent(
              sign.signId
            )
          }`
        }
        className="pq-landmark-link"
        aria-label={
          `进入${sign.label}关卡`
        }
      >
        <motion.div
          className={
            `pq-landmark-structure pq-landmark-${variant}`
          }
          whileHover={{
            y: -8,
            scale: 1.04,
          }}
          whileTap={{
            y: 5,
            scale: 0.96,
          }}
        >
          <div className="pq-landmark-roof" />

          <div className="pq-landmark-screen">
            <PixelHandGlyph
              variant={index}
            />
          </div>

          <div className="pq-landmark-base" />

          <span className="pq-landmark-light" />
        </motion.div>
      </Link>

      <div className="pq-landmark-label">
        {sign.label}
      </div>
    </motion.div>
  );
}
