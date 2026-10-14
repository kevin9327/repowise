// @vitest-environment jsdom

import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { createTranslator } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import messages from "../../../messages/en.json";
import type { ChangeListItem, ChangeListResponse } from "@/lib/api/changes";

const listChanges = vi.fn();
vi.mock("@/lib/api/changes", () => ({ listChanges: (...a: unknown[]) => listChanges(...a) }));
vi.mock("next-intl/server", () => ({
  getTranslations: async (namespace: string) =>
    createTranslator({ locale: "en", messages, namespace: namespace as never }),
}));
vi.mock("next/link", () => ({
  default: ({ href, children, ...rest }: { href: string; children?: React.ReactNode }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

import { ByChangeView } from "./by-change-view";

function row(id: string, over: Partial<ChangeListItem> = {}): ChangeListItem {
  return {
    schema_version: 1,
    id,
    identity: { kind: "pr", value: id.slice(3) },
    shape: "squash",
    forge: "github",
    forge_ref: `#${id.slice(3)}`,
    title: `change ${id}`,
    merged_at: "2026-10-01T00:00:00+00:00",
    head_sha: "a".repeat(40),
    author: { name: "Ann", email: "ann@example.com" },
    commit_count: 3,
    files_changed: 2,
    lines_added: 10,
    lines_deleted: 1,
    category: "feature",
    provenance: null,
    ...over,
  };
}

function page(items: ChangeListItem[]): ChangeListResponse {
  return { items, total: items.length, limit: 50, offset: 0, attribution: false };
}

async function show(params: Record<string, string> = {}) {
  render(await ByChangeView({ repoId: "r1", params }));
}

afterEach(() => {
  cleanup();
  listChanges.mockReset();
});

describe("ByChangeView", () => {
  it("summarises each change's kept checklist and never asks for a build", async () => {
    const at = "2026-10-14T00:00:00+00:00";
    listChanges.mockResolvedValue(
      page([
        row("pr-1", { evidence_summary: { generated_at: at, ok: 5, attention: 2, unknown: 1 } }),
        row("pr-2", { evidence_summary: { generated_at: at, ok: 9, attention: 0, unknown: 0 } }),
        row("pr-3"),
      ]),
    );
    await show();

    expect(listChanges).toHaveBeenCalledWith("r1", {
      limit: 50,
      offset: 0,
      category: undefined,
      evidence: true,
      needs_attention: undefined,
    });
    expect(screen.getAllByText("2 need attention").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1 unknown").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Nothing flagged").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Not built").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "#1" })[0]!.getAttribute("href")).toBe("/repos/r1/changes/pr-1");
    expect(screen.queryByText(/Only changes with a built checklist/)).toBeNull();
  });

  it("filters to changes needing attention and says what the filter covers", async () => {
    listChanges.mockResolvedValue(page([]));
    await show({ attention: "1", category: "fix" });

    expect(listChanges.mock.calls[0]![1]).toMatchObject({ needs_attention: true, category: "fix" });
    expect(screen.getByText(/Only changes with a built checklist are listed/)).toBeTruthy();
    expect(screen.getByText("No built checklist flags anything for attention.")).toBeTruthy();

    const chip = screen.getByRole("link", { name: "Needs attention" });
    expect(chip.getAttribute("aria-pressed")).toBe("true");
    // Pressing it again clears the filter and keeps the category.
    expect(chip.getAttribute("href")).toBe("/repos/r1/commits?view=changes&category=fix");
    // A category chip keeps the attention filter.
    expect(screen.getByRole("link", { name: "docs" }).getAttribute("href")).toBe(
      "/repos/r1/commits?view=changes&category=docs&attention=1",
    );
  });

  it("never reads a checklist with no items as clean", async () => {
    const empty = { generated_at: "2026-10-14T00:00:00+00:00", ok: 0, attention: 0, unknown: 0 };
    listChanges.mockResolvedValue(page([row("pr-1", { evidence_summary: empty })]));
    await show();
    expect(screen.getAllByText("Unknown").length).toBeGreaterThan(0);
    expect(screen.queryByText("Nothing flagged")).toBeNull();
  });

  it("pages within the combined attention and category filter", async () => {
    listChanges.mockResolvedValue({ ...page([row("pr-1")]), total: 120, offset: 50 });
    await show({ attention: "1", category: "fix", offset: "50" });
    expect(listChanges.mock.calls[0]![1]).toMatchObject({ offset: 50, category: "fix", needs_attention: true });
    expect(screen.getByRole("link", { name: "Newer" }).getAttribute("href")).toBe(
      "/repos/r1/commits?view=changes&category=fix&attention=1",
    );
    expect(screen.getByRole("link", { name: "Older" }).getAttribute("href")).toBe(
      "/repos/r1/commits?view=changes&category=fix&attention=1&offset=100",
    );
  });

  it("shows the empty state when no change is indexed", async () => {
    listChanges.mockResolvedValue(page([]));
    await show();
    expect(screen.getByText("No changes indexed yet")).toBeTruthy();
  });
});
