import type { FileCategory } from "@/types/api";

/**
 * Node colors by file category.
 *
 * Warm-leaning hues that stay legible in both themes; each entry maps to a
 * CSS color expression so theme switches update the canvas automatically.
 */
export const CATEGORY_COLORS: Record<FileCategory, string> = {
  source_code: "var(--chart-1)",
  test: "var(--chart-2)",
  configuration: "var(--chart-3)",
  documentation: "var(--chart-4)",
  data: "var(--chart-5)",
  script: "var(--chart-3)",
  image: "var(--subtle)",
  archive: "var(--subtle)",
  binary: "var(--subtle)",
  unknown: "var(--subtle)",
};

export const CATEGORY_LABELS: Record<FileCategory, string> = {
  source_code: "Source",
  test: "Tests",
  configuration: "Config",
  documentation: "Docs",
  data: "Data",
  script: "Scripts",
  image: "Images",
  archive: "Archives",
  binary: "Binaries",
  unknown: "Other",
};

export function categoryColor(category: FileCategory): string {
  return CATEGORY_COLORS[category] ?? CATEGORY_COLORS.unknown;
}
