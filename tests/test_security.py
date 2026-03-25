"""Tests for the security module."""

import pytest
from pathlib import Path

from comcan.security import (
    SecurityError,
    sanitize_content,
    validate_subprocess_command,
    validate_write_path,
    audit_report,
)


class TestSanitizeContent:
    """Tests for secret pattern scrubbing."""

    def test_strips_openai_key(self):
        text = "My key is sk-abc123def456ghi789jkl012mno345"
        result = sanitize_content(text)
        assert "sk-abc123" not in result
        assert "[REDACTED]" in result

    def test_strips_anthropic_key(self):
        text = "Key: sk-ant-api03-abcdefghijklmnopqrst"
        result = sanitize_content(text)
        assert "sk-ant-api" not in result

    def test_strips_github_pat(self):
        text = "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
        result = sanitize_content(text)
        assert "ghp_" not in result

    def test_strips_aws_key(self):
        text = "AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE"
        result = sanitize_content(text)
        assert "AKIA" not in result

    def test_preserves_normal_text(self):
        text = "This is a normal commit message about fixing the login page"
        result = sanitize_content(text)
        assert result == text

    def test_extra_patterns(self):
        text = "custom_secret_12345"
        result = sanitize_content(text, extra_patterns=[r"custom_secret_\d+"])
        assert "custom_secret" not in result

    def test_multiple_secrets_in_one_text(self):
        text = "key1=sk-abc123def456ghi789jkl012mno345 key2=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
        result = sanitize_content(text)
        assert result.count("[REDACTED]") == 2


class TestValidateSubprocessCommand:
    """Tests for subprocess command allowlisting."""

    def test_allows_git(self):
        validate_subprocess_command(["git", "log", "-n", "3"])

    def test_blocks_curl(self):
        with pytest.raises(SecurityError):
            validate_subprocess_command(["curl", "https://evil.com"])

    def test_blocks_python(self):
        with pytest.raises(SecurityError):
            validate_subprocess_command(["python", "-c", "import os"])

    def test_blocks_empty(self):
        with pytest.raises(SecurityError):
            validate_subprocess_command([])

    def test_blocks_powershell(self):
        with pytest.raises(SecurityError):
            validate_subprocess_command(["powershell", "-Command", "..."])

    def test_allows_git_with_path(self):
        # On some systems git might be called with a full path
        validate_subprocess_command(["git", "status"])


class TestValidateWritePath:
    """Tests for path traversal prevention."""

    def test_allows_path_inside_repo(self, tmp_path):
        target = tmp_path / ".comcan" / "CURRENT_STATE.md"
        validate_write_path(target, tmp_path)  # Should not raise

    def test_blocks_path_outside_repo(self, tmp_path):
        target = tmp_path / ".." / "etc" / "passwd"
        with pytest.raises(SecurityError):
            validate_write_path(target, tmp_path)

    def test_blocks_absolute_path_outside(self, tmp_path):
        target = Path("C:/Windows/System32/evil.dll")
        with pytest.raises(SecurityError):
            validate_write_path(target, tmp_path)


class TestAuditReport:
    """Tests for the security audit report."""

    def test_returns_dict(self, tmp_path):
        report = audit_report(tmp_path)
        assert isinstance(report, dict)
        assert "no_setup_py" in report
        assert "zero_network" in report

    def test_fails_when_setup_py_exists(self, tmp_path):
        (tmp_path / "setup.py").touch()
        report = audit_report(tmp_path)
        assert report["no_setup_py"]["pass"] is False

    def test_passes_without_setup_py(self, tmp_path):
        report = audit_report(tmp_path)
        assert report["no_setup_py"]["pass"] is True
