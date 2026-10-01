import {
  motion,
} from "motion/react";

export function CompanionV5() {
  return (
    <motion.div
      className="v5-companion"
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
        duration: 2.5,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    >
      <div className="v5-companion-face">
        <span className="v5-companion-eye v5-companion-eye-left" />
        <span className="v5-companion-eye v5-companion-eye-right" />
        <span className="v5-companion-mouth" />
      </div>

      <motion.span
        className="v5-companion-arm"
        animate={{
          rotate: [
            -8,
            28,
            -16,
            24,
            -8,
          ],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          repeatDelay: 1.9,
          ease: "easeInOut",
        }}
      >
        <i />
        <i />
        <i />
      </motion.span>

      <motion.span
        className="v5-companion-pointer"
        animate={{
          x: [
            0,
            8,
            0,
          ],
          opacity: [
            0.55,
            1,
            0.55,
          ],
        }}
        transition={{
          duration: 1.3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
    </motion.div>
  );
}
