import {
  motion,
} from "motion/react";

type PortalGateV5Props = {
  onActivate: () => void;
  reverse?: boolean;
};

export function PortalGateV5({
  onActivate,
  reverse = false,
}: PortalGateV5Props) {
  return (
    <motion.button
      type="button"
      className={
        reverse
          ? "v5-portal v5-portal-reverse"
          : "v5-portal"
      }
      onClick={onActivate}
      whileHover={{
        scale: 1.06,
      }}
      whileTap={{
        scale: 0.92,
      }}
      aria-label={
        reverse
          ? "返回上一世界"
          : "前往下一世界"
      }
    >
      <motion.span
        className="v5-portal-ring v5-portal-ring-a"
        animate={{
          rotate: [
            0,
            360,
          ],
        }}
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: "linear",
        }}
      />

      <motion.span
        className="v5-portal-ring v5-portal-ring-b"
        animate={{
          rotate: [
            360,
            0,
          ],
        }}
        transition={{
          duration: 7,
          repeat: Infinity,
          ease: "linear",
        }}
      />

      <motion.span
        className="v5-portal-arrow"
        animate={{
          x:
            reverse
              ? [4, -6, 4]
              : [-4, 6, -4],
        }}
        transition={{
          duration: 1.4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        {
          reverse
            ? "←"
            : "→"
        }
      </motion.span>
    </motion.button>
  );
}
