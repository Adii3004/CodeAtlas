import { useEffect, useState } from "react";

/** Subscribe to a CSS media query. */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(
    () => window.matchMedia(query).matches,
  );

  useEffect(() => {
    const media = window.matchMedia(query);
    const onChange = () => setMatches(media.matches);
    onChange();
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}

/** True below the `lg` breakpoint, where the sidebar collapses to a sheet. */
export function useIsMobile(): boolean {
  return useMediaQuery("(max-width: 1023px)");
}
