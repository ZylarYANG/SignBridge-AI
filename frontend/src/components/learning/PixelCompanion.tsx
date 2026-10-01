import {
  motion,
} from "motion/react";

export function PixelCompanion() {
  return (
    <motion.div
      className="pq-companion"
      animate={{
        y: [
          0,
          -7,
          0,
        ],
      }}
      transition={{
        duration: 1.8,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    >
      <div className="pq-companion-shadow" />

      <div className="pq-companion-body">
        <span className="pq-companion-eye pq-companion-eye-left" />
        <span className="pq-companion-eye pq-companion-eye-right" />

        <span className="pq-companion-mouth" />

        <motion.span
          className="pq-companion-arm"
          animate={{
            rotate: [
              -8,
              20,
              -12,
              20,
              -8,
            ],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            repeatDelay: 1.6,
          }}
        >
          <i />
          <i />
          <i />
        </motion.span>
      </div>

      <motion.span
        className="pq-companion-arrow"
        animate={{
          x: [
            0,
            9,
            0,
          ],
          opacity: [
            0.45,
            1,
            0.45,
          ],
        }}
        transition={{
          duration: 1.1,
          repeat: Infinity,
        }}
      >
        →
      </motion.span>
    </motion.div>
  );
}
