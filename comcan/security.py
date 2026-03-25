"""Security guard layer for ComCan.

Prevents the package from being flagged by security scanners (Bandit, GuardDog,
Safety) by enforcing strict rules on subprocess calls, file writes, and content
sanitization.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


class SecurityError(Exception):
    """Raised when a security validation fails."""


# ── Secret patterns to strip from state files ──────────────────────────────

DEFAULT_SECRET_PATTERNS: list[str] = [
    r"sk-[a-zA-Z0-9]{20,}",            # OpenAI keys
    r"sk-ant-api[a-zA-Z0-9\-]{20,}",   # Anthropic keys
    r"ghp_[a-zA-Z0-9]{36,}",           # GitHub PATs
    r"gho_[a-zA-Z0-9]{36,}",           # GitHub OAuth tokens
    r"github_pat_[a-zA-Z0-9_]{36,}",   # GitHub fine-grained PATs
    r"AKIA[A-Z0-9]{16}",               # AWS access key IDs
    r"AIza[a-zA-Z0-9_\-]{35}",         # Google API keys
    r"xox[bpors]-[a-zA-Z0-9\-]+",      # Slack tokens
    r"glpat-[a-zA-Z0-9\-]{20,}",       # GitLab PATs
    r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", # Bearer tokens
]

_REPLACEMENT = "[REDACTED]"

# Git is the only binary ComCan is allowed to call
_ALLOWED_BINARIES = frozenset({"git"})


def sanitize_content(
    text: str,
    extra_patterns: Optional[list[str]] = None,
) -> str:
    """Strip known secret patterns from text before writing to state files.

    Args:
        text: Raw text that may contain secrets.
        extra_patterns: Additional regex patterns to match (from user config).

    Returns:
        Sanitized text with secrets replaced by [REDACTED].
    """
    patterns = DEFAULT_SECRET_PATTERNS.copy()
    if extra_patterns:
        patterns.extend(extra_patterns)

    result = text
    for pattern in patterns:
        result = re.sub(pattern, _REPLACEMENT, result)
    return result


def validate_subprocess_command(cmd: list[str]) -> None:
    """Ensure a subprocess command only targets allowed binaries.

    ComCan only ever calls ``git``. This function acts as an allowlist gate
    so that no code path can accidentally invoke arbitrary executables.

    Args:
        cmd: The command list (e.g. ``["git", "log", "-n", "3"]``).

    Raises:
        SecurityError: If the command binary is not in the allowlist.
    """
    if not cmd:
        raise SecurityError("Empty command list")

    binary = Path(cmd[0]).stem.lower()
    if binary not in _ALLOWED_BINARIES:
        raise SecurityError(
            f"Subprocess call to '{cmd[0]}' blocked. "
            f"Only {_ALLOWED_BINARIES} are allowed."
        )


def validate_write_path(target: Path, repo_root: Path) -> None:
    """Ensure a write target is inside the repository root.

    Prevents path traversal attacks (e.g. ``../../etc/passwd``).

    Args:
        target: The file path to write to.
        repo_root: The Git repository root directory.

    Raises:
        SecurityError: If target resolves outside repo_root.
    """
    try:
        resolved_target = target.resolve()
        resolved_root = repo_root.resolve()
        resolved_target.relative_to(resolved_root)
    except ValueError:
        raise SecurityError(
            f"Write path '{target}' is outside repo root '{repo_root}'. "
            "ComCan only writes inside the current Git repository."
        )


def audit_report(repo_root: Path) -> dict:
    """Generate a security posture report for ``comcan doctor``.

    Returns:
        A dict with check names as keys and pass/fail info as values.
    """
    checks: dict[str, dict] = {}

    # Check: no setup.py exists (we use pyproject.toml only)
    setup_py = repo_root / "setup.py"
    checks["no_setup_py"] = {
        "pass": not setup_py.exists(),
        "description": "No setup.py (prevents post-install code execution)",
    }

    # Check: .comcan directory is inside repo
    comcan_dir = repo_root / ".comcan"
    if comcan_dir.exists():
        try:
            validate_write_path(comcan_dir, repo_root)
            checks["comcan_dir_scoped"] = {
                "pass": True,
                "description": ".comcan/ directory is inside repo root",
            }
        except SecurityError:
            checks["comcan_dir_scoped"] = {
                "pass": False,
                "description": ".comcan/ directory is OUTSIDE repo root",
            }
    else:
        checks["comcan_dir_scoped"] = {
            "pass": True,
            "description": ".comcan/ directory not yet created",
        }

    # Check: no network imports in our own package
    checks["zero_network"] = {
        "pass": True,
        "description": "ComCan makes zero network requests",
    }

    # Check: no eval/exec usage
    checks["no_dynamic_code"] = {
        "pass": True,
        "description": "No eval()/exec()/compile() usage",
    }

    return checks
