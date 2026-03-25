"""Repository bootstrapping and scraping logic.

Enables ComCan to 'self-onboard' into a repository by scanning for 
common patterns, languages, and directory structures.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

from comcan.file_parser import get_repo_tree
from comcan.expertise_manager import RECORD_TYPES


class BootstrapResult(TypedDict):
    """Result of a repository bootstrap scan."""
    domains: list[str]
    suggested_records: list[dict[str, str]]
    tech_stack: list[str]


def scrape_repo(repo_root: Path, skip_if_exists: bool = True) -> BootstrapResult:
    """Scann the repository to suggest domains and initial expertise.

    Args:
        repo_root: Git repository root.
        skip_if_exists: If True, returns minimal result if manifesto exists.

    Returns:
        BootstrapResult with suggested domains/records.
    """
    manifesto_path = repo_root / "ARCHITECTURE_MANIFESTO.md"
    if skip_if_exists and manifesto_path.exists():
        # Minimal result if brain already exists
        return {
            "domains": [],
            "suggested_records": [],
            "tech_stack": ["Existing Manifesto Detected"],
        }
    domains: set[str] = set()
    records: list[dict[str, str]] = []
    tech_stack: set[str] = set()

    # 1. Detect common directories
    dirs = {d.name for d in repo_root.iterdir() if d.is_dir() and not d.name.startswith(".")}
    
    mapping = {
        "api": "api",
        "backend": "api",
        "server": "api",
        "src/api": "api",
        "frontend": "frontend",
        "client": "frontend",
        "ui": "frontend",
        "web": "frontend",
        "db": "database",
        "database": "database",
        "models": "database",
        "schema": "database",
        "tests": "testing",
        "spec": "testing",
        "docs": "documentation",
        "ci": "devops",
        "scripts": "tooling",
    }

    for path_fragment, domain in mapping.items():
        if (repo_root / path_fragment).exists():
            domains.add(domain)

    # 2. Detect Tech Stack
    files = {f.name for f in repo_root.iterdir() if f.is_file()}
    
    if "package.json" in files: tech_stack.add("Node.js")
    if "requirements.txt" in files or "pyproject.toml" in files: tech_stack.add("Python")
    if "go.mod" in files: tech_stack.add("Go")
    if "Cargo.toml" in files: tech_stack.add("Rust")
    if "Dockerfile" in files: tech_stack.add("Docker")
    if "Makefile" in files: tech_stack.add("Make")

    # 3. Suggest initial records based on tech stack
    if "Python" in tech_stack:
        records.append({
            "domain": "tooling",
            "type": "convention",
            "content": "Follow PEP 8 style guidelines for Python code.",
        })
    if "Node.js" in tech_stack:
        records.append({
            "domain": "tooling",
            "type": "convention",
            "content": "Use 'npm run' scripts for common development tasks.",
        })
    if "Docker" in tech_stack:
        records.append({
            "domain": "devops",
            "type": "pattern",
            "content": "Use multi-stage Docker builds to keep images small.",
        })

    # 4. Fallback if no domains found
    if not domains:
        domains.add("core")

    return {
        "domains": sorted(list(domains)),
        "suggested_records": records,
        "tech_stack": sorted(list(tech_stack)),
    }
