type PixelHandGlyphProps = {
  variant?: number;
  className?: string;
};

export function PixelHandGlyph({
  variant = 0,
  className = "",
}: PixelHandGlyphProps) {
  const offset =
    [
      0,
      2,
      -2,
      3,
    ][variant % 4];

  return (
    <svg
      className={
        `pq-pixel-hand ${className}`
      }
      viewBox="0 0 64 64"
      shapeRendering="crispEdges"
      aria-hidden="true"
    >
      <path
        d="
          M18 34
          H14
          V26
          H18
          V18
          H22
          V30
          H24
          V12
          H28
          V29
          H30
          V9
          H34
          V29
          H36
          V14
          H40
          V31
          H43
          V20
          H47
          V35
          H50
          V43
          H46
          V49
          H40
          V53
          H25
          V50
          H19
          V45
          H16
          V39
          H18
          Z
        "
        transform={`translate(0 ${offset})`}
      />

      <rect
        x="24"
        y="37"
        width="18"
        height="3"
        className="pq-pixel-hand-detail"
      />

      <rect
        x="29"
        y="42"
        width="10"
        height="3"
        className="pq-pixel-hand-detail"
      />
    </svg>
  );
}
