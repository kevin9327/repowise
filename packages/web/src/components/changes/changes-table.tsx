"use client";

import Link from "next/link";
import { ResponsiveTable, type ResponsiveColumn } from "@repowise-dev/ui/shared/responsive-table";
import { formatDate } from "@repowise-dev/ui/lib/format";
import type { ChangeSummary } from "@/lib/api/changes";
import { changeLabel } from "@/lib/changes";

export interface ChangesTableLabels {
  change: string;
  merged: string;
  category: string;
  files: string;
  lines: string;
  title: string;
  provenance: string;
}

export function ChangesTable({
  repoId,
  rows,
  labels,
  showProvenance,
}: {
  repoId: string;
  rows: ChangeSummary[];
  labels: ChangesTableLabels;
  showProvenance: boolean;
}) {
  const columns: ResponsiveColumn<ChangeSummary>[] = [
    {
      key: "id",
      header: labels.change,
      render: (c) => (
        <Link
          href={`/repos/${repoId}/changes/${encodeURIComponent(c.id)}`}
          className="font-mono text-xs text-[var(--color-accent-primary)] hover:underline"
        >
          {changeLabel(c)}
        </Link>
      ),
    },
    {
      key: "title",
      header: labels.title,
      cellClassName: "min-w-[220px] max-w-[520px] truncate",
      render: (c) => <span title={c.title}>{c.title}</span>,
    },
    {
      key: "merged_at",
      header: labels.merged,
      priority: 2,
      render: (c) => (
        <span className="text-xs text-[var(--color-text-secondary)]">
          {c.merged_at ? formatDate(c.merged_at) : ""}
        </span>
      ),
    },
    {
      key: "category",
      header: labels.category,
      priority: 2,
      render: (c) => <span className="text-xs">{c.category}</span>,
    },
    {
      key: "files",
      header: labels.files,
      align: "right",
      priority: 3,
      render: (c) => <span className="tabular-nums">{c.files_changed}</span>,
    },
    {
      key: "lines",
      header: labels.lines,
      align: "right",
      priority: 3,
      render: (c) => (
        <span className="font-mono text-xs tabular-nums">
          <span className="text-[var(--color-success)]">+{c.lines_added}</span>{" "}
          <span className="text-[var(--color-error)]">-{c.lines_deleted}</span>
        </span>
      ),
    },
  ];
  if (showProvenance) {
    columns.push({
      key: "provenance",
      header: labels.provenance,
      priority: 3,
      render: (c) => <span className="text-xs">{c.provenance?.label.replace("_", " ") ?? ""}</span>,
    });
  }
  return <ResponsiveTable columns={columns} rows={rows} rowKey={(c) => c.id} stacked="sm" />;
}
