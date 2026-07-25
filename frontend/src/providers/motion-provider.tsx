import { MotionConfig } from "framer-motion";
import { useEffect, type ReactNode } from "react";

import { usePreferences } from "@/hooks/use-preferences";

/**
 * Applies the user's motion preference.
 *
 * `reducedMotion="user"` already honours the OS setting; the stored
 * preference can force it on. The data attribute lets CSS transitions
 * (which Framer Motion does not control) opt out too.
 */
export function MotionProvider({ children }: { children: ReactNode }) {
  const { preferences } = usePreferences();
  const reduce = preferences.reduceMotion;

  useEffect(() => {
    document.documentElement.toggleAttribute("data-reduce-motion", reduce);
  }, [reduce]);

  return (
    <MotionConfig reducedMotion={reduce ? "always" : "user"}>
      {children}
    </MotionConfig>
  );
}
