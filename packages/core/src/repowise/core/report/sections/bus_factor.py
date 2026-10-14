"""Bus-factor exposure per component. Owners are counted, never named."""

from __future__ import annotations

from typing import Any

from repowise.core.report.model import ReportContext, Section, check, report_sections


async def collect(ctx: ReportContext) -> list[dict[str, Any]]:
    found = await ctx.components()
    rollups = await ctx.rollups()
    criticality = {c.name: c.criticality for c in found.resolved.components}
    out = []
    for name, rolled in sorted((n, r) for n, r in rollups.items() if n is not None):
        bus = rolled["bus_factor"]
        if bus["basis"] == "unavailable":
            out.append(
                check(
                    f"bus-factor:{name}",
                    reason=bus["reason"],
                    method="fewest primary owners who together own over half the owned files",
                    basis="unresolved",
                )
            )
            continue
        details = [
            f"{bus['owned_files']} of {bus['file_count']} file(s) have a known primary owner",
            f"{bus['single_owner_files']} file(s) have a single owner",
        ]
        if criticality.get(name):
            details.append(f"criticality: {criticality[name]}")
        if bus.get("note"):
            details.append(bus["note"])
        out.append(
            check(
                f"bus-factor:{name}",
                reason=f"bus factor {bus['value']}",
                details=details,
                method=bus["method"],
                basis=bus["basis"],
                data=bus,
            )
        )
    return out


report_sections.register(
    "bus-factor",
    Section(
        title="Bus-factor exposure",
        summary="How few people hold most of each component's files; counted, never named.",
        collect=collect,
        order=30,
    ),
)
