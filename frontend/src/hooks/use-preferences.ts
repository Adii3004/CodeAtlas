import { useLocalStorage } from "@/hooks/use-local-storage";
import { STORAGE_KEYS } from "@/lib/env";

export interface Preferences {
  /** Default retrieval depth for questions. */
  topK: number;
  /** Token budget for the LLM context window. */
  maxContextTokens: number;
  /** Sampling temperature for answers. */
  temperature: number;
  /** Show the referenced-files panel beside the conversation. */
  showReferencedFiles: boolean;
  /** Reduce non-essential motion. */
  reduceMotion: boolean;
}

export const DEFAULT_PREFERENCES: Preferences = {
  topK: 10,
  maxContextTokens: 4000,
  temperature: 0.2,
  showReferencedFiles: true,
  reduceMotion: false,
};

/** User preferences, persisted locally (no backend involvement). */
export function usePreferences() {
  const [preferences, setPreferences] = useLocalStorage<Preferences>(
    STORAGE_KEYS.preferences,
    DEFAULT_PREFERENCES,
  );

  const update = <K extends keyof Preferences>(
    key: K,
    value: Preferences[K],
  ) => {
    setPreferences((previous) => ({ ...previous, [key]: value }));
  };

  const reset = () => setPreferences(DEFAULT_PREFERENCES);

  // Merge with defaults so new keys appear for existing users.
  return {
    preferences: { ...DEFAULT_PREFERENCES, ...preferences },
    update,
    reset,
  };
}
