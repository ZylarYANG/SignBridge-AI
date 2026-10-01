import { motion } from "motion/react";
import { Link } from "react-router-dom";

import type {
  CollectionSign,
} from "../../services/catalog";

type LessonCardProps = {
  sign: CollectionSign;
  index: number;
};

export function LessonCard({
  sign,
  index,
}: LessonCardProps) {
  return (
    <motion.div
      initial={{
        opacity: 0,
        y: 20,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay: Math.min(index * 0.05, 0.3),
        type: "spring",
        stiffness: 250,
        damping: 24,
      }}
      whileHover={{
        y: -5,
      }}
    >
      <Link
        className="lesson-card"
        to={`/learn/${encodeURIComponent(sign.signId)}`}
      >
        <div className="lesson-card-icon">
          ??
        </div>

        <div className="lesson-card-copy">
          <span>
            {
              sign.handednessPolicy === "both_hands"
                ? "????"
                : "?? / ???"
            }
          </span>

          <h3>{sign.label}</h3>

          <p>
            ???????????
          </p>
        </div>

        <div className="lesson-card-arrow">
          ?
        </div>
      </Link>
    </motion.div>
  );
}
