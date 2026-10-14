import { describe, expect, it, vi } from "vitest";

const redirect = vi.fn();
vi.mock("next/navigation", () => ({ redirect: (to: string) => redirect(to) }));

import ChangesPage from "./page";
import { repoNavItems } from "@/components/layout/nav-items";
import { parseCommitsView } from "@/lib/changes";

describe("/repos/[id]/changes", () => {
  it("redirects to the Commits page grouped by change", async () => {
    await ChangesPage({ params: Promise.resolve({ id: "r1" }) });
    expect(redirect).toHaveBeenCalledWith("/repos/r1/commits?view=changes");
  });

  it("is no longer a navigation entry", () => {
    expect(repoNavItems("r1").map((i) => i.href)).not.toContain("/repos/r1/changes");
  });

  it("reads only view=changes as the by-change view", () => {
    expect(parseCommitsView("changes")).toBe("changes");
    expect(parseCommitsView(undefined)).toBe("commits");
    expect(parseCommitsView("anything")).toBe("commits");
  });
});
