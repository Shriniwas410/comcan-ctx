"""Tests for the context budget engine."""

import pytest

from comcan.context_budget import ContextBudget, PROFILES


class TestContextBudget:
    """Tests for the ContextBudget class."""

    def test_default_profile(self):
        budget = ContextBudget()
        assert budget.profile.name == "large"
        assert budget.total_budget == 10_000

    def test_standard_profile(self):
        budget = ContextBudget("standard")
        assert budget.total_budget == 6_400

    def test_max_profile(self):
        budget = ContextBudget("max")
        assert budget.total_budget == 50_000

    def test_custom_profile(self):
        budget = ContextBudget("custom", custom_budget=5000)
        assert budget.total_budget == 5000

    def test_custom_requires_budget(self):
        with pytest.raises(ValueError):
            ContextBudget("custom")

    def test_invalid_profile(self):
        with pytest.raises(ValueError):
            ContextBudget("nonexistent")

    def test_count_tokens_empty(self):
        budget = ContextBudget()
        assert budget.count_tokens("") == 0

    def test_count_tokens_simple(self):
        budget = ContextBudget()
        count = budget.count_tokens("Hello, world!")
        assert count > 0
        assert count < 10

    def test_fits_budget_true(self):
        budget = ContextBudget()
        assert budget.fits_budget("Hello") is True

    def test_fits_budget_false(self):
        budget = ContextBudget("custom", custom_budget=1)
        assert budget.fits_budget("This is a very long text " * 100) is False

    def test_allocate_default(self):
        budget = ContextBudget("large")
        alloc = budget.allocate()
        assert alloc["tree"] == 4000
        assert alloc["commits"] == 1500
        assert alloc["diff"] == 2000
        assert alloc["expertise"] == 2500
        assert sum(alloc.values()) == budget.total_budget

    def test_allocate_custom(self):
        budget = ContextBudget("large")
        alloc = budget.allocate({"code": 50, "docs": 50})
        assert alloc["code"] == 5000
        assert alloc["docs"] == 5000

    def test_allocate_bad_percentages(self):
        budget = ContextBudget()
        with pytest.raises(ValueError):
            budget.allocate({"a": 30, "b": 30})

    def test_truncate_short_text(self):
        budget = ContextBudget()
        text = "Hello"
        assert budget.truncate_smart(text, 100) == text

    def test_truncate_preserves_start(self):
        budget = ContextBudget()
        text = "Start " + "padding " * 1000
        result = budget.truncate_smart(text, 50, preserve_start=True)
        assert result.startswith("Start")
        assert "truncated" in result

    def test_fit_content(self):
        budget = ContextBudget("large")
        sections = {
            "tree": "short tree",
            "commits": "short commits",
        }
        result = budget.fit_content(sections)
        assert "short tree" in result["tree"]
        assert "short commits" in result["commits"]

    def test_estimate_profile(self):
        budget = ContextBudget("large")
        assert budget.estimate_profile("Hello") == "standard"
