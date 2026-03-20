"""Upstream feedback forwarding.

When a consumer project has ``upstream.feedback_repo`` configured in
storage.yaml, feedback-type inbox entries are forwarded to the framework
author's GitHub repository as issues.
"""

from __future__ import annotations

import shutil
import subprocess


def forward_feedback(
    repo: str,
    text: str,
    notes: str = "",
    priority: str = "Medium",
) -> dict:
    """Create a GitHub issue on the upstream repo for a feedback entry.

    Args:
        repo: GitHub repo in ``owner/repo`` format.
        text: Short feedback title.
        notes: Optional longer description.
        priority: Priority level.

    Returns:
        dict with ``forwarded`` (bool), ``url`` (str|None), ``error`` (str|None).
    """
    gh = shutil.which("gh")
    if gh is None:
        return {
            "forwarded": False,
            "url": None,
            "error": "gh CLI not found. Install GitHub CLI to forward feedback upstream.",
        }

    body_parts = []
    if notes:
        body_parts.append(notes)
    body_parts.append(f"\n**Priority:** {priority}")
    body_parts.append("_Submitted via `briefcase inbox add --type feedback`_")
    body = "\n\n".join(body_parts)

    cmd = [
        gh,
        "issue",
        "create",
        "--repo",
        repo,
        "--title",
        f"[Feedback] {text}",
        "--body",
        body,
        "--label",
        "feedback",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            return {"forwarded": True, "url": url, "error": None}
        else:
            return {
                "forwarded": False,
                "url": None,
                "error": f"gh issue create failed: {result.stderr.strip()}",
            }
    except subprocess.TimeoutExpired:
        return {
            "forwarded": False,
            "url": None,
            "error": "gh issue create timed out after 30s.",
        }
    except OSError as exc:
        return {
            "forwarded": False,
            "url": None,
            "error": f"Failed to run gh: {exc}",
        }
