import { formatNumber, humanize } from "@/lib/format";
import type { RepositoryReport } from "@/types/api";

function table(headers: string[], rows: string[][]): string[] {
  if (rows.length === 0) return ["_None._", ""];
  return [
    `| ${headers.join(" | ")} |`,
    `| ${headers.map(() => "---").join(" | ")} |`,
    ...rows.map((row) => `| ${row.join(" | ")} |`),
    "",
  ];
}

function counts(record: Record<string, number>): string[] {
  const rows = Object.entries(record)
    .filter(([, count]) => count > 0)
    .sort(([, a], [, b]) => b - a)
    .map(([name, count]) => [humanize(name), formatNumber(count)]);
  return table(["Name", "Files"], rows);
}

/** Render a report payload as a shareable Markdown document. */
export function reportToMarkdown(report: RepositoryReport): string {
  const { general, graph_summary: graph, architecture, issues } = report;

  const lines: string[] = [
    `# Repository Report: ${general.repository_name}`,
    "",
    `Generated: ${new Date(general.generated_at).toLocaleString()}`,
    `Root: \`${general.root_path}\``,
    "",
    "## General",
    "",
    ...table(
      ["Metric", "Value"],
      [
        ["Total files", formatNumber(general.total_files)],
        ["Parsed files", formatNumber(general.parsed_files)],
        ["Total symbols", formatNumber(general.total_symbols)],
        ["Total imports", formatNumber(general.total_imports)],
      ],
    ),
    "## Languages",
    "",
    ...counts(report.languages),
    "## Categories",
    "",
    ...counts(report.categories),
    "## Dependency graph",
    "",
    ...table(
      ["Metric", "Value"],
      [
        ["Nodes", formatNumber(graph.nodes)],
        ["Edges", formatNumber(graph.edges)],
        ["Density", graph.density.toFixed(4)],
        ["Connected components", formatNumber(graph.connected_components)],
        ["Largest component", formatNumber(graph.largest_component_size)],
        ["Cycles", formatNumber(graph.cycle_count)],
      ],
    ),
    "## Architecture highlights",
    "",
    "### Most imported files",
    "",
    ...table(
      ["File", "Fan-in"],
      architecture.most_imported.map((item) => [
        `\`${item.path}\``,
        formatNumber(item.count),
      ]),
    ),
    "### Most dependent files",
    "",
    ...table(
      ["File", "Fan-out"],
      architecture.most_dependent.map((item) => [
        `\`${item.path}\``,
        formatNumber(item.count),
      ]),
    ),
    "### Root modules",
    "",
    architecture.root_modules.length === 0
      ? "_None._"
      : architecture.root_modules.map((path) => `- \`${path}\``).join("\n"),
    "",
    "### Leaf modules",
    "",
    architecture.leaf_modules.length === 0
      ? "_None._"
      : architecture.leaf_modules.map((path) => `- \`${path}\``).join("\n"),
    "",
    "## Potential issues",
    "",
  ];

  if (issues.circular_dependencies.length > 0) {
    lines.push("### Circular dependencies", "");
    for (const cycle of issues.circular_dependencies) {
      lines.push(`- ${cycle.join(" → ")} → ${cycle[0]}`);
    }
    lines.push("");
  }

  if (issues.high_fan_in.length > 0) {
    lines.push("### High fan-in modules", "");
    lines.push(
      ...table(
        ["File", "Fan-in"],
        issues.high_fan_in.map((item) => [
          `\`${item.path}\``,
          formatNumber(item.count),
        ]),
      ),
    );
  }

  if (issues.high_fan_out.length > 0) {
    lines.push("### High fan-out modules", "");
    lines.push(
      ...table(
        ["File", "Fan-out"],
        issues.high_fan_out.map((item) => [
          `\`${item.path}\``,
          formatNumber(item.count),
        ]),
      ),
    );
  }

  if (issues.unresolved_imports.length > 0) {
    lines.push("### Unresolved imports", "");
    for (const unresolved of issues.unresolved_imports.slice(0, 50)) {
      const { module, name, line } = unresolved.statement;
      const target = [module, name].filter(Boolean).join(".");
      lines.push(`- \`${unresolved.file_path}\` line ${line}: \`${target}\``);
    }
    if (issues.unresolved_imports.length > 50) {
      lines.push(
        `- …and ${issues.unresolved_imports.length - 50} more unresolved imports.`,
      );
    }
    lines.push("");
  }

  const issueCount =
    issues.circular_dependencies.length +
    issues.high_fan_in.length +
    issues.high_fan_out.length +
    issues.unresolved_imports.length;

  if (issueCount === 0) lines.push("No issues detected.", "");

  return lines.join("\n");
}

/** Trigger a client-side download of a text file. */
export function downloadTextFile(
  filename: string,
  contents: string,
  mimeType = "text/markdown;charset=utf-8",
): void {
  const blob = new Blob([contents], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
