"""Governing decisions per component, with the ones gone stale."""

from __future__ import annotations

from typing import Any

from repowise.core.report.model import ReportContext, Section, check, report_sections

_METHOD = (
    "accepted decisions at a governing currency whose recorded files fall in the component; "
    "stale at staleness 0.5 or above"
)


async def collect(ctx: ReportContext) -> list[dict[str, Any]]:
    from repowise.core.events.snapshot import governing_decisions

    governing, stale = await governing_decisions(ctx.session, ctx.repository_id)
    titles = {d: t for pairs in governing.values() for d, t in pairs}
    out = [
        check(
            "decisions",
            reason=f"{len(titles)} governing decision(s), {len(stale)} stale",
            details=[f"stale: {d} {titles[d]}" for d in sorted(stale)],
            method=_METHOD,
            basis="declared",
            data={"governing": len(titles), "stale": sorted(stale)},
        )
    ]
    found = await ctx.components()
    for comp in found.resolved.components:
        paths = found.resolved.files.get(comp.name, ())
        ids = sorted({d for p in paths for d, _ in governing.get(p, ())})
        if not ids:
            continue
        gone = [d for d in ids if d in stale]
        out.append(
            check(
                f"decisions:{comp.name}",
                reason=f"{len(ids)} governing decision(s), {len(gone)} stale",
                details=[f"{d}{' (stale)' if d in stale else ''}: {titles[d]}" for d in ids],
                method=_METHOD,
                basis="declared",
                data={"governing": ids, "stale": gone},
            )
        )
    return out


report_sections.register(
    "decisions",
    Section(
        title="Governing decisions",
        summary="Recorded decisions that bind each component's files, and which are stale.",
        collect=collect,
        order=70,
    ),
)
