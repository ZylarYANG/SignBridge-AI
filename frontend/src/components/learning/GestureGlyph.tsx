type GestureGlyphProps = {
  variant?: number;
  className?: string;
};

export function GestureGlyph({
  variant = 0,
  className = "",
}: GestureGlyphProps) {
  const fingerLift =
    [
      0,
      5,
      -3,
      7,
    ][variant % 4];

  return (
    <svg
      className={`v5-gesture-glyph ${className}`}
      viewBox="0 0 100 100"
      aria-hidden="true"
    >
      <path
        d="
          M33 55
          C29 45 31 34 37 32
          C42 30 46 34 47 41
          L48 25
          C48 19 52 16 57 17
          C62 18 64 22 63 28
          L62 41
          L66 24
          C68 18 72 16 77 18
          C82 20 83 25 81 31
          L75 49
          L81 37
          C84 32 89 31 93 34
          C97 37 97 42 94 47
          L82 68
          C77 79 67 85 55 85
          C42 85 32 79 27 69
          L18 52
          C15 46 17 41 22 39
          C27 37 31 41 33 46
          Z
        "
        transform={`translate(0 ${fingerLift})`}
      />

      <path
        className="v5-gesture-glyph-line"
        d="
          M38 58
          C48 62 59 61 70 55
        "
      />

      <path
        className="v5-gesture-glyph-line"
        d="
          M48 46
          L47 63
        "
      />

      <path
        className="v5-gesture-glyph-line"
        d="
          M61 43
          L59 64
        "
      />
    </svg>
  );
}
