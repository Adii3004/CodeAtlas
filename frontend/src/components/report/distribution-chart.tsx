import { memo, useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { humanize } from "@/lib/format";

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

export interface DistributionDatum {
  name: string;
  value: number;
}

export interface DistributionChartProps {
  data: DistributionDatum[];
  height?: number;
  /** Cap the number of bars; the rest are summed into "Other". */
  limit?: number;
}

function prepare(data: DistributionDatum[], limit: number) {
  const sorted = [...data].sort((a, b) => b.value - a.value);
  if (sorted.length <= limit) return sorted;
  const head = sorted.slice(0, limit);
  const rest = sorted.slice(limit).reduce((sum, item) => sum + item.value, 0);
  return rest > 0 ? [...head, { name: "other", value: rest }] : head;
}

/** Horizontal bar chart for language/category distributions. */
function DistributionChartComponent({
  data,
  height = 260,
  limit = 8,
}: DistributionChartProps) {
  const rows = useMemo(
    () =>
      prepare(data, limit).map((item) => ({
        ...item,
        label: humanize(item.name),
      })),
    [data, limit],
  );

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={rows}
        layout="vertical"
        margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
      >
        <CartesianGrid
          horizontal={false}
          stroke="var(--border)"
          strokeDasharray="3 3"
        />
        <XAxis
          type="number"
          stroke="var(--muted-foreground)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          allowDecimals={false}
        />
        <YAxis
          type="category"
          dataKey="label"
          stroke="var(--muted-foreground)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={92}
        />
        <Tooltip
          cursor={{ fill: "var(--muted)", opacity: 0.4 }}
          contentStyle={{
            background: "var(--popover)",
            border: "1px solid var(--border)",
            borderRadius: "0.5rem",
            fontSize: "0.75rem",
            color: "var(--popover-foreground)",
          }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={22}>
          {rows.map((row, index) => (
            <Cell
              key={row.name}
              fill={CHART_COLORS[index % CHART_COLORS.length]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Charts re-render only when their data actually changes. */
export const DistributionChart = memo(DistributionChartComponent);

export default DistributionChart;
