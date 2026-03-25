"""Structured expertise storage — the 'Hard Drive' engine.

Manages JSONL-based expertise records organized by domain. Implements
file locking for concurrency safety and atomic writes.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from comcan.security import validate_write_path


# ── Record Types ────────────────────────────────────────────────────────────

RECORD_TYPES = frozenset({
    "convention",   # "Always use X"
    "pattern",      # "We do Y using Z approach"
    "failure",      # "X broke because of Y" + resolution
    "decision",     # "We chose X over Y because..."
    "reference",    # Links, docs, external resources
})

CLASSIFICATIONS = frozenset({
    "foundational",   # Core rules that rarely change
    "tactical",       # Current sprint / active work patterns
    "observational",  # Nice-to-know, may expire
})


@dataclass
class ExpertiseRecord:
    """A single expertise record."""

    id: str
    type: str
    content: str
    domain: str
    timestamp: str
    description: str = ""
    resolution: str = ""
    tags: list[str] = field(default_factory=list)
    classification: str = "tactical"
    author: str = "developer"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpertiseRecord":
        """Deserialize from a dict."""
        return cls(
            id=data["id"],
            type=data["type"],
            content=data["content"],
            domain=data.get("domain", ""),
            timestamp=data.get("timestamp", ""),
            description=data.get("description", ""),
            resolution=data.get("resolution", ""),
            tags=data.get("tags", []),
            classification=data.get("classification", "tactical"),
            author=data.get("author", "developer"),
        )


# ── ID Generation ───────────────────────────────────────────────────────────

def _generate_id(content: str) -> str:
    """Generate a short, deterministic record ID."""
    hash_input = f"{content}{time.time_ns()}"
    return "cm-" + hashlib.sha256(hash_input.encode()).hexdigest()[:8]


# ── File Locking ────────────────────────────────────────────────────────────

_LOCK_TIMEOUT = 5.0       # seconds
_LOCK_RETRY_INTERVAL = 0.05  # seconds
_STALE_LOCK_AGE = 30.0    # seconds


class LockError(Exception):
    """Raised when a file lock cannot be acquired."""


def _acquire_lock(filepath: Path) -> Path:
    """Acquire an advisory file lock.

    Args:
        filepath: The file to lock.

    Returns:
        Path to the lock file.

    Raises:
        LockError: If the lock cannot be acquired within timeout.
    """
    lock_path = filepath.with_suffix(filepath.suffix + ".lock")
    start = time.monotonic()

    while True:
        try:
            # O_CREAT | O_EXCL is atomic on most filesystems
            fd = os.open(
                str(lock_path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return lock_path
        except FileExistsError:
            # Check for stale lock
            try:
                lock_age = time.time() - os.path.getmtime(str(lock_path))
                if lock_age > _STALE_LOCK_AGE:
                    os.unlink(str(lock_path))
                    continue
            except OSError:
                pass

            elapsed = time.monotonic() - start
            if elapsed > _LOCK_TIMEOUT:
                raise LockError(
                    f"Could not acquire lock on {filepath} "
                    f"after {_LOCK_TIMEOUT}s. "
                    "Another process may be writing."
                )
            time.sleep(_LOCK_RETRY_INTERVAL)


def _release_lock(lock_path: Path) -> None:
    """Release an advisory file lock."""
    try:
        os.unlink(str(lock_path))
    except OSError:
        pass


# ── Path Helpers ────────────────────────────────────────────────────────────

def _expertise_dir(repo_root: Path) -> Path:
    """Return the path to the expertise directory."""
    return repo_root / ".comcan" / "expertise"


def _domain_path(repo_root: Path, domain: str) -> Path:
    """Return the JSONL file path for a domain."""
    # Sanitize domain name
    safe_name = domain.lower().replace(" ", "-").replace("/", "-")
    return _expertise_dir(repo_root) / f"{safe_name}.jsonl"


# ── Public API ──────────────────────────────────────────────────────────────

def add_domain(repo_root: Path, domain: str) -> Path:
    """Create a new expertise domain.

    Args:
        repo_root: Git repository root.
        domain: Domain name (e.g., "database", "api").

    Returns:
        Path to the created JSONL file.
    """
    expertise_dir = _expertise_dir(repo_root)
    validate_write_path(expertise_dir, repo_root)
    expertise_dir.mkdir(parents=True, exist_ok=True)

    domain_file = _domain_path(repo_root, domain)
    if not domain_file.exists():
        domain_file.touch()

    return domain_file


def list_domains(repo_root: Path) -> list[str]:
    """List all registered expertise domains.

    Args:
        repo_root: Git repository root.

    Returns:
        List of domain names.
    """
    expertise_dir = _expertise_dir(repo_root)
    if not expertise_dir.exists():
        return []

    return sorted(
        p.stem for p in expertise_dir.glob("*.jsonl")
    )


def record(
    repo_root: Path,
    domain: str,
    record_type: str,
    content: str,
    description: str = "",
    resolution: str = "",
    tags: Optional[list[str]] = None,
    classification: str = "tactical",
    author: str = "developer",
) -> ExpertiseRecord:
    """Record a new expertise entry with file locking.

    Args:
        repo_root: Git repository root.
        domain: Domain name.
        record_type: One of: convention, pattern, failure, decision, reference.
        content: The expertise content (main lesson).
        description: Optional longer description.
        resolution: Optional resolution (for failures).
        tags: Optional list of tags.
        classification: One of: foundational, tactical, observational.
        author: Who recorded this.

    Returns:
        The created ExpertiseRecord.

    Raises:
        ValueError: If record_type or classification is invalid.
        LockError: If the file lock cannot be acquired.
    """
    if record_type not in RECORD_TYPES:
        raise ValueError(
            f"Invalid record type '{record_type}'. "
            f"Must be one of: {', '.join(sorted(RECORD_TYPES))}"
        )

    if classification not in CLASSIFICATIONS:
        raise ValueError(
            f"Invalid classification '{classification}'. "
            f"Must be one of: {', '.join(sorted(CLASSIFICATIONS))}"
        )

    # Ensure domain exists
    domain_file = add_domain(repo_root, domain)
    validate_write_path(domain_file, repo_root)

    entry = ExpertiseRecord(
        id=_generate_id(content),
        type=record_type,
        content=content,
        domain=domain,
        timestamp=datetime.now(timezone.utc).isoformat(),
        description=description,
        resolution=resolution,
        tags=tags or [],
        classification=classification,
        author=author,
    )

    # Atomic write with locking
    lock = _acquire_lock(domain_file)
    try:
        with open(domain_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    finally:
        _release_lock(lock)

    return entry


def query(repo_root: Path, domain: str) -> list[ExpertiseRecord]:
    """Retrieve all expertise records for a domain.

    Args:
        repo_root: Git repository root.
        domain: Domain name.

    Returns:
        List of ExpertiseRecord objects, ordered by timestamp.
    """
    domain_file = _domain_path(repo_root, domain)
    if not domain_file.exists():
        return []

    records: list[ExpertiseRecord] = []
    with open(domain_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(ExpertiseRecord.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue  # Skip malformed records

    return records


def query_all(repo_root: Path) -> dict[str, list[ExpertiseRecord]]:
    """Retrieve all expertise records across all domains.

    Args:
        repo_root: Git repository root.

    Returns:
        Dict mapping domain names to their records.
    """
    domains = list_domains(repo_root)
    return {domain: query(repo_root, domain) for domain in domains}


def search(
    repo_root: Path,
    query_text: str,
    domain: Optional[str] = None,
) -> list[ExpertiseRecord]:
    """Keyword search across expertise records.

    Args:
        repo_root: Git repository root.
        query_text: Text to search for (case-insensitive).
        domain: Optional domain to restrict search to.

    Returns:
        List of matching records.
    """
    query_lower = query_text.lower()

    if domain:
        all_records = {domain: query(repo_root, domain)}
    else:
        all_records = query_all(repo_root)

    results: list[ExpertiseRecord] = []
    for records in all_records.values():
        for rec in records:
            searchable = f"{rec.content} {rec.description} {rec.resolution} {' '.join(rec.tags)}"
            if query_lower in searchable.lower():
                results.append(rec)

    return results


def delete(repo_root: Path, domain: str, record_id: str) -> bool:
    """Delete a record by ID.

    Uses atomic write: writes all records except the deleted one to a
    temp file, then renames.

    Args:
        repo_root: Git repository root.
        domain: Domain name.
        record_id: The record ID to delete.

    Returns:
        True if the record was found and deleted.
    """
    domain_file = _domain_path(repo_root, domain)
    if not domain_file.exists():
        return False

    validate_write_path(domain_file, repo_root)

    lock = _acquire_lock(domain_file)
    try:
        records = query(repo_root, domain)
        new_records = [r for r in records if r.id != record_id]

        if len(new_records) == len(records):
            return False  # Record not found

        # Atomic write via temp file
        tmp_file = domain_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            for rec in new_records:
                f.write(json.dumps(rec.to_dict()) + "\n")

        tmp_file.replace(domain_file)
        return True
    finally:
        _release_lock(lock)


def prime(
    repo_root: Path,
    domains: Optional[list[str]] = None,
    budget: Optional[int] = None,
) -> str:
    """Generate agent-injectable markdown from expertise records.

    Args:
        repo_root: Git repository root.
        domains: Specific domains to include (all if None).
        budget: Token budget for the output.

    Returns:
        Markdown-formatted expertise summary.
    """
    if domains:
        all_records = {d: query(repo_root, d) for d in domains}
    else:
        all_records = query_all(repo_root)

    if not any(all_records.values()):
        return "No expertise recorded yet."

    lines: list[str] = ["# Project Expertise", ""]

    for domain, records in sorted(all_records.items()):
        if not records:
            continue

        lines.append(f"## {domain.title()} ({len(records)} entries)")
        lines.append("")

        # Group by type
        by_type: dict[str, list[ExpertiseRecord]] = {}
        for rec in records:
            by_type.setdefault(rec.type, []).append(rec)

        for record_type, recs in sorted(by_type.items()):
            lines.append(f"### {record_type.title()}s")
            for rec in recs:
                lines.append(f"- {rec.content}")
                if rec.resolution:
                    lines.append(f"  → {rec.resolution}")
            lines.append("")

    output = "\n".join(lines)

    if budget:
        from comcan.context_budget import ContextBudget
        cb = ContextBudget("large")
        output = cb.truncate_smart(output, budget, preserve_start=True)

    return output
