"""Component map and posture: each component's health, catalog facts and
ownership findings, from the component rollups and ownership checks."""

from __future__ import annotations

from typing import Any

from repowise.core.report.model import ReportContext, Section, check, report_sections

_OWNERSHIP_METHOD = (
    "declared owners (catalog spec.owner, CODEOWNERS, teams.yaml) against indexed "
    "commits in the 90 days before the newest one"
)


async def collect(ctx: ReportContext) -> list[dict[str, Any]]:
    from repowise.core.components.catalog import owner_group_name
    from repowise.core.components.store import component_ownership

    found = await ctx.components()
    rollups = await ctx.rollups()
    files = found.resolved.files
    comps = [(c, files[c.name]) for c in found.resolved.components]
    blocks, directory_issues = await component_ownership(
        ctx.session,
        ctx.repository_id,
        ctx.repo_root,
        comps,
        {n: r["bus_factor"] for n, r in rollups.items() if n is not None},
    )

    declared = sum(1 for c, _ in comps if c.declared)
    catalog = found.catalog
    out = [
        check(
            "component-map",
            score=None,
            reason=(
                f"{len(comps)} component(s): {declared} declared, {len(comps) - declared} "
                f"derived; {len(found.resolved.unassigned)} file(s) belong to none"
            ),
            details=[
                *(f"catalog file: {s}" for s in catalog.sources),
                *(f"catalog {i.severity}: {i.message}" for i in catalog.issues),
                *(f"team directory: {issue}" for issue in directory_issues),
            ],
            method=(
                "components declared in .repowise/components.yaml or catalog-info.yaml, "
                "else derived from workspace services, module pages or top-level directories"
            ),
            basis="declared" if catalog.sources else "inferred",
            data={
                "declared": declared,
                "derived": len(comps) - declared,
                "unassigned_files": len(found.resolved.unassigned),
            },
        )
    ]
    gated = ((rollups.get(None) or {}).get("health") or {}).get("gated_files")
    if gated:
        out.append(
            check(
                "health:gated",
                reason=f"{gated} file(s) in languages health is held back on carry no score here",
                method="the language gates every health surface applies",
                basis="gated",
                data={"gated_files": gated},
            )
        )
    for comp, paths in comps:
        health = rollups.get(comp.name, {}).get("health") or {"basis": "unavailable"}
        ownership = blocks.get(comp.name, {})
        findings = ownership.get("findings", [])
        if health.get("basis") == "measured":
            basis, score = "measured", health["average"]
            posture = f"health {health['average']} over {health['scored_files']} scored file(s)"
        else:
            basis = "gated" if health.get("gated_files") else "unresolved"
            score = None
            posture = health.get("reason", "no health score")
        source = f"declared in {comp.declared_in}" if comp.declared else f"derived ({comp.source})"
        group = owner_group_name(comp.owner)
        details = [
            source,
            *([f"criticality: {comp.criticality}"] if comp.criticality else []),
            *([f"tags: {', '.join(comp.tags)}"] if comp.tags else []),
            *([f"owning team: {group}"] if group else []),
            *(f"{f['kind']}: {f['message']}" for f in findings),
        ]
        out.append(
            check(
                f"component:{comp.name}",
                score=score,
                reason=f"{len(paths)} file(s); {posture}; {len(findings)} ownership finding(s)",
                details=details,
                method=(
                    f"{health.get('method', 'file health scores')}; ownership: {_OWNERSHIP_METHOD}"
                ),
                basis=basis,
                data={
                    "source": comp.source,
                    "criticality": comp.criticality,
                    "tags": list(comp.tags),
                    "owning_team": group,
                    "file_count": len(paths),
                    "health": health,
                    "ownership": ownership,
                },
            )
        )
    return out


report_sections.register(
    "components",
    Section(
        title="Component map and posture",
        summary="Each component's health, catalog facts and ownership findings.",
        collect=collect,
        order=10,
    ),
)
