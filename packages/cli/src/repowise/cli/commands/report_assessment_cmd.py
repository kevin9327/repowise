"""``repowise report assessment`` - the assessment pack for a repo or workspace.

Reads the index only (no LLM, no network, no writes) and prints or writes one
document: JSON (canonical), Markdown or self-contained HTML. In a workspace it
covers every repo, or the one ``--repo`` names.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from repowise.cli.helpers import (
    err_console,
    repo_index_session,
    resolve_command_target,
    run_async,
    silence_logs_for_machine_output_until_close,
)


def _targets(target: Any) -> list[tuple[str | None, Path]]:
    """``(alias, path)`` per repository the report covers."""
    if not target.is_workspace:
        return [(None, Path(target.repo_path).resolve())]
    if target.repo_filter is not None:
        return [(target.repo_filter, target.single_repo_path())]
    return [(r.alias, (target.ws_root / r.path).resolve()) for r in target.ws_config.repos]


async def _build(repos: list[tuple[str | None, Path]], sections: list, scope: dict) -> dict:
    from repowise.core.persistence.models import Repository
    from repowise.core.report.build import assemble, collect_repo
    from repowise.core.report.model import ReportContext

    parts = []
    for alias, root in repos:
        async with repo_index_session(root) as opened:
            if opened is None:
                if scope["kind"] == "repo":
                    raise click.ClickException(
                        f"No index for {root}. Run `repowise init` there first."
                    )
                entry = {"alias": alias, "name": root.name, "indexed": False}
                parts.append((entry, []))
                continue
            session, repo_id = opened
            repo = await session.get(Repository, repo_id)
            ctx = ReportContext(
                session, repo_id, root, alias=alias, head_commit=repo.head_commit if repo else None
            )
            parts.append(await collect_repo(ctx, sections))
    return assemble(scope, parts)


@click.command("assessment")
@click.argument("path", required=False, type=click.Path(exists=True, file_okay=False))
@click.option("--sections", "wanted", default=None, help="Comma-separated section ids.")
@click.option(
    "--format",
    "fmt",
    default="markdown",
    show_default=True,
    help="Renderer: json, markdown or html (or one a plugin registers).",
)
@click.option("--out", "out_path", type=click.Path(dir_okay=False), help="Write to this file.")
@click.option("--workspace", "workspace_flag", is_flag=True, help="Cover every workspace repo.")
@click.option("--no-workspace", is_flag=True, help="Force single-repo mode.")
@click.option("--repo", "repo_alias", default=None, help="Workspace repo alias to cover.")
def assessment_command(
    path: str | None,
    wanted: str | None,
    fmt: str,
    out_path: str | None,
    workspace_flag: bool,
    no_workspace: bool,
    repo_alias: str | None,
) -> None:
    """Assessment pack: components, hotspots, bus factor, dead code, test reach,
    contracts, decisions, provenance and the quarter's moves, each with its basis."""
    from repowise.core.report.build import available_sections
    from repowise.core.report.render import report_renderers

    if not out_path:
        silence_logs_for_machine_output_until_close()  # stdout carries only the report
    sections = available_sections()
    if wanted:
        names = [n.strip() for n in wanted.split(",") if n.strip()]
        known = dict(sections)
        unknown = [n for n in names if n not in known]
        if unknown:
            raise click.BadParameter(
                f"unknown section(s) {', '.join(unknown)}; available: {', '.join(known)}",
                param_hint="--sections",
            )
        sections = [(n, s) for n, s in sections if n in names]
    if fmt not in report_renderers.names:
        raise click.BadParameter(
            f"unknown format {fmt!r}; available: {', '.join(report_renderers.names)}",
            param_hint="--format",
        )

    target = resolve_command_target(
        path=path,
        workspace_flag=workspace_flag,
        no_workspace_flag=no_workspace,
        repo_alias=repo_alias,
    )
    target.notice(err_console, command="report assessment")
    repos = _targets(target)
    if target.is_workspace and target.repo_filter is None:
        scope = {"kind": "workspace", "name": target.ws_root.name}
    else:
        scope = {"kind": "repo", "name": repos[0][1].name}
    document = run_async(_build(repos, sections, scope))
    text = report_renderers.get(fmt)(document)
    if out_path:
        Path(out_path).write_text(text, encoding="utf-8", newline="\n")
        err_console.print(f"Wrote {fmt} report to {out_path}")
    else:
        click.echo(text, nl=False)
