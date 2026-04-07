"""Load and save storage configuration.

Supports dual-mode resolution (D-036):
- Canonical: _project/storage.yaml
- Fallback: .briefcase/storage.yaml (installer bootstrap only)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


STORAGE_CONFIG_FILENAME = "storage.yaml"
DEFAULT_BACKEND = "local"
VALID_BACKENDS = ("local", "git", "notion")


@dataclass
class GitConfig:
    """Git-specific sync configuration."""

    remote: str = "origin"
    remote_url: str = ""
    branch: str = "main"
    paths: list = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.paths is None:
            self.paths = ["docs/plan/", "_project/"]


@dataclass
class NotionConfig:
    """Notion-specific backend configuration."""

    parent_page_id: str = ""
    parent_page_url: str = ""
    databases: dict[str, str] = field(default_factory=dict)
    seeded_template_versions: dict[str, str] = field(default_factory=dict)


@dataclass
class UpstreamConfig:
    """Upstream feedback routing configuration.

    When present, ``briefcase inbox add --type feedback`` forwards the
    entry to the framework author's repo as a GitHub issue.
    """

    feedback_repo: str = ""  # e.g. "owner/repo"


@dataclass
class ProjectConfig:
    """Project-scoped metadata used by artifact creation flows."""

    name: str = ""


@dataclass
class StorageConfig:
    """Top-level storage configuration."""

    backend: str = DEFAULT_BACKEND
    notion: NotionConfig | None = None
    git: GitConfig | None = None
    upstream: UpstreamConfig | None = None
    project: ProjectConfig | None = None

    def is_notion(self) -> bool:
        return self.backend == "notion"

    def is_local(self) -> bool:
        return self.backend == "local"

    def is_git(self) -> bool:
        return self.backend == "git"

    def has_upstream_feedback(self) -> bool:
        return self.upstream is not None and bool(self.upstream.feedback_repo)

    def default_project_name(self) -> str:
        return self.project.name if self.project is not None else ""


def _find_project_dir(start: str | Path | None = None) -> Path:
    """Locate the _project/ directory by walking up from start (or cwd)."""
    current = Path(start) if start else Path.cwd()
    while True:
        candidate = current / "_project"
        if candidate.is_dir():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    raise FileNotFoundError(
        "_project/ directory not found. Run `agent setup` to initialize."
    )


def _find_config_dir(start: str | Path | None = None) -> Path:
    """Locate the directory containing storage.yaml.

    Resolution order (D-036):
    1. _project/storage.yaml — canonical project config
    2. .briefcase/storage.yaml — fallback for installer bootstrap

    Walks up from start (or cwd) checking each ancestor.
    """
    current = Path(start) if start else Path.cwd()
    while True:
        briefcase = current / ".briefcase"
        project = current / "_project"
        project_config_path = project / STORAGE_CONFIG_FILENAME
        briefcase_config_path = briefcase / STORAGE_CONFIG_FILENAME

        if project.is_dir() and project_config_path.exists():
            if (
                briefcase.is_dir()
                and briefcase_config_path.exists()
                and not _config_files_match(project_config_path, briefcase_config_path)
            ):
                raise ValueError(
                    "Config mismatch detected: _project/storage.yaml and "
                    ".briefcase/storage.yaml both exist but differ. "
                    "Use _project/storage.yaml as canonical and align or remove "
                    ".briefcase/storage.yaml."
                )
            return project
        if briefcase.is_dir() and briefcase_config_path.exists():
            return briefcase
        parent = current.parent
        if parent == current:
            break
        current = parent
    raise FileNotFoundError(
        "storage.yaml not found. Checked .briefcase/ and _project/ walking up "
        "from current directory. Run install.sh or `agent setup` to initialize."
    )


def load_config(project_dir: str | Path | None = None) -> StorageConfig:
    """Load storage configuration.

    If project_dir is given, reads storage.yaml from that directory.
    Otherwise, walks up from cwd checking _project/ then .briefcase/.
    Returns default local config if file does not exist.
    Raises ValueError if the backend value is not recognized.
    """
    if project_dir is None:
        project_dir = _find_config_dir()
    else:
        project_dir = Path(project_dir)

    config_path = project_dir / STORAGE_CONFIG_FILENAME

    if not config_path.exists():
        return StorageConfig()

    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return StorageConfig()

    backend = raw.get("backend", DEFAULT_BACKEND)
    if backend not in VALID_BACKENDS:
        raise ValueError(
            f"Unknown backend '{backend}' in {config_path}. "
            f"Valid backends: {', '.join(VALID_BACKENDS)}"
        )

    notion_config = None
    if backend == "notion" and "notion" in raw:
        notion_raw = raw["notion"]
        notion_config = NotionConfig(
            parent_page_id=notion_raw.get("parent_page_id", ""),
            parent_page_url=notion_raw.get("parent_page_url", ""),
            databases=notion_raw.get("databases", {}),
            seeded_template_versions=notion_raw.get(
                "seeded_template_versions", {}
            ),
        )

    git_config = None
    if backend == "git" and "git" in raw:
        git_raw = raw["git"]
        git_config = GitConfig(
            remote=git_raw.get("remote", "origin"),
            remote_url=git_raw.get("remote_url", ""),
            branch=git_raw.get("branch", "main"),
            paths=git_raw.get("paths", ["docs/plan/", "_project/"]),
        )

    upstream_config = None
    if "upstream" in raw:
        upstream_raw = raw["upstream"]
        upstream_config = UpstreamConfig(
            feedback_repo=upstream_raw.get("feedback_repo", ""),
        )

    project_config = None
    if "project" in raw:
        project_raw = raw["project"] or {}
        project_config = ProjectConfig(
            name=project_raw.get("name", ""),
        )

    return StorageConfig(
        backend=backend,
        notion=notion_config,
        git=git_config,
        upstream=upstream_config,
        project=project_config,
    )


def resolve_config_dir(project_root: str | Path) -> Path:
    """Resolve config directory for a specific project root.

    Canonical precedence:
    1. _project/storage.yaml
    2. .briefcase/storage.yaml

    If both files exist and differ, raises ValueError to prevent silent drift.
    If neither exists, returns _project/ so callers can use local defaults.
    """
    root = Path(project_root).resolve()
    project_dir = root / "_project"
    briefcase_dir = root / ".briefcase"
    project_config_path = project_dir / STORAGE_CONFIG_FILENAME
    briefcase_config_path = briefcase_dir / STORAGE_CONFIG_FILENAME

    if project_config_path.exists():
        if (
            briefcase_config_path.exists()
            and not _config_files_match(project_config_path, briefcase_config_path)
        ):
            raise ValueError(
                "Config mismatch detected: _project/storage.yaml and "
                ".briefcase/storage.yaml both exist but differ. "
                "Use _project/storage.yaml as canonical and align or remove "
                ".briefcase/storage.yaml."
            )
        return project_dir

    if briefcase_config_path.exists():
        return briefcase_dir

    return project_dir


def _config_files_match(path_a: Path, path_b: Path) -> bool:
    """Return True when two YAML config files are semantically equal."""
    with open(path_a, "r") as f:
        raw_a = yaml.safe_load(f) or {}
    with open(path_b, "r") as f:
        raw_b = yaml.safe_load(f) or {}
    return raw_a == raw_b


def save_config(config: StorageConfig, project_dir: str | Path) -> Path:
    """Save storage configuration to _project/storage.yaml.

    Creates the file if it doesn't exist. Returns the path written.
    """
    project_dir = Path(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    config_path = project_dir / STORAGE_CONFIG_FILENAME

    data: dict[str, Any] = {"backend": config.backend}

    if config.git is not None:
        data["git"] = {
            "remote": config.git.remote,
            "remote_url": config.git.remote_url,
            "branch": config.git.branch,
            "paths": config.git.paths,
        }

    if config.notion is not None:
        data["notion"] = {
            "parent_page_id": config.notion.parent_page_id,
            "parent_page_url": config.notion.parent_page_url,
            "databases": config.notion.databases,
            "seeded_template_versions": config.notion.seeded_template_versions,
        }

    if config.upstream is not None and config.upstream.feedback_repo:
        data["upstream"] = {
            "feedback_repo": config.upstream.feedback_repo,
        }

    if config.project is not None and config.project.name:
        data["project"] = {
            "name": config.project.name,
        }

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return config_path
