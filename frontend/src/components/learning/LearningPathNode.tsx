import { motion } from "motion/react";
import { Link } from "react-router-dom";

import type {
  CollectionSign,
} from "../../services/catalog";

type Props = {
  sign: CollectionSign;
  index: number;
  active: boolean;
};

const ICONS = [
  "👋",
  "🤟",
  "🤝",
  "👍",
  "💬",
  "✨",
];

export function LearningPathNode({
  sign,
  index,
  active,
}: Props) {
  const side =
    index % 4 === 0
      ? "center"
      : index % 4 === 1
        ? "right"
        : index % 4 === 2
          ? "center"
          : "left";

  return (
    <motion.div
      className={
        `path-node-row path-node-row-${side}`
      }
      initial={{
        opacity: 0,
        y: 26,
        scale: 0.92,
      }}
      animate={{
        opacity: 1,
        y: 0,
        scale: 1,
      }}
      transition={{
        delay: 0.08 + index * 0.055,
        type: "spring",
        stiffness: 250,
        damping: 21,
      }}
    >
      <div className="path-node-wrap">
        {active && (
          <motion.div
            className="path-start-bubble"
            initial={{
              opacity: 0,
              y: 7,
              scale: 0.9,
            }}
            animate={{
              opacity: 1,
              y: [0, -4, 0],
              scale: 1,
            }}
            transition={{
              opacity: {
                duration: 0.25,
              },
              scale: {
                type: "spring",
                stiffness: 260,
                damping: 18,
              },
              y: {
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              },
            }}
          >
            从这里开始
          </motion.div>
        )}

        <Link
          to={`/learn/${encodeURIComponent(sign.signId)}`}
          className="path-node-link"
          aria-label={`学习${sign.label}`}
        >
          <motion.div
            className={
              active
                ? "path-node path-node-active"
                : "path-node"
            }
            whileHover={{
              scale: 1.08,
              y: -3,
            }}
            whileTap={{
              scale: 0.9,
              y: 5,
            }}
            animate={
              active
                ? {
                    y: [0, -5, 0],
                  }
                : undefined
            }
            transition={
              active
                ? {
                    duration: 2.2,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }
                : {
                    type: "spring",
                    stiffness: 350,
                    damping: 18,
                  }
            }
          >
            <span className="path-node-shine" />
            <span className="path-node-icon">
              {ICONS[index % ICONS.length]}
            </span>
          </motion.div>
        </Link>

        <motion.div
          className="path-node-label"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          transition={{
            delay: 0.16 + index * 0.055,
          }}
        >
          <strong>{sign.label}</strong>
          <small>
            {active ? "准备学习" : "点击开始"}
          </small>
        </motion.div>
      </div>
    </motion.div>
  );
}
