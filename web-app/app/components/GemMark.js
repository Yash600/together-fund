"use client";

// A small decorative gem/diamond mark in the same thin-line style as
// together.fund's brand illustrations, with a subtle draw-in + float
// animation (CSS-only, no JS) so the header isn't static.
export default function GemMark() {
  return (
    <svg
      className="tf-gem-wrap"
      width="52"
      height="60"
      viewBox="0 0 120 140"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* shaded facet */}
      <polygon className="tf-gem-facet" points="40,15 10,45 56,122" />

      {/* crown + girdle + pavilion outline, each path drawn in on mount */}
      <path className="tf-gem-line" pathLength="1" d="M40,15 L80,15" />
      <path className="tf-gem-line" pathLength="1" d="M40,15 L10,45" />
      <path className="tf-gem-line" pathLength="1" d="M80,15 L110,45" />
      <path className="tf-gem-line" pathLength="1" d="M10,45 L110,45" />
      <path className="tf-gem-line" pathLength="1" d="M40,15 L60,45" />
      <path className="tf-gem-line" pathLength="1" d="M80,15 L60,45" />
      <path className="tf-gem-line" pathLength="1" d="M10,45 L60,130" />
      <path className="tf-gem-line" pathLength="1" d="M110,45 L60,130" />
      <path className="tf-gem-line" pathLength="1" d="M60,45 L60,130" />
    </svg>
  );
}
