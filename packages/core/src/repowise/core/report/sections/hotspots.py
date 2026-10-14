"""Hotspots: files git history flags for high recent churn, per component."""

from __future__ import annotations

from typing import Any

from repowise.core.report.model import ReportContext, Section, check, report_sections

_METHOD = "files git history flags as hotspots (high recent churn), from the component rollups"


async def collect(ctx: ReportContext) -> list[dict[str, Any]]:
    rollups = await ctx.rollups()
    whole = (rollups.get(None) or {}).get("hotspots") or {"basis": "unavailable"}
    if whole["basis"] != "measured":
        return [
            check(
                "hotspots",
                reason=whole.get("reason", "no git history indexed"),
                method=_METHOD,
                basis="unresolved",
            )
        ]
    by_component = sorted(
        (
            (name, r["hotspots"])
            for name, r in rollups.items()
            if name is not None and r["hotspots"].get("count")
        ),
        key=lambda kv: (-kv[1]["count"], kv[0]),
    )
    out = [
        check(
            "hotspots",
            reason=f"{whole['count']} hotspot file(s) across {len(by_component)} component(s)",
            details=[f"{name}: {h['count']}" for name, h in by_component],
            method=_METHOD,
            basis="measured",
            data={"count": whole["count"], "top": whole["top"]},
        )
    ]
    for name, h in by_component:
        out.append(
            check(
                f"hotspots:{name}",
                reason=f"{h['count']} hotspot file(s)",
                details=h["top"],
                method=_METHOD,
                basis="measured",
                data=h,
            )
        )
    return out


report_sections.register(
    "hotspots",
    Section(
        title="Hotspots",
        summary="Files with high recent churn, counted per component.",
        collect=collect,
        order=20,
    ),
)
