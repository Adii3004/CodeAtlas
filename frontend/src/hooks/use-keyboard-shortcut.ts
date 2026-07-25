import { useEffect } from "react";

/** True when focus is inside a field, where shortcuts should not fire. */
function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return (
    target.isContentEditable ||
    ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)
  );
}

export interface KeyboardShortcutOptions {
  /** Fire even when focus is inside an input (used for Escape). */
  allowInFields?: boolean;
  enabled?: boolean;
}

/**
 * Binds a single-key shortcut on the document.
 *
 * Modifier combinations are ignored so browser and OS shortcuts keep
 * working.
 */
export function useKeyboardShortcut(
  key: string,
  handler: (event: KeyboardEvent) => void,
  { allowInFields = false, enabled = true }: KeyboardShortcutOptions = {},
) {
  useEffect(() => {
    if (!enabled) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== key) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (!allowInFields && isEditableTarget(event.target)) return;
      handler(event);
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [key, handler, allowInFields, enabled]);
}
