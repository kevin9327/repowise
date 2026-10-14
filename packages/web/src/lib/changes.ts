/**
 * Pure Change Record helpers, safe to call from server and client components
 * alike. Kept out of the client table module: a server component cannot call
 * a function exported from a "use client" file.
 */
import type { ChangeListItem } from "@repowise-dev/types/changes";

/** The change's short name: the forge ref when it has one, else a trimmed id. */
export function changeLabel(c: Pick<ChangeListItem, "forge_ref" | "id">): string {
  return c.forge_ref ?? (c.id.length > 19 ? c.id.slice(0, 19) : c.id);
}

export type CommitsView = "changes" | "commits";

/** The Commits page in one view: `?view=changes` groups by merged change. */
export function commitsViewHref(repoId: string, view: CommitsView): string {
  const base = `/repos/${repoId}/commits`;
  return view === "changes" ? `${base}?view=changes` : base;
}

/** The view a `?view=` value asks for; anything else is the commit view. */
export function parseCommitsView(raw: string | string[] | undefined): CommitsView {
  return raw === "changes" ? "changes" : "commits";
}

/** Filters and paging of the by-change view, as its query parameters keep them. */
export interface ByChangeQuery {
  category?: string | undefined;
  attention?: boolean;
  offset?: number;
}

/** The by-change view with these filters; empty filters stay out of the URL. */
export function byChangeHref(repoId: string, next: ByChangeQuery = {}): string {
  const q = new URLSearchParams({ view: "changes" });
  if (next.category) q.set("category", next.category);
  if (next.attention) q.set("attention", "1");
  if (next.offset) q.set("offset", String(next.offset));
  return `${commitsViewHref(repoId, "commits")}?${q.toString()}`;
}

/** The commit categories a change can carry, in chip order. */
export const CHANGE_CATEGORIES = ["feature", "fix", "refactor", "docs", "test", "deps", "chore", "other"];

/** A category's name under `views.changes`; one this list does not know shows as stored. */
export function categoryLabel(t: (key: string) => string, category: string): string {
  return CHANGE_CATEGORIES.includes(category) ? t(`categories.${category}`) : category;
}
