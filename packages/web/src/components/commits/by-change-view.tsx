import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { EmptyState } from "@repowise-dev/ui/shared/empty-state";
import { OverviewSection } from "@repowise-dev/ui/overview";
import { ChangesTable } from "@/components/changes/changes-table";
import { listChanges } from "@/lib/api/changes";
import { commitsViewHref } from "@/lib/changes";

const PAGE_SIZE = 50;
const CATEGORIES = ["feature", "fix", "refactor", "docs", "test", "deps", "chore", "other"];

export interface ByChangeParams {
  category?: string | undefined;
  attention?: string | undefined;
  offset?: string | undefined;
}

const CHIP =
  "rounded-full border px-2.5 py-0.5 text-xs transition-colors border-[var(--color-border-default)] hover:bg-[var(--color-bg-elevated)]";
const ACTIVE = "bg-[var(--color-bg-elevated)] text-[var(--color-text-primary)] font-medium";

/**
 * The Commits page grouped by merged change, with each change's kept
 * evidence checklist summarised. Server-rendered: filters and paging are
 * query parameters, so every view is a link. The list reads checklists the
 * change pages already built and never builds one itself.
 */
export async function ByChangeView({ repoId, params }: { repoId: string; params: ByChangeParams }) {
  const t = await getTranslations("views.changes");
  const offset = Math.max(0, Number.parseInt(params.offset ?? "0", 10) || 0);
  const category = CATEGORIES.includes(params.category ?? "") ? params.category : undefined;
  const attention = params.attention === "1";

  let page;
  try {
    page = await listChanges(repoId, {
      limit: PAGE_SIZE,
      offset,
      category,
      evidence: true,
      needs_attention: attention || undefined,
    });
  } catch {
    page = null;
  }

  if (!page || (page.total === 0 && !category && !attention)) {
    return (
      <EmptyState
        title={t("emptyTitle")}
        description={t("emptyHint")}
        action={{ label: t("emptyAction"), href: `/repos/${repoId}/overview` }}
      />
    );
  }

  const href = (next: { offset?: number; category?: string | undefined; attention?: boolean }) => {
    const q = new URLSearchParams({ view: "changes" });
    if (next.category) q.set("category", next.category);
    if (next.attention) q.set("attention", "1");
    if (next.offset) q.set("offset", String(next.offset));
    return `${commitsViewHref(repoId, "commits")}?${q.toString()}`;
  };

  return (
    <OverviewSection title={t("byChangeTitle")} description={t("byChangeDescription")}>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Link
          href={href({ category, attention: !attention })}
          aria-pressed={attention}
          className={`${CHIP} ${attention ? ACTIVE : ""}`}
        >
          {t("needsAttention")}
        </Link>
        <span aria-hidden className="mx-1 h-4 w-px bg-[var(--color-border-default)]" />
        <nav className="flex flex-wrap gap-2" aria-label={t("category")}>
          <Link href={href({ attention })} className={`${CHIP} ${category ? "" : ACTIVE}`}>
            {t("allCategories")}
          </Link>
          {CATEGORIES.map((c) => (
            <Link
              key={c}
              href={href({ category: c, attention })}
              className={`${CHIP} ${category === c ? ACTIVE : ""}`}
            >
              {c}
            </Link>
          ))}
        </nav>
      </div>
      {attention && (
        <p className="mb-3 text-xs text-[var(--color-text-tertiary)]">{t("attentionScope")}</p>
      )}
      {page.items.length === 0 ? (
        <p className="py-6 text-sm text-[var(--color-text-secondary)]">
          {t(attention ? "attentionEmpty" : "filterEmpty")}
        </p>
      ) : (
        <ChangesTable repoId={repoId} rows={page.items} showProvenance={page.attribution} />
      )}
      <div className="mt-4 flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
        <span>{t("showing", { shown: page.items.length, total: page.total })}</span>
        <span className="flex gap-3">
          {offset > 0 && (
            <Link href={href({ category, attention, offset: Math.max(0, offset - PAGE_SIZE) })}>
              {t("newer")}
            </Link>
          )}
          {offset + PAGE_SIZE < page.total && (
            <Link href={href({ category, attention, offset: offset + PAGE_SIZE })}>{t("older")}</Link>
          )}
        </span>
      </div>
    </OverviewSection>
  );
}
