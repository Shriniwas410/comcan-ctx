"""Smart directory tree generator for large codebases.

Generates a Unix ``tree``-like output while respecting ``.gitignore``,
token budgets, and adaptive depth/collapse rules to avoid overwhelming
LLM context windows.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pathspec

from comcan.context_budget import ContextBudget


# Directories always excluded regardless of .gitignore
_HARDCODED_EXCLUDES = {
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".next",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    ".eggs",
    "*.egg-info",
    ".comcan",
}

# File extensions always excluded
_EXCLUDED_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dll", ".dylib",
    ".class", ".o", ".obj",
}

# Threshold: directories with more children than this get collapsed
_COLLAPSE_THRESHOLD = 30

# Connectors for tree drawing
_TEE = "├── "
_LAST = "└── "
_PIPE = "│   "
_SPACE = "    "


def _load_gitignore(root: Path) -> Optional[pathspec.PathSpec]:
    """Load and parse .gitignore from the given directory.

    Args:
        root: Directory to look for a .gitignore file in.

    Returns:
        A PathSpec matcher, or None if no .gitignore exists.
    """
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return None

    with open(gitignore_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def _should_exclude(
    name: str,
    rel_path: str,
    is_dir: bool,
    gitignore_spec: Optional[pathspec.PathSpec],
    extra_ignores_spec: Optional[pathspec.PathSpec],
) -> bool:
    """Check if a file/directory should be excluded from the tree.

    Args:
        name: The file or directory basename.
        rel_path: Path relative to the repo root.
        is_dir: Whether this entry is a directory.
        gitignore_spec: Parsed .gitignore rules.
        extra_ignores_spec: Additional ignore patterns from config.

    Returns:
        True if the entry should be excluded.
    """
    # Hardcoded excludes
    if name in _HARDCODED_EXCLUDES:
        return True

    # Match against hardcoded wildcard patterns
    for pattern in _HARDCODED_EXCLUDES:
        if "*" in pattern:
            import fnmatch
            if fnmatch.fnmatch(name, pattern):
                return True

    # Extension excludes (files only)
    if not is_dir:
        suffix = Path(name).suffix.lower()
        if suffix in _EXCLUDED_EXTENSIONS:
            return True

    # .gitignore rules
    check_path = rel_path + "/" if is_dir else rel_path
    if gitignore_spec and gitignore_spec.match_file(check_path):
        return True

    # Extra ignore patterns from config
    if extra_ignores_spec and extra_ignores_spec.match_file(check_path):
        return True

    return False


def _annotate_file(name: str) -> str:
    """Add a type annotation tag to a filename for agent comprehension.

    Args:
        name: The filename.

    Returns:
        Annotated filename (e.g., ``"conftest.py [test]"``).
    """
    lower = name.lower()

    # Config files
    config_names = {
        "pyproject.toml", "setup.cfg", "setup.py", "package.json",
        "tsconfig.json", "webpack.config.js", "vite.config.ts",
        ".env.example", "docker-compose.yml", "dockerfile",
        "makefile", ".eslintrc.js", ".prettierrc",
    }
    if lower in config_names or lower.startswith(".") and "rc" in lower:
        return f"{name} [config]"

    # Test files
    if lower.startswith("test_") or lower.endswith("_test.py"):
        return f"{name} [test]"
    if lower == "conftest.py":
        return f"{name} [test]"

    # Docs
    if lower in {"readme.md", "contributing.md", "changelog.md", "license"}:
        return f"{name} [doc]"

    return name


def _build_tree(
    current_dir: Path,
    repo_root: Path,
    prefix: str,
    depth: int,
    max_depth: int,
    gitignore_spec: Optional[pathspec.PathSpec],
    extra_ignores_spec: Optional[pathspec.PathSpec],
) -> list[str]:
    """Recursively build the tree lines.

    Args:
        current_dir: The directory being traversed.
        repo_root: The repo root (for relative paths).
        prefix: The visual prefix for tree indentation.
        depth: Current depth level.
        max_depth: Maximum depth to traverse.
        gitignore_spec: Parsed .gitignore rules.
        extra_ignores_spec: Additional ignore patterns.

    Returns:
        List of tree lines.
    """
    if depth > max_depth:
        return []

    lines: list[str] = []

    try:
        entries = sorted(
            os.scandir(current_dir),
            key=lambda e: (not e.is_dir(), e.name.lower()),
        )
    except PermissionError:
        return [f"{prefix}[permission denied]"]

    # Filter entries
    visible: list[os.DirEntry] = []
    for entry in entries:
        rel = os.path.relpath(entry.path, repo_root).replace("\\", "/")
        if not _should_exclude(
            entry.name, rel, entry.is_dir(),
            gitignore_spec, extra_ignores_spec,
        ):
            visible.append(entry)

    # Collapse large directories
    if len(visible) > _COLLAPSE_THRESHOLD:
        dir_count = sum(1 for e in visible if e.is_dir())
        file_count = len(visible) - dir_count
        lines.append(
            f"{prefix}[... {file_count} files, {dir_count} dirs omitted]"
        )
        return lines

    for i, entry in enumerate(visible):
        is_last = i == len(visible) - 1
        connector = _LAST if is_last else _TEE

        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            extension = _SPACE if is_last else _PIPE
            lines.extend(
                _build_tree(
                    Path(entry.path),
                    repo_root,
                    prefix + extension,
                    depth + 1,
                    max_depth,
                    gitignore_spec,
                    extra_ignores_spec,
                )
            )
        else:
            annotated = _annotate_file(entry.name)
            lines.append(f"{prefix}{connector}{annotated}")

    return lines


def generate_tree(
    root: Path,
    max_depth: int = 4,
    token_budget: int = 8000,
    extra_ignores: Optional[list[str]] = None,
) -> str:
    """Generate a token-budget-aware directory tree.

    Starts at the given depth and adaptively reduces until the output
    fits within the token budget.

    Args:
        root: The repository root directory.
        max_depth: Starting maximum depth (will be reduced if needed).
        token_budget: Maximum token count for the tree output.
        extra_ignores: Additional glob patterns to ignore.

    Returns:
        A string containing the tree visualization.
    """
    root = root.resolve()

    # Load .gitignore
    gitignore_spec = _load_gitignore(root)

    # Load extra ignores
    extra_spec = None
    if extra_ignores:
        extra_spec = pathspec.PathSpec.from_lines("gitwildmatch", extra_ignores)

    budget = ContextBudget("large")

    # Adaptively reduce depth until tree fits the budget
    for depth in range(max_depth, 0, -1):
        lines = [f"{root.name}/"]
        lines.extend(
            _build_tree(
                root, root, "", 1, depth,
                gitignore_spec, extra_spec,
            )
        )
        tree_str = "\n".join(lines)

        if budget.fits_budget(tree_str, token_budget):
            return tree_str

    # Even depth=1 doesn't fit → truncate
    lines = [f"{root.name}/"]
    lines.extend(
        _build_tree(root, root, "", 1, 1, gitignore_spec, extra_spec)
    )
    tree_str = "\n".join(lines)
    return budget.truncate_smart(tree_str, token_budget, preserve_start=True)
