"""Git subprocess wrappers for ComCan.

All subprocess calls go through the security layer to ensure only ``git``
is ever invoked, with no ``shell=True`` and no user-controlled command parts.
"""

from __future__ import annotations

import os
import platform
import stat
import subprocess
from pathlib import Path
from typing import Optional

from comcan.security import validate_subprocess_command, validate_write_path


class GitError(Exception):
    """Raised when a Git operation fails."""


def _run_git(
    *args: str,
    cwd: Optional[Path] = None,
    check: bool = True,
) -> str:
    """Run a git command and return stdout.

    Args:
        *args: Git subcommand and arguments (e.g. ``"log", "-n", "3"``).
        cwd: Working directory for the command.
        check: Whether to raise on non-zero exit code.

    Returns:
        Stripped stdout output.

    Raises:
        GitError: If the command fails and check is True.
    """
    cmd = ["git", *args]
    validate_subprocess_command(cmd)

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
            timeout=30,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitError(
            f"Git command failed: {' '.join(cmd)}\n"
            f"stderr: {e.stderr.strip()}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise GitError(f"Git command timed out: {' '.join(cmd)}") from e


def is_git_repo(path: Optional[Path] = None) -> bool:
    """Check whether a path is inside a Git repository.

    Args:
        path: Directory to check (defaults to CWD).

    Returns:
        True if the path is inside a Git repo.
    """
    try:
        _run_git(
            "rev-parse", "--is-inside-work-tree",
            cwd=path,
            check=True,
        )
        return True
    except (GitError, FileNotFoundError):
        return False


def get_repo_root(path: Optional[Path] = None) -> Path:
    """Return the root directory of the Git repository.

    Args:
        path: A directory inside the repo (defaults to CWD).

    Returns:
        Absolute path to the repo root.

    Raises:
        GitError: If not inside a Git repo.
    """
    output = _run_git("rev-parse", "--show-toplevel", cwd=path)
    return Path(output).resolve()


def get_current_branch(cwd: Optional[Path] = None) -> str:
    """Return the name of the current Git branch.

    Args:
        cwd: Working directory.

    Returns:
        Branch name (e.g. ``"main"``, ``"feature/auth"``).
    """
    return _run_git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)


def get_recent_commits(
    n: int = 10,
    cwd: Optional[Path] = None,
) -> str:
    """Return the last N commit summaries as one-liners.

    Args:
        n: Number of commits to retrieve.
        cwd: Working directory.

    Returns:
        Multi-line string of commit summaries.
    """
    return _run_git(
        "log", f"-n{n}", "--oneline", "--no-decorate",
        cwd=cwd,
    )


def get_changed_files(
    ref: str = "main",
    cwd: Optional[Path] = None,
) -> str:
    """Return a list of files changed compared to a reference branch.

    Args:
        ref: The branch/ref to compare against.
        cwd: Working directory.

    Returns:
        Newline-separated list of changed file paths.
    """
    try:
        return _run_git("diff", "--name-only", f"{ref}...HEAD", cwd=cwd)
    except GitError:
        # Fallback if ref doesn't exist (e.g. no 'main' branch)
        return _run_git("diff", "--name-only", "HEAD", cwd=cwd, check=False)


def get_diff_summary(
    ref: str = "main",
    cwd: Optional[Path] = None,
) -> str:
    """Return a short diff stat compared to a reference branch.

    Args:
        ref: The branch/ref to compare against.
        cwd: Working directory.

    Returns:
        Diff stat summary (files changed, insertions, deletions).
    """
    try:
        return _run_git("diff", "--stat", f"{ref}...HEAD", cwd=cwd)
    except GitError:
        return _run_git("diff", "--stat", "HEAD", cwd=cwd, check=False)


def install_hook(
    hook_name: str,
    script_content: str,
    repo_root: Path,
) -> Path:
    """Install a Git hook script.

    If a hook already exists and was NOT created by ComCan, it is backed up
    with a ``.bak`` suffix. If it was created by ComCan, it is overwritten.

    Args:
        hook_name: Hook name (e.g. ``"post-commit"``).
        script_content: The shell script to write.
        repo_root: Git repository root.

    Returns:
        Path to the installed hook.

    Raises:
        SecurityError: If the hook path is outside the repo.
    """
    hooks_dir = repo_root / ".git" / "hooks"
    hook_path = hooks_dir / hook_name

    # Security: verify path is inside repo
    validate_write_path(hook_path, repo_root)

    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Back up existing non-ComCan hooks
    comcan_marker = "# ComCan:"
    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8")
        if comcan_marker not in existing:
            backup = hook_path.with_suffix(f".{hook_name}.bak")
            backup.write_text(existing, encoding="utf-8")

    hook_path.write_text(script_content, encoding="utf-8")

    # Make executable on Unix-like systems
    if platform.system() != "Windows":
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)

    return hook_path
