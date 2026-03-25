"""Tests for the expertise manager."""

import json
import pytest
from pathlib import Path

from comcan.expertise_manager import (
    add_domain,
    delete,
    list_domains,
    prime,
    query,
    query_all,
    record,
    search,
)


@pytest.fixture
def repo(tmp_path):
    """Create a minimal repo structure for testing."""
    comcan_dir = tmp_path / ".comcan" / "expertise"
    comcan_dir.mkdir(parents=True)
    return tmp_path


class TestAddDomain:
    def test_creates_domain_file(self, repo):
        path = add_domain(repo, "database")
        assert path.exists()
        assert path.name == "database.jsonl"

    def test_idempotent(self, repo):
        add_domain(repo, "database")
        add_domain(repo, "database")
        assert (repo / ".comcan" / "expertise" / "database.jsonl").exists()


class TestRecord:
    def test_basic_record(self, repo):
        entry = record(repo, "database", "convention", "Use WAL mode")
        assert entry.id.startswith("cm-")
        assert entry.type == "convention"
        assert entry.content == "Use WAL mode"

    def test_record_with_tags(self, repo):
        entry = record(repo, "api", "pattern", "REST endpoints", tags=["rest", "http"])
        assert entry.tags == ["rest", "http"]

    def test_invalid_type(self, repo):
        with pytest.raises(ValueError):
            record(repo, "api", "invalid_type", "content")

    def test_invalid_classification(self, repo):
        with pytest.raises(ValueError):
            record(repo, "api", "convention", "content", classification="invalid")

    def test_record_persists(self, repo):
        record(repo, "database", "convention", "Use WAL mode")
        records = query(repo, "database")
        assert len(records) == 1
        assert records[0].content == "Use WAL mode"


class TestQuery:
    def test_empty_domain(self, repo):
        add_domain(repo, "empty")
        records = query(repo, "empty")
        assert records == []

    def test_nonexistent_domain(self, repo):
        records = query(repo, "nonexistent")
        assert records == []

    def test_multiple_records(self, repo):
        record(repo, "db", "convention", "First")
        record(repo, "db", "pattern", "Second")
        records = query(repo, "db")
        assert len(records) == 2


class TestQueryAll:
    def test_multiple_domains(self, repo):
        record(repo, "db", "convention", "DB rule")
        record(repo, "api", "pattern", "API pattern")
        all_records = query_all(repo)
        assert "db" in all_records
        assert "api" in all_records


class TestSearch:
    def test_finds_by_content(self, repo):
        record(repo, "db", "convention", "Always use WAL mode")
        results = search(repo, "WAL")
        assert len(results) == 1

    def test_finds_by_tag(self, repo):
        record(repo, "db", "convention", "Rule", tags=["sqlite"])
        results = search(repo, "sqlite")
        assert len(results) == 1

    def test_case_insensitive(self, repo):
        record(repo, "db", "convention", "WAL MODE")
        results = search(repo, "wal mode")
        assert len(results) == 1

    def test_no_results(self, repo):
        record(repo, "db", "convention", "Something else")
        results = search(repo, "nonexistent")
        assert len(results) == 0

    def test_search_specific_domain(self, repo):
        record(repo, "db", "convention", "WAL rule")
        record(repo, "api", "convention", "WAL endpoint")
        results = search(repo, "WAL", domain="db")
        assert len(results) == 1


class TestDelete:
    def test_deletes_record(self, repo):
        entry = record(repo, "db", "convention", "Delete me")
        assert delete(repo, "db", entry.id) is True
        assert len(query(repo, "db")) == 0

    def test_delete_nonexistent(self, repo):
        record(repo, "db", "convention", "Keep me")
        assert delete(repo, "db", "cm-nonexistent") is False
        assert len(query(repo, "db")) == 1


class TestPrime:
    def test_outputs_markdown(self, repo):
        record(repo, "db", "convention", "Use WAL mode")
        output = prime(repo)
        assert "# Project Expertise" in output
        assert "Use WAL mode" in output

    def test_empty_output(self, repo):
        output = prime(repo)
        assert "No expertise" in output
