/**
 * Pure Change Record helpers, safe to call from server and client components
 * alike. Kept out of the client table module: a server component cannot call
 * a function exported from a "use client" file.
 */
import type { ChangeSummary } from "@repowise-dev/types/changes";

/** The change's short name: the forge ref when it has one, else a trimmed id. */
export function changeLabel(c: Pick<ChangeSummary, "forge_ref" | "id">): string {
  return c.forge_ref ?? (c.id.length > 19 ? c.id.slice(0, 19) : c.id);
}
