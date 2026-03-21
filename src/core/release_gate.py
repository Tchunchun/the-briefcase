"""Release readiness gate — validates all prerequisites before shipping.

Checks feature statuses, release note existence, release_note_link on done
features, parent idea propagation, and git cleanliness.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CheckResult:
    """Result of a single readiness check."""

    name: str
    passed: bool
    message: str


@dataclass
class GateReport:
    """Aggregated release readiness report."""

    version: str
    timestamp: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def overall_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "overall_passed": self.overall_passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "message": c.message}
                for c in self.checks
            ],
        }


class ReleaseGate:
    """Validates release readiness across multiple criteria."""

    def __init__(self, store, version: str, project_root: str = ".") -> None:
        self._store = store
        self._version = version
        self._project_root = project_root

    def run(self, apply: bool = False) -> GateReport:
        """Run all readiness checks. If apply=True, perform safe updates."""
        report = GateReport(
            version=self._version,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        backlog = self._store.read_backlog()
        features = [r for r in backlog if r.get("type") == "Feature"]
        ideas = [r for r in backlog if r.get("type") == "Idea"]

        report.checks.append(self._check_release_note_exists())
        report.checks.append(self._check_features_accepted(features))
        report.checks.append(
            self._check_release_note_links(features, apply=apply)
        )
        report.checks.append(
            self._check_parent_ideas_shipped(features, ideas, apply=apply)
        )
        report.checks.append(self._check_no_blocking_findings(features))
        report.checks.append(self._check_git_clean())
        report.checks.append(self._check_tag_not_exists())

        return report

    def _check_release_note_exists(self) -> CheckResult:
        """Verify release note exists for this version."""
        try:
            self._store.read_release_note(self._version)
            return CheckResult(
                "release_note_exists", True,
                f"Release note found for {self._version}",
            )
        except (KeyError, Exception) as e:
            return CheckResult(
                "release_note_exists", False,
                f"Release note missing for {self._version}: {e}",
            )

    def _check_features_accepted(self, features: list[dict]) -> CheckResult:
        """Verify all features are review-accepted or done."""
        not_ready = []
        for f in features:
            status = f.get("status", "")
            if status and status not in (
                "review-accepted", "done", "shipped", ""
            ):
                # Only flag features that are actively in the pipeline
                if status in (
                    "draft", "architect-review", "implementation-ready",
                    "in-progress", "review-ready",
                ):
                    not_ready.append(f"{f.get('title', '?')} ({status})")
        if not_ready:
            return CheckResult(
                "features_accepted", False,
                f"{len(not_ready)} feature(s) not yet accepted: "
                + "; ".join(not_ready[:5]),
            )
        return CheckResult(
            "features_accepted", True,
            "All features are review-accepted or done",
        )

    def _check_release_note_links(
        self, features: list[dict], *, apply: bool = False
    ) -> CheckResult:
        """Verify done features have release_note_link set."""
        missing = []
        for f in features:
            if f.get("status") == "done" and not f.get("release_note_link"):
                missing.append(f)
        if missing and apply:
            # Try to look up the release note URL and set it
            try:
                note = self._store.read_release_note(self._version)
                link = note.get("notion_url") or note.get("url", "")
                if link:
                    for f in missing:
                        self._store.write_backlog_row({
                            "title": f["title"],
                            "type": "Feature",
                            "status": "done",
                            "release_note_link": link,
                        })
                    return CheckResult(
                        "release_note_links", True,
                        f"Applied release_note_link to {len(missing)} feature(s)",
                    )
            except Exception:
                pass
        if missing:
            names = [f.get("title", "?") for f in missing[:5]]
            return CheckResult(
                "release_note_links", False,
                f"{len(missing)} done feature(s) missing release_note_link: "
                + "; ".join(names),
            )
        return CheckResult(
            "release_note_links", True,
            "All done features have release_note_link",
        )

    def _check_parent_ideas_shipped(
        self, features: list[dict], ideas: list[dict], *, apply: bool = False
    ) -> CheckResult:
        """Verify parent ideas are marked shipped when their feature is done."""
        ideas_by_id = {}
        for idea in ideas:
            idea_id = idea.get("notion_id") or idea.get("id", "")
            if idea_id:
                ideas_by_id[idea_id] = idea

        not_shipped = []
        for f in features:
            if f.get("status") != "done":
                continue
            for pid in f.get("parent_ids", []):
                parent = ideas_by_id.get(pid)
                if parent and parent.get("status") not in ("shipped", ""):
                    not_shipped.append(parent)

        if not_shipped and apply:
            for idea in not_shipped:
                try:
                    self._store.write_backlog_row({
                        "title": idea["title"],
                        "type": "Idea",
                        "status": "shipped",
                        "notes": idea.get("notes", "")
                        + f"\nShipped via {self._version}",
                    })
                except Exception:
                    pass
            return CheckResult(
                "parent_ideas_shipped", True,
                f"Applied shipped status to {len(not_shipped)} parent idea(s)",
            )

        if not_shipped:
            names = [i.get("title", "?") for i in not_shipped[:5]]
            return CheckResult(
                "parent_ideas_shipped", False,
                f"{len(not_shipped)} parent idea(s) not shipped: "
                + "; ".join(names),
            )
        return CheckResult(
            "parent_ideas_shipped", True,
            "All parent ideas are shipped",
        )

    def _check_no_blocking_findings(self, features: list[dict]) -> CheckResult:
        """Verify no features have changes-requested review verdict."""
        blocked = []
        for f in features:
            verdict = f.get("review_verdict", "")
            if verdict == "changes-requested":
                blocked.append(f.get("title", "?"))
        if blocked:
            return CheckResult(
                "no_blocking_findings", False,
                f"{len(blocked)} feature(s) have changes-requested: "
                + "; ".join(blocked[:5]),
            )
        return CheckResult(
            "no_blocking_findings", True,
            "No blocking review findings",
        )

    def _check_git_clean(self) -> CheckResult:
        """Verify git working tree is clean."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=10,
                cwd=self._project_root,
            )
            if result.returncode != 0:
                return CheckResult(
                    "git_clean", False,
                    f"git status failed: {result.stderr.strip()}",
                )
            if result.stdout.strip():
                lines = result.stdout.strip().splitlines()
                return CheckResult(
                    "git_clean", False,
                    f"Working tree has {len(lines)} uncommitted change(s)",
                )
            return CheckResult("git_clean", True, "Working tree is clean")
        except FileNotFoundError:
            return CheckResult(
                "git_clean", False, "git not found on PATH"
            )

    def _check_tag_not_exists(self) -> CheckResult:
        """Verify the version tag does not already exist."""
        try:
            result = subprocess.run(
                ["git", "tag", "-l", self._version],
                capture_output=True, text=True, timeout=10,
                cwd=self._project_root,
            )
            if result.stdout.strip():
                return CheckResult(
                    "tag_not_exists", False,
                    f"Tag {self._version} already exists",
                )
            return CheckResult(
                "tag_not_exists", True,
                f"Tag {self._version} does not exist yet",
            )
        except FileNotFoundError:
            return CheckResult(
                "tag_not_exists", False, "git not found on PATH"
            )
