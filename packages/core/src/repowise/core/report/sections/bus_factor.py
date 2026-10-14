"""Bus-factor exposure per component. Owners are counted, never named."""

from __future__ import annotations

from typing import Any

from repowise.core.report.model import (
    ReportContext,
    Section,
    check,
    component_summary,
    report_sections,
)

_METHOD = "fewest primary owners who together own over half the owned files"
#: A component whose bus factor is above this is named in the summary only.
_NOTED_UP_TO = 2


async def collect(ctx: ReportContext) -> list[dict[str, Any]]:
    found = await ctx.components()
    rollups = await ctx.rollups()
    criticality = {c.name: c.criticality for c in found.resolved.components}
    out: list[dict[str, Any]] = []
    figures: dict[str, dict[str, Any]] = {}
    outcomes = {"bus factor 1": 0, "bus factor 2": 0, "3 or more": 0, "unresolved": 0}
    quiet: list[str] = []
    for name, rolled in sorted((n, r) for n, r in rollups.items() if n is not None):
        bus = figures[name] = rolled["bus_factor"]
        if bus["basis"] == "unavailable":
            outcomes["unresolved"] += 1
            out.append(
                check(
                    f"bus-factor:{name}", reason=bus["reason"], method=_METHOD, basis="unresolved"
                )
            )
            continue
        if bus["value"] > _NOTED_UP_TO:
            outcomes["3 or more"] += 1
            quiet.append(name)
            continue
        outcomes[f"bus factor {bus['value']}"] += 1
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
    out.insert(
        0,
        component_summary(
            "bus-factor",
            outcomes=outcomes,
            quiet=quiet,
            method=_METHOD,
            basis="measured",
            data={"components": figures},
        ),
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
