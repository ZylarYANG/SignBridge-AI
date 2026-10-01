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
  GestureGlyph,
} from "./GestureGlyph";

type QuestLevelNodeV5Props = {
  sign: CollectionSign;
  index: number;
  active: boolean;
  left: number;
  bottom: number;
  tilt: number;
};

export function QuestLevelNodeV5({
  sign,
  index,
  active,
  left,
  bottom,
  tilt,
}: QuestLevelNodeV5Props) {
  return (
    <motion.div
      className={
        active
          ? "v5-level v5-level-active"
          : "v5-level"
      }
      style={{
        left: `${left}%`,
        bottom: `${bottom}%`,
      }}
      initial={{
        opacity: 0,
        y: 42,
        scale: 0.75,
        rotate: tilt,
      }}
      whileInView={{
        opacity: 1,
        y: 0,
        scale: 1,
        rotate: tilt,
      }}
      viewport={{
        once: true,
        amount: 0.4,
      }}
      transition={{
        delay:
          0.08 +
          index * 0.08,
        type: "spring",
        stiffness: 220,
        damping: 17,
      }}
    >
      {active && (
        <>
          <motion.span
            className="v5-level-beacon"
            animate={{
              y: [
                -3,
                -14,
                -3,
              ],
              opacity: [
                0.6,
                1,
                0.6,
              ],
            }}
            transition={{
              duration: 1.45,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.span
            className="v5-level-pulse v5-level-pulse-a"
            animate={{
              scale: [
                0.75,
                1.35,
                0.75,
              ],
              opacity: [
                0.6,
                0,
                0.6,
              ],
            }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />

          <motion.span
            className="v5-level-pulse v5-level-pulse-b"
            animate={{
              scale: [
                0.8,
                1.6,
                0.8,
              ],
              opacity: [
                0.35,
                0,
                0.35,
              ],
            }}
            transition={{
              duration: 2.2,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
        </>
      )}


      <div
        className={
          `v5-level-platform v5-level-platform-${
            index % 4
          }`
        }
      />


      <Link
        to={
          `/learn/${
            encodeURIComponent(
              sign.signId
            )
          }`
        }
        className="v5-level-link"
        aria-label={
          `学习${sign.label}`
        }
      >
        <motion.div
          className={
            `v5-level-device v5-level-device-${
              index % 4
            }`
          }
          whileHover={{
            y: -13,
            scale: 1.08,
            rotate:
              tilt * -0.55,
          }}
          whileTap={{
            y: 7,
            scale: 0.93,
          }}
          animate={
            active
              ? {
                  y: [
                    0,
                    -8,
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
          <span className="v5-device-gloss" />

          <GestureGlyph
            variant={index}
          />

          <span className="v5-device-core" />
        </motion.div>
      </Link>


      <motion.div
        className="v5-level-word"
        whileHover={{
          y: -3,
        }}
      >
        {sign.label}
      </motion.div>
    </motion.div>
  );
}
