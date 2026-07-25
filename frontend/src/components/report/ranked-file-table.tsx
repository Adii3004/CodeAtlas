import { DataTable } from "@/components/common/data-table";
import { formatNumber } from "@/lib/format";
import type { RankedFile } from "@/types/api";

export interface RankedFileTableProps {
  rows: RankedFile[];
  countHeader?: string;
  emptyTitle?: string;
}

/** Shared table for "most imported" / "most dependent" style rankings. */
export function RankedFileTable({
  rows,
  countHeader = "Count",
  emptyTitle = "No files to rank",
}: RankedFileTableProps) {
  return (
    <DataTable
      rows={rows}
      rowKey={(row) => row.path}
      emptyTitle={emptyTitle}
      columns={[
        {
          id: "path",
          header: "File",
          cell: (row) => (
            <span className="font-mono text-xs break-all">{row.path}</span>
          ),
        },
        {
          id: "count",
          header: countHeader,
          align: "right",
          className: "w-24",
          cell: (row) => formatNumber(row.count),
        },
      ]}
    />
  );
}
