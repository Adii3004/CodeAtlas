import { animate, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

import { formatNumber } from "@/lib/format";

export interface AnimatedNumberProps {
  value: number;
  /** Custom formatter; defaults to locale-grouped integers. */
  format?: (value: number) => string;
  durationMs?: number;
  className?: string;
}

/**
 * Counts up to `value` on mount and whenever it changes.
 *
 * The animation is driven by requestAnimationFrame, which browsers throttle
 * in background tabs, so a safety timer snaps to the final value if the
 * animation has not finished. The true value is always exposed to assistive
 * technology regardless of animation state.
 */
export function AnimatedNumber({
  value,
  format = formatNumber,
  durationMs = 900,
  className,
}: AnimatedNumberProps) {
  const reduceMotion = useReducedMotion();
  // Background tabs throttle rAF, so only count up when actually visible.
  const canAnimate = () =>
    !reduceMotion && document.visibilityState === "visible";
  const [display, setDisplay] = useState(() => (canAnimate() ? 0 : value));
  const previous = useRef(display);

  useEffect(() => {
    if (!canAnimate()) {
      setDisplay(value);
      previous.current = value;
      return;
    }

    const settle = () => {
      previous.current = value;
      setDisplay(value);
    };

    const controls = animate(previous.current, value, {
      duration: durationMs / 1000,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: setDisplay,
      onComplete: settle,
    });

    // Guarantees the correct number is shown even if rAF never advances.
    const fallback = window.setTimeout(settle, durationMs + 400);

    return () => {
      controls.stop();
      window.clearTimeout(fallback);
    };
  }, [value, durationMs, reduceMotion]);

  return (
    <span className={className}>
      <span aria-hidden>{format(Math.round(display))}</span>
      <span className="sr-only">{format(value)}</span>
    </span>
  );
}
