"""Tests for shared private artifact repo sync."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.core.storage.local_backend import LocalBackend
from src.sync.git_sync import GitSync, GitSyncConfig, GitSyncError


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
	return subprocess.run(
		["git", *args],
		cwd=cwd,
		check=True,
		capture_output=True,
		text=True,
	)


def _init_repo(root: Path) -> None:
	_git(root, "init", "-b", "main")
	_git(root, "config", "user.name", "Test User")
	_git(root, "config", "user.email", "test@example.com")


def _commit_all(root: Path, message: str) -> None:
	_git(root, "add", ".")
	_git(root, "commit", "-m", message)


def _clone_remote(remote: Path, destination: Path) -> Path:
	subprocess.run(
		["git", "clone", str(remote), str(destination)],
		check=True,
		capture_output=True,
		text=True,
	)
	return destination


@pytest.fixture()
def project_repo(tmp_path: Path) -> tuple[Path, Path]:
	remote = tmp_path / "artifacts-remote.git"
	_git(tmp_path, "init", "--bare", str(remote))

	project = tmp_path / "project"
	project.mkdir()
	(project / "docs" / "plan").mkdir(parents=True)
	(project / "_project").mkdir()
	(project / "src").mkdir()
	(project / "docs" / "plan" / "brief.md").write_text("version one\n")
	(project / "_project" / "storage.yaml").write_text("backend: git\n")
	(project / "src" / "app.py").write_text("print('code')\n")

	_init_repo(project)
	_commit_all(project, "initial project state")
	return project, remote


def test_push_exports_only_artifacts_to_project_namespace(
	project_repo: tuple[Path, Path], tmp_path: Path
):
	project, remote = project_repo
	(project / "docs" / "plan" / "brief.md").write_text("version two\n")

	syncer = GitSync(
		project,
		GitSyncConfig(
			remote="origin",
			remote_url=str(remote),
			branch="main",
			project_slug="demo-project",
		),
	)

	syncer.configure_remote(str(remote))
	result = syncer.push()

	assert result["pushed"] is True

	clone_dir = _clone_remote(remote, tmp_path / "inspect-remote")
	assert (
		clone_dir / "projects" / "demo-project" / "docs" / "plan" / "brief.md"
	).read_text() == "version two\n"
	assert (
		clone_dir / "projects" / "demo-project" / "_project" / "storage.yaml"
	).exists()
	assert not (clone_dir / "src" / "app.py").exists()


def test_pull_restores_only_current_project_namespace(
	project_repo: tuple[Path, Path], tmp_path: Path
):
	project, remote = project_repo
	syncer = GitSync(
		project,
		GitSyncConfig(
			remote="origin",
			remote_url=str(remote),
			branch="main",
			project_slug="demo-project",
		),
	)
	(project / "docs" / "plan" / "brief.md").write_text("local sync seed\n")
	syncer.configure_remote(str(remote))
	syncer.push()

	clone_dir = _clone_remote(remote, tmp_path / "mutate-remote")
	_git(clone_dir, "config", "user.name", "Remote User")
	_git(clone_dir, "config", "user.email", "remote@example.com")
	(clone_dir / "projects" / "demo-project" / "docs" / "plan").mkdir(
		parents=True, exist_ok=True
	)
	(
		clone_dir / "projects" / "demo-project" / "docs" / "plan" / "brief.md"
	).write_text("remote update\n")
	(clone_dir / "projects" / "other-project").mkdir(parents=True, exist_ok=True)
	(clone_dir / "projects" / "other-project" / "docs.txt").write_text(
		"ignore me\n"
	)
	_commit_all(clone_dir, "update artifact namespace")
	_git(clone_dir, "push", "origin", "HEAD:main")

	result = syncer.pull()

	assert result["applied"] is True
	assert (project / "docs" / "plan" / "brief.md").read_text() == "remote update\n"
	assert (project / "src" / "app.py").read_text() == "print('code')\n"


def test_push_fails_clearly_when_project_slug_missing(
	project_repo: tuple[Path, Path]
):
	project, remote = project_repo
	syncer = GitSync(
		project,
		GitSyncConfig(
			remote="origin",
			remote_url=str(remote),
			branch="main",
			project_slug="",
		),
	)

	with pytest.raises(GitSyncError, match="project_slug"):
		syncer.push()


def test_pull_allows_bootstrap_storage_yaml_for_clean_consumer(
	project_repo: tuple[Path, Path], tmp_path: Path
):
	project, remote = project_repo
	syncer = GitSync(
		project,
		GitSyncConfig(
			remote="origin",
			remote_url=str(remote),
			branch="main",
			project_slug="demo-project",
		),
	)
	(project / "docs" / "plan" / "brief.md").write_text("seeded artifact\n")
	syncer.configure_remote(str(remote))
	syncer.push()

	consumer = tmp_path / "consumer"
	consumer.mkdir()
	(consumer / "_project").mkdir()
	(consumer / "_project" / "storage.yaml").write_text(
		"backend: git\n"
		"git:\n"
		"  remote: origin\n"
		f"  remote_url: {remote}\n"
		"  branch: main\n"
		"  project_slug: demo-project\n"
	)

	consumer_syncer = GitSync(
		consumer,
		GitSyncConfig(
			remote="origin",
			remote_url=str(remote),
			branch="main",
			project_slug="demo-project",
		),
	)
	consumer_syncer.configure_remote(str(remote))

	result = consumer_syncer.pull()

	assert result["applied"] is True
	assert result["conflicts"] == []
	assert (consumer / "docs" / "plan" / "brief.md").read_text() == "seeded artifact\n"


def test_pull_restores_missing_local_artifacts_without_new_remote_commit(
	project_repo: tuple[Path, Path]
):
	project, remote = project_repo
	syncer = GitSync(
		project,
		GitSyncConfig(
			remote="origin",
			remote_url=str(remote),
			branch="main",
			project_slug="demo-project",
		),
	)
	(project / "docs" / "plan" / "brief.md").write_text("rehydrate me\n")
	syncer.configure_remote(str(remote))
	syncer.push()

	(project / "docs" / "plan" / "brief.md").unlink()

	result = syncer.pull()

	assert result["applied"] is True
	assert "docs/plan/brief.md" in result["incoming"]
	assert (project / "docs" / "plan" / "brief.md").read_text() == "rehydrate me\n"


def test_git_roundtrip_preserves_compact_backlog_metadata(
	project_repo: tuple[Path, Path], tmp_path: Path
):
	project, remote = project_repo
	(project / "docs" / "plan" / "_shared").mkdir(parents=True, exist_ok=True)
	(project / "docs" / "plan" / "_shared" / "backlog.md").write_text(
		"# Backlog\n\n"
		"Cross-feature source of truth for task priority and execution status.\n\n"
		"| Type | Title | Status | Priority | Project | Notes |\n"
		"|---|---|---|---|---|---|\n"
	)

	backend = LocalBackend(project)
	backend.write_backlog_row(
		{
			"title": "Shared private artifact repo",
			"type": "Feature",
			"status": "review-accepted",
			"priority": "High",
			"project": "Briefcase",
			"notes": "Delivery handoff preserved.",
			"review_verdict": "accepted",
			"route_state": "routed",
			"lane": "feature",
			"release_note_link": "docs/plan/_releases/v0.9.4/release-notes.md",
			"automation_trace": "[auto-review-ready] dispatched",
		}
	)

	syncer = GitSync(
		project,
		GitSyncConfig(
			remote="origin",
			remote_url=str(remote),
			branch="main",
			project_slug="demo-project",
		),
	)
	syncer.configure_remote(str(remote))
	syncer.push()

	consumer = tmp_path / "consumer"
	consumer.mkdir()
	(consumer / "_project").mkdir()
	(consumer / "_project" / "storage.yaml").write_text(
		"backend: git\n"
		"git:\n"
		"  remote: origin\n"
		f"  remote_url: {remote}\n"
		"  branch: main\n"
		"  project_slug: demo-project\n"
	)

	consumer_syncer = GitSync(
		consumer,
		GitSyncConfig(
			remote="origin",
			remote_url=str(remote),
			branch="main",
			project_slug="demo-project",
		),
	)
	consumer_syncer.configure_remote(str(remote))
	consumer_syncer.pull()

	row = next(
		item
		for item in LocalBackend(consumer).read_backlog()
		if item["title"] == "Shared private artifact repo"
	)

	assert row["status"] == "review-accepted"
	assert row["review_verdict"] == "accepted"
	assert row["route_state"] == "routed"
	assert row["lane"] == "feature"
	assert row["release_note_link"] == "docs/plan/_releases/v0.9.4/release-notes.md"
	assert row["automation_trace"] == "[auto-review-ready] dispatched"
	assert row["notes"] == "Delivery handoff preserved."
