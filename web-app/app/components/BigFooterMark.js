"use client";

import { useEffect, useRef, useState } from "react";

// Together Fund's real footer has a giant static wordmark with no animation
// at all (checked the live site directly). This is our own take: same big
// brand-mark idea, but with a subtle fade/slide-up entrance the first time
// it scrolls into view, rather than a straight copy.
export default function BigFooterMark() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="tf-bigfooter" ref={ref}>
      <div className={`tf-bigfooter-mark${visible ? " in-view" : ""}`}>
        Together<span>.</span>tools
      </div>
    </div>
  );
}
