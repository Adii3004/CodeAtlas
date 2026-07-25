import { useCallback, useEffect, useRef, useState } from "react";

/** Copy text to the clipboard with a short-lived "copied" flag. */
export function useCopyToClipboard(resetAfterMs = 1500) {
  const [copied, setCopied] = useState(false);
  const timeout = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timeout.current), []);

  const copy = useCallback(
    async (value: string) => {
      try {
        await navigator.clipboard.writeText(value);
        setCopied(true);
        window.clearTimeout(timeout.current);
        timeout.current = window.setTimeout(
          () => setCopied(false),
          resetAfterMs,
        );
        return true;
      } catch {
        return false;
      }
    },
    [resetAfterMs],
  );

  return { copied, copy };
}
