import { motion } from "motion/react";

type Props = {
  label: string;
};

export function StandardSignPreview({
  label,
}: Props) {
  return (
    <div className="standard-preview">
      <div className="standard-preview-heading">
        <span>标准动作</span>
        <small>观察完整动作</small>
      </div>

      <div className="standard-preview-stage">
        <motion.div
          className="preview-spark preview-spark-a"
          animate={{
            rotate: [0, 18, 0],
            scale: [1, 1.18, 1],
          }}
          transition={{
            duration: 2.4,
            repeat: Infinity,
          }}
        >
          ✦
        </motion.div>

        <motion.div
          className="preview-spark preview-spark-b"
          animate={{
            y: [0, -8, 0],
          }}
          transition={{
            duration: 1.8,
            repeat: Infinity,
          }}
        >
          ✦
        </motion.div>

        <svg
          className="standard-preview-svg"
          viewBox="0 0 420 320"
          aria-label={`${label}标准动作演示`}
        >
          <circle
            cx="210"
            cy="62"
            r="34"
            className="preview-head"
          />

          <path
            d="M210 101 L210 210"
            className="preview-body"
          />

          <path
            d="M210 127 L151 177"
            className="preview-body"
          />

          <path
            d="M210 127 L269 177"
            className="preview-body"
          />

          <path
            d="M210 210 L178 274"
            className="preview-body"
          />

          <path
            d="M210 210 L242 274"
            className="preview-body"
          />

          <motion.circle
            cx="148"
            cy="177"
            r="19"
            className="preview-hand"
            animate={{
              x: [0, 16, 6, 0],
              y: [0, -27, -10, 0],
            }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.circle
            cx="272"
            cy="177"
            r="19"
            className="preview-hand"
            animate={{
              x: [0, -16, -6, 0],
              y: [0, -27, -10, 0],
            }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.path
            d="M134 211 Q210 133 286 211"
            className="preview-trajectory"
            initial={{
              pathLength: 0.1,
            }}
            animate={{
              pathLength: 1,
              opacity: [0.2, 0.95, 0.2],
            }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
            }}
          />
        </svg>

        <motion.div
          className="standard-preview-word"
          initial={{
            opacity: 0,
            scale: 0.85,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
          transition={{
            type: "spring",
            stiffness: 260,
            damping: 19,
          }}
        >
          {label}
        </motion.div>
      </div>

      <div className="preview-control-row">
        <motion.button
          type="button"
          whileTap={{
            scale: 0.88,
          }}
        >
          ↻
        </motion.button>

        <motion.button
          type="button"
          className="preview-play-button"
          whileHover={{
            scale: 1.06,
          }}
          whileTap={{
            scale: 0.9,
          }}
        >
          ▶
        </motion.button>

        <span>自动循环</span>
      </div>
    </div>
  );
}
