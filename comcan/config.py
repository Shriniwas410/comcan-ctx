"""Configuration management for ComCan.

Loads and saves ``comcan.config.yaml`` from the ``.comcan/`` directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


_CONFIG_FILENAME = "comcan.config.yaml"

_DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "base_branch": "main",
    "budget_profile": "large",
    "custom_budget": None,
    "domains": [],
    "extra_ignores": [],
    "auto_sync": True,
    "secret_patterns": [],
}


@dataclass
class ComCanConfig:
    """Typed representation of a ComCan config file."""

    version: int = 1
    base_branch: str = "main"
    budget_profile: str = "large"
    custom_budget: Optional[int] = None
    domains: list[str] = field(default_factory=list)
    extra_ignores: list[str] = field(default_factory=list)
    auto_sync: bool = True
    secret_patterns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize config to a plain dict for YAML output."""
        return {
            "version": self.version,
            "base_branch": self.base_branch,
            "budget_profile": self.budget_profile,
            "custom_budget": self.custom_budget,
            "domains": self.domains,
            "extra_ignores": self.extra_ignores,
            "auto_sync": self.auto_sync,
            "secret_patterns": self.secret_patterns,
        }


def get_config_path(repo_root: Path) -> Path:
    """Return the path to the config file."""
    return repo_root / ".comcan" / _CONFIG_FILENAME


def load_config(repo_root: Path) -> ComCanConfig:
    """Load configuration from disk.

    Falls back to defaults if the config file does not exist.

    Args:
        repo_root: Git repository root directory.

    Returns:
        Parsed configuration.
    """
    config_path = get_config_path(repo_root)

    if not config_path.exists():
        return ComCanConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # Merge loaded values over defaults
    merged = {**_DEFAULT_CONFIG, **raw}

    return ComCanConfig(
        version=merged["version"],
        base_branch=merged["base_branch"],
        budget_profile=merged["budget_profile"],
        custom_budget=merged["custom_budget"],
        domains=merged["domains"] or [],
        extra_ignores=merged["extra_ignores"] or [],
        auto_sync=merged["auto_sync"],
        secret_patterns=merged["secret_patterns"] or [],
    )


def save_config(repo_root: Path, config: ComCanConfig) -> Path:
    """Save configuration to disk.

    Creates the ``.comcan/`` directory if it doesn't exist.

    Args:
        repo_root: Git repository root directory.
        config: The configuration to save.

    Returns:
        Path to the saved config file.
    """
    config_path = get_config_path(repo_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            config.to_dict(),
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    return config_path
