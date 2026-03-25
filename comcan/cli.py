"""ComCan CLI -- friendly command-line interface for context management.

Built with Typer + Rich for beautiful terminal output.
"""

from __future__ import annotations

import importlib.resources
import platform
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from comcan import __version__
from comcan.config import ComCanConfig, load_config, save_config
from comcan.context_budget import PROFILES
from comcan.expertise_manager import (
    CLASSIFICATIONS,
    RECORD_TYPES,
    add_domain,
    delete,
    list_domains,
    prime,
    query,
    query_all,
    record,
    search,
    generate_manifesto,
    import_from_branch,
)
from comcan.bootstrap import scrape_repo
from comcan.git_utils import (
    GitError,
    get_current_branch,
    get_recent_commits,
    get_repo_root,
    install_hook,
    is_git_repo,
)
from comcan.security import audit_report
from comcan.state_manager import write_state

app = typer.Typer(
    name="comcan",
    help="ComCan -- Context Manager for AI Coding Agents",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console(highlight=False)

# ── Helpers ─────────────────────────────────────────────────────────────────


def _get_repo_root_or_exit() -> Path:
    """Get the Git repo root or exit with an error."""
    if not is_git_repo():
        console.print(
            "[bold red]Error:[/] Not inside a Git repository. "
            "Run this command from within a Git repo.",
        )
        raise typer.Exit(1)
    return get_repo_root()


def _load_template(name: str) -> str:
    """Load a template file from the templates directory."""
    templates_dir = Path(__file__).parent / "templates"
    template_path = templates_dir / name
    return template_path.read_text(encoding="utf-8")


# ── Commands ────────────────────────────────────────────────────────────────


@app.command()
def init(
    yes: bool = typer.Option(False, "--yes", "-y", help="Non-interactive mode with defaults"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing ComCan setup"),
) -> None:
    """Initialize ComCan in the current Git repository.

    Creates .comcan/ directory, installs Git hooks, writes .cursorrules,
    and generates the initial CURRENT_STATE.md.
    """
    repo_root = _get_repo_root_or_exit()
    comcan_dir = repo_root / ".comcan"

    if comcan_dir.exists() and not force:
        console.print(
            "[yellow]ComCan is already initialized.[/] "
            "Use [bold]--force[/] to reinitialize."
        )
        raise typer.Exit(0)

    console.print(Panel(
        "[bold cyan]ComCan Setup Wizard[/]\n"
        "Setting up context management for AI coding agents.",
        title="ComCan",
    ))

    # ── Gather configuration ────────────────────────────────────────────

    if yes:
        base_branch = "main"
        budget_profile = "large"
        domains: list[str] = []
    else:
        base_branch = typer.prompt(
            "Base branch (for diff comparisons)",
            default="main",
        )
        console.print("\n[dim]Budget profiles control how much context ComCan generates:[/]")
        for name, profile in PROFILES.items():
            console.print(f"  [cyan]{name:10}[/] -- {profile.description}")
        budget_profile = typer.prompt(
            "\nBudget profile",
            default="large",
        )
        console.print(
            "\n[dim]Domains are areas of your codebase (e.g., database, api, frontend).[/]"
            "\n[dim]You can add more later with [bold]comcan add <domain>[/bold].[/]"
        )
        domains_input = typer.prompt(
            "Initial domains (comma-separated, or Enter to skip)",
            default="",
        )
        domains = [
            d.strip() for d in domains_input.split(",") if d.strip()
        ]

    # ── Create config ───────────────────────────────────────────────────

    config = ComCanConfig(
        base_branch=base_branch,
        budget_profile=budget_profile,
        domains=domains,
    )

    comcan_dir.mkdir(parents=True, exist_ok=True)
    save_config(repo_root, config)
    console.print("  [green]+[/] Created .comcan/comcan.config.yaml")

    # ── Create expertise directories ────────────────────────────────────

    expertise_dir = comcan_dir / "expertise"
    expertise_dir.mkdir(exist_ok=True)
    for domain in domains:
        add_domain(repo_root, domain)
    if domains:
        console.print(f"  [green]+[/] Created domains: {', '.join(domains)}")

    # ── Install Git hooks ───────────────────────────────────────────────

    for hook_name in ("post-commit", "post-checkout"):
        hook_content = _load_template(hook_name)

        # On Windows, adjust the hook to use `start /b` for background
        if platform.system() == "Windows":
            hook_content = hook_content.replace(
                "comcan sync --quiet &",
                "start /b comcan sync --quiet",
            )

        install_hook(hook_name, hook_content, repo_root)
        console.print(f"  [green]+[/] Installed .git/hooks/{hook_name}")

    # ── Write .cursorrules ──────────────────────────────────────────────

    cursorrules_path = repo_root / ".cursorrules"
    cursorrules_content = _load_template("cursorrules.md")
    cursorrules_path.write_text(cursorrules_content, encoding="utf-8")
    console.print("  [green]+[/] Created .cursorrules")

    # ── Write Native AI Skill files ─────────────────────────────────────

    cursor_rules_dir = repo_root / ".cursor" / "rules"
    cursor_rules_dir.mkdir(parents=True, exist_ok=True)
    mdc_path = cursor_rules_dir / "comcan.mdc"
    mdc_path.write_text(_load_template("comcan.mdc"), encoding="utf-8")
    console.print("  [green]+[/] Created .cursor/rules/comcan.mdc")

    skill_path = comcan_dir / "comcan-skill.md"
    skill_path.write_text(_load_template("comcan-skill.md"), encoding="utf-8")
    console.print("  [green]+[/] Created .comcan/comcan-skill.md")

    antigravity_dir = repo_root / ".agents" / "skills" / "comcan"
    antigravity_dir.mkdir(parents=True, exist_ok=True)
    antigravity_path = antigravity_dir / "SKILL.md"
    antigravity_path.write_text(_load_template("antigravity_skill.md"), encoding="utf-8")
    console.print("  [green]+[/] Created .agents/skills/comcan/SKILL.md (Antigravity)")

    # ── Generate initial state ──────────────────────────────────────────

    try:
        write_state(repo_root)
        console.print("  [green]+[/] Generated .comcan/CURRENT_STATE.md")
    except GitError:
        console.print(
            "  [yellow]![/] Could not generate state (no commits yet?). "
            "Will auto-generate on first commit."
        )

    # ── Setup .gitattributes for merge=union on JSONL ───────────────────

    gitattributes = repo_root / ".gitattributes"
    merge_rule = ".comcan/expertise/*.jsonl merge=union\n"
    if gitattributes.exists():
        existing = gitattributes.read_text(encoding="utf-8")
        if merge_rule.strip() not in existing:
            with open(gitattributes, "a", encoding="utf-8") as f:
                f.write("\n" + merge_rule)
    else:
        gitattributes.write_text(merge_rule, encoding="utf-8")
    console.print("  [green]+[/] Configured .gitattributes (merge=union for JSONL)")

    console.print(Panel(
        "[bold green]ComCan initialized![/]\n\n"
        "Next steps:\n"
        "  - [cyan]comcan learn <domain> \"lesson\"[/] -- record expertise\n"
        "  - [cyan]comcan status[/] -- view current context\n"
        "  - [cyan]comcan query <domain>[/] -- view domain expertise\n"
        "  - Commit code and watch .comcan/CURRENT_STATE.md auto-update!",
        title="Setup Complete",
    ))


@app.command()
def sync(
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output"),
) -> None:
    """Regenerate CURRENT_STATE.md with latest Git info."""
    repo_root = _get_repo_root_or_exit()

    try:
        state_path = write_state(repo_root)
        if not quiet:
            console.print(f"[green]+[/] State synced -> {state_path.relative_to(repo_root)}")
    except GitError as e:
        if not quiet:
            console.print(f"[red]Error syncing state:[/] {e}")
        raise typer.Exit(1)


@app.command("add")
def add_cmd(
    domain: str = typer.Argument(help="Domain name (e.g., database, api, frontend)"),
) -> None:
    """Register a new expertise domain."""
    repo_root = _get_repo_root_or_exit()
    config = load_config(repo_root)

    path = add_domain(repo_root, domain)

    if domain not in config.domains:
        config.domains.append(domain)
        save_config(repo_root, config)

    console.print(f"[green]+[/] Domain [bold]{domain}[/] ready -> {path.name}")


@app.command()
def learn(
    domain: str = typer.Argument(help="Domain name"),
    lesson: str = typer.Argument(help="What you learned"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
) -> None:
    """Quick-record a convention (most common action).

    Shortcut for: comcan record <domain> --type convention "lesson"
    """
    repo_root = _get_repo_root_or_exit()
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    entry = record(
        repo_root,
        domain=domain,
        record_type="convention",
        content=lesson,
        tags=tag_list,
    )
    console.print(
        f"[green]+[/] Recorded [bold]{entry.type}[/] in "
        f"[cyan]{domain}[/]: {lesson} [dim]({entry.id})[/]"
    )


@app.command("record")
def record_cmd(
    domain: str = typer.Argument(help="Domain name"),
    content: str = typer.Argument(help="Expertise content"),
    type: str = typer.Option("convention", "--type", "-t", help=f"Record type: {', '.join(sorted(RECORD_TYPES))}"),
    description: str = typer.Option("", "--description", "-d", help="Longer description"),
    resolution: str = typer.Option("", "--resolution", "-r", help="Resolution (for failures)"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    classification: str = typer.Option(
        "tactical", "--classification", "-c",
        help=f"Classification: {', '.join(sorted(CLASSIFICATIONS))}",
    ),
) -> None:
    """Record an expertise entry (full syntax)."""
    repo_root = _get_repo_root_or_exit()
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    try:
        entry = record(
            repo_root,
            domain=domain,
            record_type=type,
            content=content,
            description=description,
            resolution=resolution,
            tags=tag_list,
            classification=classification,
        )
        console.print(
            f"[green]+[/] Recorded [bold]{entry.type}[/] in "
            f"[cyan]{domain}[/]: {content} [dim]({entry.id})[/]"
        )
    except ValueError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command("query")
def query_cmd(
    domain: Optional[str] = typer.Argument(None, help="Domain to query (all if omitted)"),
    all_domains: bool = typer.Option(False, "--all", help="Show all domains"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """View expertise for a domain."""
    repo_root = _get_repo_root_or_exit()

    if domain:
        records = query(repo_root, domain)
        if not records:
            console.print(f"[dim]No records found for domain '{domain}'.[/]")
            return

        if json_output:
            import json
            console.print(json.dumps([r.to_dict() for r in records], indent=2))
            return

        table = Table(title=f"{domain.title()} Expertise ({len(records)} entries)")
        table.add_column("ID", style="dim", width=12)
        table.add_column("Type", style="cyan")
        table.add_column("Content")
        table.add_column("Tags", style="yellow")

        for rec in records:
            table.add_row(
                rec.id,
                rec.type,
                rec.content,
                ", ".join(rec.tags) if rec.tags else "",
            )
        console.print(table)
    else:
        all_records = query_all(repo_root)
        if not any(all_records.values()):
            console.print("[dim]No expertise recorded yet. Use [bold]comcan learn[/bold] to start.[/]")
            return

        for dom, records in sorted(all_records.items()):
            if records:
                console.print(f"\n[bold cyan]{dom.title()}[/] ({len(records)} entries)")
                for rec in records:
                    console.print(f"  - [dim]{rec.type}[/] {rec.content}")


@app.command("search")
def search_cmd(
    query_text: str = typer.Argument(help="Text to search for"),
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Restrict to domain"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Search across all expertise records."""
    repo_root = _get_repo_root_or_exit()
    results = search(repo_root, query_text, domain=domain)

    if not results:
        console.print(f"[dim]No results for '{query_text}'.[/]")
        return

    if json_output:
        import json
        console.print(json.dumps([r.to_dict() for r in results], indent=2))
        return

    console.print(f"[bold]Found {len(results)} result(s) for[/] '{query_text}':\n")
    for rec in results:
        console.print(
            f"  [{rec.domain}] [cyan]{rec.type}[/]: {rec.content}"
        )
        if rec.resolution:
            console.print(f"    -> {rec.resolution}")


@app.command("prime")
def prime_cmd(
    domains: Optional[list[str]] = typer.Argument(None, help="Domains to include"),
    budget: Optional[int] = typer.Option(None, "--budget", "-b", help="Token budget"),
) -> None:
    """Output full context for agent injection.

    Designed for piping into AI agent workflows.
    """
    repo_root = _get_repo_root_or_exit()
    output = prime(repo_root, domains=domains or None, budget=budget)
    console.print(output)


@app.command()
def status() -> None:
    """Show a dashboard of current context state."""
    repo_root = _get_repo_root_or_exit()
    config = load_config(repo_root)

    try:
        branch = get_current_branch(cwd=repo_root)
    except GitError:
        branch = "unknown"

    try:
        commits = get_recent_commits(n=3, cwd=repo_root)
    except GitError:
        commits = "(no commits)"

    domains = list_domains(repo_root)
    state_file = repo_root / ".comcan" / "CURRENT_STATE.md"

    # ── Dashboard ───────────────────────────────────────────────────────

    console.print(Panel(
        f"[bold]Branch:[/] [cyan]{branch}[/]\n"
        f"[bold]Profile:[/] {config.budget_profile}\n"
        f"[bold]Base:[/] {config.base_branch}\n"
        f"[bold]State:[/] {'[green]synced[/]' if state_file.exists() else '[yellow]not synced[/]'}",
        title="ComCan Status",
    ))

    if commits and commits != "(no commits)":
        console.print("[bold]Recent Commits:[/]")
        for line in commits.split("\n")[:3]:
            console.print(f"  [dim]{line}[/]")
        console.print()

    if domains:
        table = Table(title="Expertise Domains")
        table.add_column("Domain", style="cyan")
        table.add_column("Records", justify="right")

        for domain in domains:
            records = query(repo_root, domain)
            table.add_row(domain, str(len(records)))

        console.print(table)
    else:
        console.print("[dim]No domains registered. Use [bold]comcan add <domain>[/bold].[/]")


@app.command()
def forget(
    domain: str = typer.Argument(help="Domain name"),
    record_id: str = typer.Argument(help="Record ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Remove an expertise record."""
    repo_root = _get_repo_root_or_exit()

    if not yes:
        confirm = typer.confirm(f"Delete record {record_id} from {domain}?")
        if not confirm:
            raise typer.Abort()

    if delete(repo_root, domain, record_id):
        console.print(f"[green]+[/] Deleted record [dim]{record_id}[/] from {domain}")
    else:
        console.print(f"[red]Record {record_id} not found in {domain}.[/]")
        raise typer.Exit(1)


@app.command()
def doctor() -> None:
    """Run health checks on your ComCan setup."""
    repo_root = _get_repo_root_or_exit()
    config = load_config(repo_root)

    console.print(Panel("[bold]ComCan Health Check[/]", title="Doctor"))

    all_ok = True

    # ── Check: .comcan directory exists ──────────────────────────────────

    comcan_dir = repo_root / ".comcan"
    if comcan_dir.exists():
        console.print("  [green]+[/] .comcan/ directory exists")
    else:
        console.print("  [red]x[/] .comcan/ directory missing -- run [bold]comcan init[/]")
        all_ok = False

    # ── Check: config file ──────────────────────────────────────────────

    config_path = repo_root / ".comcan" / "comcan.config.yaml"
    if config_path.exists():
        console.print("  [green]+[/] Config file found")
    else:
        console.print("  [red]x[/] Config file missing")
        all_ok = False

    # ── Check: Git hooks ────────────────────────────────────────────────

    for hook in ("post-commit", "post-checkout"):
        hook_path = repo_root / ".git" / "hooks" / hook
        if hook_path.exists():
            content = hook_path.read_text(encoding="utf-8")
            if "ComCan" in content:
                console.print(f"  [green]+[/] Git hook: {hook}")
            else:
                console.print(
                    f"  [yellow]![/] Git hook {hook} exists but wasn't installed by ComCan"
                )
        else:
            console.print(f"  [red]x[/] Git hook missing: {hook}")
            all_ok = False

    # ── Check: .cursorrules and AI Skills ───────────────────────────────

    cursorrules = repo_root / ".cursorrules"
    if cursorrules.exists():
        console.print("  [green]+[/] .cursorrules file found")
    else:
        console.print("  [red]x[/] .cursorrules file missing")
        all_ok = False
        
    mdc_file = repo_root / ".cursor" / "rules" / "comcan.mdc"
    if mdc_file.exists():
        console.print("  [green]+[/] .cursor/rules/comcan.mdc found")
    else:
        console.print("  [yellow]![/] .cursor/rules/comcan.mdc missing")

    skill_file = repo_root / ".comcan" / "comcan-skill.md"
    if skill_file.exists():
        console.print("  [green]+[/] .comcan/comcan-skill.md found")
    else:
        console.print("  [yellow]![/] .comcan/comcan-skill.md missing")

    # ── Check: state file ───────────────────────────────────────────────

    state_file = repo_root / ".comcan" / "CURRENT_STATE.md"
    if state_file.exists():
        console.print("  [green]+[/] CURRENT_STATE.md exists")
    else:
        console.print("  [yellow]![/] CURRENT_STATE.md not generated yet")

    # ── Security audit ──────────────────────────────────────────────────

    console.print("\n[bold]Security Audit:[/]")
    report = audit_report(repo_root)
    for check_name, info in report.items():
        icon = "[green]+[/]" if info["pass"] else "[red]x[/]"
        console.print(f"  {icon} {info['description']}")
        if not info["pass"]:
            all_ok = False

    # ── Summary ─────────────────────────────────────────────────────────

    if all_ok:
        console.print("\n[bold green]All checks passed![/]")
    else:
        console.print("\n[bold yellow]Some checks failed.[/] Run [bold]comcan init[/] to fix.")


@app.command()
def version() -> None:
    """Show ComCan version."""
    console.print(f"ComCan v{__version__}")


# ── Entry point ─────────────────────────────────────────────────────────────

@app.command()
def manifesto(
    output: str = typer.Option("ARCHITECTURE_MANIFESTO.md", "--output", "-o", help="Output file name"),
) -> None:
    """Generate a high-level human-readable Architecture Manifesto."""
    repo_root = _get_repo_root_or_exit()
    
    content = generate_manifesto(repo_root)
    output_path = repo_root / output
    
    output_path.write_text(content, encoding="utf-8")
    console.print(f"[green]+[/] Architecture Manifesto generated -> {output}")
    console.print(f"[dim]View it at: {output_path.absolute()}[/]")


@app.command()
def bridge(
    branch: str = typer.Argument(help="The branch to pull expertise from"),
) -> None:
    """Import expertise records from another branch (Cross-Pollination)."""
    repo_root = _get_repo_root_or_exit()
    
    console.print(f"[cyan]Teleporting wisdom from branch [bold]{branch}[/]...[/]")
    
    stats = import_from_branch(repo_root, branch)
    
    if not stats:
        console.print("[dim]No new expertise found on that branch.[/]")
        return
        
    table = Table(title="Imported Expertise")
    table.add_column("Domain", style="cyan")
    table.add_column("New Records", justify="right")
    
    for domain, count in stats.items():
        table.add_row(domain, str(count))
        
    console.print(table)
    console.print("[green]Brain expansion complete![/]")


@app.command()
def bootstrap(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-scrape even if manifesto exists"),
) -> None:
    """Scrape the repository to autonomously build the initial 'Main Brain'."""
    repo_root = _get_repo_root_or_exit()
    
    console.print(Panel(
        "[bold cyan]Repo Bootstrap Wizard[/]\n"
        "Scraping repository structure to generate initial expertise...",
        title="ComCan",
    ))
    
    result = scrape_repo(repo_root, skip_if_exists=not force)
    
    if "Existing Manifesto Detected" in result['tech_stack']:
        console.print("[yellow]![/] ARCHITECTURE_MANIFESTO.md already exists.")
        console.print("    Skipping redundant scrape for efficiency.")
        console.print("    Use [bold]comcan manifesto[/] to refresh it from expertise,")
        console.print("    or use [bold]comcan bootstrap --force[/] to re-scrape.")
        return
    
    console.print(f"[bold]Detected Tech Stack:[/] {', '.join(result['tech_stack'])}")
    console.print(f"[bold]Suggested Domains:[/] {', '.join(result['domains'])}")
    
    if not result['suggested_records']:
        console.print("[dim]No specific patterns detected, but ready to start learning![/]")
    else:
        console.print(f"\n[bold]Suggested Rules ({len(result['suggested_records'])}):[/]")
        for rec in result['suggested_records']:
            console.print(f"  - [{rec['domain']}] {rec['content']}")

    if not yes:
        confirm = typer.confirm("\nDo you want to apply these suggestions and generate the Manifesto?")
        if not confirm:
            console.print("[yellow]Bootstrap cancelled.[/]")
            raise typer.Exit(0)

    # Apply suggestions
    for dom in result['domains']:
        add_domain(repo_root, dom)
        
    for rec in result['suggested_records']:
        record(
            repo_root,
            domain=rec['domain'],
            record_type=rec['type'],
            content=rec['content'],
            author="comcan-bootstrap",
        )
        
    # Generate manifesto
    content = generate_manifesto(repo_root)
    (repo_root / "ARCHITECTURE_MANIFESTO.md").write_text(content, encoding="utf-8")
    
    console.print("\n[green]Success![/] Main Brain bootstrapped.")
    console.print("  [green]+[/] Created Domains")
    console.print("  [green]+[/] Recorded Initial Expertise")
    console.print("  [green]+[/] Generated ARCHITECTURE_MANIFESTO.md")
    console.print("\n[cyan]Next step: Commit these changes to share the brain with the team![/]")


if __name__ == "__main__":
    app()
