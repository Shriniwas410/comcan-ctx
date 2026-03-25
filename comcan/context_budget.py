"""Production-grade, multi-model-aware context budget engine.

Understands how Cursor and other AI coding agents consume context windows.
Allocates token budgets across sections (tree, commits, diff, expertise)
to maximize the usefulness of ComCan's output while leaving 90%+ of the
context window for the agent's actual work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import tiktoken


# ── Model Profiles ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ModelProfile:
    """Defines a context window profile for a family of LLM models."""
    name: str
    context_window: int      # Total tokens the model supports
    comcan_budget: int        # Tokens ComCan should use (~5% of window)
    encoding_name: str        # tiktoken encoding to use
    description: str


PROFILES: dict[str, ModelProfile] = {
    "standard": ModelProfile(
        name="standard",
        context_window=128_000,
        comcan_budget=6_400,
        encoding_name="o200k_base",
        description="GPT-4o, Claude 3.5 Sonnet (128k context)",
    ),
    "large": ModelProfile(
        name="large",
        context_window=200_000,
        comcan_budget=10_000,
        encoding_name="o200k_base",
        description="Claude 3.5/4, Cursor default (200k context)",
    ),
    "max": ModelProfile(
        name="max",
        context_window=1_000_000,
        comcan_budget=50_000,
        encoding_name="o200k_base",
        description="Gemini 2.5 Pro Max Mode (1M context)",
    ),
}

# Section allocation percentages (must sum to 100)
DEFAULT_ALLOCATION = {
    "tree": 40,
    "commits": 15,
    "diff": 20,
    "expertise": 25,
}


class ContextBudget:
    """Manages token budgets for ComCan's content sections.

    Usage::

        budget = ContextBudget("large")
        allocations = budget.allocate()
        # {'tree': 4000, 'commits': 1500, 'diff': 2000, 'expertise': 2500}

        fitted = budget.fit_content({
            'tree': very_long_tree_string,
            'commits': commit_log,
        })
    """

    def __init__(
        self,
        profile: str = "large",
        custom_budget: Optional[int] = None,
    ) -> None:
        """Initialize the budget engine.

        Args:
            profile: One of 'standard', 'large', 'max', or 'custom'.
            custom_budget: Total token budget when profile is 'custom'.
        """
        if profile == "custom":
            if custom_budget is None:
                raise ValueError("custom_budget is required when profile='custom'")
            self._profile = ModelProfile(
                name="custom",
                context_window=custom_budget * 20,  # assume 5% allocation
                comcan_budget=custom_budget,
                encoding_name="o200k_base",
                description=f"Custom ({custom_budget} token budget)",
            )
        else:
            if profile not in PROFILES:
                raise ValueError(
                    f"Unknown profile '{profile}'. "
                    f"Choose from: {', '.join(PROFILES.keys())}, custom"
                )
            self._profile = PROFILES[profile]

        self._encoding = tiktoken.get_encoding(self._profile.encoding_name)

    @property
    def profile(self) -> ModelProfile:
        """The active model profile."""
        return self._profile

    @property
    def total_budget(self) -> int:
        """Total token budget for ComCan content."""
        return self._profile.comcan_budget

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: The text to tokenize.

        Returns:
            Number of tokens.
        """
        if not text:
            return 0
        return len(self._encoding.encode(text))

    def fits_budget(self, text: str, budget: Optional[int] = None) -> bool:
        """Check if text fits within a token budget.

        Args:
            text: The text to check.
            budget: Token limit (defaults to total ComCan budget).

        Returns:
            True if the text fits.
        """
        limit = budget if budget is not None else self.total_budget
        return self.count_tokens(text) <= limit

    def allocate(
        self,
        allocation: Optional[dict[str, int]] = None,
    ) -> dict[str, int]:
        """Calculate per-section token budgets.

        Args:
            allocation: Custom percentage allocation. Keys are section names,
                values are percentages that must sum to 100.

        Returns:
            Dict mapping section names to their token budgets.
        """
        alloc = allocation or DEFAULT_ALLOCATION

        total_pct = sum(alloc.values())
        if total_pct != 100:
            raise ValueError(
                f"Allocation percentages must sum to 100, got {total_pct}"
            )

        return {
            section: int(self.total_budget * pct / 100)
            for section, pct in alloc.items()
        }

    def truncate_smart(
        self,
        text: str,
        budget: int,
        preserve_start: bool = True,
    ) -> str:
        """Truncate text to fit within a token budget.

        Uses smart truncation that preserves either the start or end of
        the content (start = recent commits first, end = deepest tree nodes).

        Args:
            text: The text to truncate.
            budget: Maximum token count.
            preserve_start: If True, keep the beginning; if False, keep the end.

        Returns:
            Truncated text with a marker indicating omission.
        """
        if not text:
            return text

        tokens = self._encoding.encode(text)
        if len(tokens) <= budget:
            return text

        # Reserve tokens for the truncation marker
        marker = "\n[... truncated to fit context budget ...]\n"
        marker_tokens = len(self._encoding.encode(marker))
        available = max(budget - marker_tokens, 0)

        if available == 0:
            return marker.strip()

        if preserve_start:
            kept_tokens = tokens[:available]
            truncated = self._encoding.decode(kept_tokens)
            return truncated + marker
        else:
            kept_tokens = tokens[-available:]
            truncated = self._encoding.decode(kept_tokens)
            return marker + truncated

    def fit_content(self, sections: dict[str, str]) -> dict[str, str]:
        """Fit multiple content sections into their allocated budgets.

        Args:
            sections: Dict mapping section names to their content strings.
                Section names should match the allocation keys (tree, commits,
                diff, expertise).

        Returns:
            Dict with the same keys but content truncated to fit budgets.
        """
        budgets = self.allocate()
        result: dict[str, str] = {}

        for section, content in sections.items():
            section_budget = budgets.get(section, self.total_budget // 4)
            preserve_start = section in ("commits", "diff", "expertise")
            result[section] = self.truncate_smart(
                content, section_budget, preserve_start=preserve_start
            )

        return result

    def estimate_profile(self, text: str) -> str:
        """Suggest which profile best fits the generated content.

        Args:
            text: The full ComCan output to analyze.

        Returns:
            Recommended profile name.
        """
        token_count = self.count_tokens(text)

        if token_count <= PROFILES["standard"].comcan_budget:
            return "standard"
        elif token_count <= PROFILES["large"].comcan_budget:
            return "large"
        else:
            return "max"
