import { useCallback, useEffect, useState } from "react";

/** State persisted to localStorage, synced across tabs. */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = window.localStorage.getItem(key);
      return stored ? (JSON.parse(stored) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const update = useCallback(
    (next: T | ((previous: T) => T)) => {
      setValue((previous) => {
        const resolved =
          typeof next === "function"
            ? (next as (previous: T) => T)(previous)
            : next;
        try {
          window.localStorage.setItem(key, JSON.stringify(resolved));
        } catch {
          // Storage full or unavailable — keep the in-memory value.
        }
        return resolved;
      });
    },
    [key],
  );

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== key || event.newValue === null) return;
      try {
        setValue(JSON.parse(event.newValue) as T);
      } catch {
        // Ignore malformed values written by other tabs.
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [key]);

  return [value, update] as const;
}
