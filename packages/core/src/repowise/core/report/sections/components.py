"""Component map and posture: each component's health, catalog facts and
ownership findings, from the component rollups and ownership checks."""

from __future__ import annotations

from typing import Any

from repowise.core.report.model import (
    ReportContext,
    Section,
    check,
    component_summary,
    report_sections,
)

_OWNERSHIP_METHOD = (
    "declared owners (catalog spec.owner, CODEOWNERS, teams.yaml) against indexed "
    "commits in the 90 days before the newest one"
)


def _map_item(found: Any, comps: list, directory_issues: list[str]) -> dict[str, Any]:
    """The component map: how many components, where they came from, catalog problems."""
    declared = sum(1 for c, _ in comps if c.declared)
    catalog = found.catalog
    return check(
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


def _gated_item(rollups: dict) -> dict[str, Any] | None:
    gated = ((rollups.get(None) or {}).get("health") or {}).get("gated_files")
    if not gated:
        return None
    return check(
        "health:gated",
        reason=f"{gated} file(s) in languages health is held back on carry no score here",
        method="the language gates every health surface applies",
        basis="gated",
        data={"gated_files": gated},
    )


def _posture(health: dict[str, Any]) -> tuple[str, float | None, str]:
    """``(basis, score, posture text)`` of one component's health rollup."""
    if health.get("basis") == "measured":
        posture = f"health {health['average']} over {health['scored_files']} scored file(s)"
        return "measured", health["average"], posture
    basis = "gated" if health.get("gated_files") else "unresolved"
    return basis, None, health.get("reason", "no health score")


def _outcome(findings: list, basis: str) -> str:
    if findings:
        return "ownership findings"
    return {"gated": "health gated", "unresolved": "no health score"}.get(basis, "nothing to note")


def _component_item(
    comp: Any, paths: list[str], figures: dict[str, Any], posture: tuple
) -> dict[str, Any]:
    basis, score, text = posture
    findings = figures["ownership"].get("findings", [])
    group = figures["owning_team"]
    source = f"declared in {comp.declared_in}" if comp.declared else f"derived ({comp.source})"
    details = [
        source,
        *([f"criticality: {comp.criticality}"] if comp.criticality else []),
        *([f"tags: {', '.join(comp.tags)}"] if comp.tags else []),
        *([f"owning team: {group}"] if group else []),
        *(f"{f['kind']}: {f['message']}" for f in findings),
    ]
    method = figures["health"].get("method", "file health scores")
    return check(
        f"component:{comp.name}",
        score=score,
        reason=f"{len(paths)} file(s); {text}; {len(findings)} ownership finding(s)",
        details=details,
        method=f"{method}; ownership: {_OWNERSHIP_METHOD}",
        basis=basis,
        data=figures,
    )


async def collect(ctx: ReportContext) -> list[dict[str, Any]]:
    from repowise.core.components.catalog import owner_group_name
    from repowise.core.components.store import component_ownership

    found = await ctx.components()
    rollups = await ctx.rollups()
    comps = [(c, found.resolved.files[c.name]) for c in found.resolved.components]
    blocks, directory_issues = await component_ownership(
        ctx.session,
        ctx.repository_id,
        ctx.repo_root,
        comps,
        {n: r["bus_factor"] for n, r in rollups.items() if n is not None},
    )
    out = [_map_item(found, comps, directory_issues)]
    gated = _gated_item(rollups)
    if gated:
        out.append(gated)

    figures: dict[str, dict[str, Any]] = {}
    outcomes = dict.fromkeys(
        ("ownership findings", "health gated", "no health score", "nothing to note"), 0
    )
    quiet: list[str] = []
    items: list[dict[str, Any]] = []
    for comp, paths in comps:
        health = rollups.get(comp.name, {}).get("health") or {"basis": "unavailable"}
        figures[comp.name] = {
            "source": comp.source,
            "criticality": comp.criticality,
            "tags": list(comp.tags),
            "owning_team": owner_group_name(comp.owner),
            "file_count": len(paths),
            "health": health,
            "ownership": blocks.get(comp.name, {}),
        }
        posture = _posture(health)
        outcome = _outcome(figures[comp.name]["ownership"].get("findings", []), posture[0])
        outcomes[outcome] += 1
        if outcome == "nothing to note":
            quiet.append(comp.name)
        else:
            items.append(_component_item(comp, paths, figures[comp.name], posture))
    out.append(
        component_summary(
            "components",
            outcomes=outcomes,
            quiet=quiet,
            method=f"file health scores per component; ownership: {_OWNERSHIP_METHOD}",
            basis="measured",
            data={"components": figures},
        )
    )
    return out + items


report_sections.register(
    "components",
    Section(
        title="Component map and posture",
        summary="Each component's health, catalog facts and ownership findings.",
        collect=collect,
        order=10,
    ),
)
