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
