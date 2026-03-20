"""Unit tests for upstream feedback forwarding."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import subprocess

from src.core.feedback import forward_feedback


class TestForwardFeedback:
    def test_returns_error_when_gh_not_found(self):
        with patch("src.core.feedback.shutil.which", return_value=None):
            result = forward_feedback("owner/repo", "test title")
        assert result["forwarded"] is False
        assert "gh CLI not found" in result["error"]

    def test_forwards_successfully(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/owner/repo/issues/42\n"

        with (
            patch("src.core.feedback.shutil.which", return_value="/usr/bin/gh"),
            patch("src.core.feedback.subprocess.run", return_value=mock_result) as mock_run,
        ):
            result = forward_feedback(
                "owner/repo", "test title", notes="some notes", priority="High"
            )

        assert result["forwarded"] is True
        assert result["url"] == "https://github.com/owner/repo/issues/42"
        assert result["error"] is None

        # Verify gh was called with correct args
        call_args = mock_run.call_args[0][0]
        assert "issue" in call_args
        assert "create" in call_args
        assert "--repo" in call_args
        assert "owner/repo" in call_args
        assert "[Feedback] test title" in call_args

    def test_returns_error_on_gh_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "HTTP 403: forbidden"

        with (
            patch("src.core.feedback.shutil.which", return_value="/usr/bin/gh"),
            patch("src.core.feedback.subprocess.run", return_value=mock_result),
        ):
            result = forward_feedback("owner/repo", "test title")

        assert result["forwarded"] is False
        assert "HTTP 403" in result["error"]

    def test_returns_error_on_timeout(self):
        with (
            patch("src.core.feedback.shutil.which", return_value="/usr/bin/gh"),
            patch(
                "src.core.feedback.subprocess.run",
                side_effect=subprocess.TimeoutExpired("gh", 30),
            ),
        ):
            result = forward_feedback("owner/repo", "test title")

        assert result["forwarded"] is False
        assert "timed out" in result["error"]

    def test_body_includes_notes_and_priority(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/owner/repo/issues/1\n"

        with (
            patch("src.core.feedback.shutil.which", return_value="/usr/bin/gh"),
            patch("src.core.feedback.subprocess.run", return_value=mock_result) as mock_run,
        ):
            forward_feedback(
                "owner/repo", "title", notes="detailed notes", priority="Low"
            )

        call_args = mock_run.call_args[0][0]
        body_idx = call_args.index("--body") + 1
        body = call_args[body_idx]
        assert "detailed notes" in body
        assert "**Priority:** Low" in body
