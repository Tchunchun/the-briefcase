"""Launcher integration checks without installing dependencies or using a remote."""

import json
import os
import subprocess
import sys
from pathlib import Path

import click
import pytest

from src.cli.main import cli
from src.core.storage.local_backend import LocalBackend


ROOT = Path(__file__).resolve().parents[3]


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True,
    )


def run_launcher(launcher, cwd, *args):
    env = os.environ.copy()
    env.pop("BRIEFCASE_PROJECT_ROOT", None)
    return subprocess.run(
        ["bash", str(launcher), *args], cwd=cwd,
        capture_output=True, text=True, env=env, timeout=15,
    )


def generate_launcher(root):
    installer = (ROOT / "install.sh").read_text()
    start = installer.index('echo "  [3/$TOTAL_STEPS]')
    end = installer.index("# --- 4.", start)
    env = {
        **os.environ,
        "FRAMEWORK_DIR": str(ROOT),
        "TARGET_DIR": str(root),
        "TOTAL_STEPS": "7",
    }
    result = subprocess.run(
        ["bash", "-eu", "-c", installer[start:end]],
        capture_output=True, text=True, env=env, check=True,
    )
    assert "./briefcase created" in result.stdout
    launcher = root / "briefcase"
    assert launcher.read_text() == (ROOT / "template" / "briefcase.sh").read_text()
    assert os.access(launcher, os.X_OK)


@pytest.fixture
def consumer(tmp_path):
    root = tmp_path / "main checkout's files"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test User")
    git(root, "config", "user.email", "test@example.invalid")
    (root / ".gitignore").write_text(".briefcase/\n")
    generate_launcher(root)
    framework = root / ".briefcase"
    framework.mkdir()
    (framework / "src").symlink_to(ROOT / "src", target_is_directory=True)
    (framework / ".venv" / "bin").mkdir(parents=True)
    (framework / ".venv" / "bin" / "python").symlink_to(sys.executable)
    (root / "_project").mkdir()
    config = "backend: local\nproject:\n  name: Main checkout\n"
    (root / "_project" / "storage.yaml").write_text(config)
    (framework / "storage.yaml").write_text(config)
    LocalBackend(str(root)).write_brief(
        "example", {"title": "Main title", "problem": "Main problem"}
    )
    git(root, "add", ".")
    git(root, "commit", "-m", "Initialize consumer")
    return root


@pytest.fixture(params=["external", "nested"])
def worktree(consumer, tmp_path, request):
    root = (
        tmp_path / "external worktree's files"
        if request.param == "external"
        else consumer / ".claude" / "worktrees" / "task"
    )
    git(consumer, "worktree", "add", "-b", "task", str(root))
    (root / "_project" / "storage.yaml").write_text(
        "backend: local\nproject:\n  name: Worktree\n"
    )
    LocalBackend(str(root)).write_brief(
        "example", {"title": "Worktree title", "problem": "Worktree problem"}
    )
    return root


@pytest.mark.parametrize("use_main_launcher", [False, True])
def test_worktree_reads_its_own_artifacts(consumer, worktree, use_main_launcher):
    subdir = worktree / "nested"
    subdir.mkdir()
    launcher = (consumer if use_main_launcher else worktree) / "briefcase"
    result = run_launcher(launcher, subdir, "brief", "read", "example")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["data"]["title"] == "Worktree title"
    assert not (worktree / ".briefcase").exists()


def test_worktree_write_keeps_relative_file_and_project_paths(consumer, worktree):
    subdir = worktree / "nested"
    subdir.mkdir()
    (subdir / "partial.md").write_text("## Problem\nUpdated from worktree\n")
    result = run_launcher(
        worktree / "briefcase", subdir,
        "brief", "write", "example", "--file", "partial.md",
    )
    assert result.returncode == 0, result.stderr
    assert LocalBackend(str(worktree)).read_brief("example")["problem"] == (
        "Updated from worktree"
    )
    assert LocalBackend(str(worktree)).read_brief("example")["project"] == "Worktree"
    assert LocalBackend(str(consumer)).read_brief("example")["problem"] == "Main problem"
    assert not (subdir / "docs").exists()


def test_explicit_project_dir_overrides_worktree_default(consumer, worktree):
    result = run_launcher(
        worktree / "briefcase", worktree,
        "brief", "read", "example", "--project-dir", str(consumer),
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["data"]["title"] == "Main title"


def test_missing_worktree_config_fails_without_inheriting_main(consumer, worktree):
    (worktree / "_project" / "storage.yaml").unlink()
    result = run_launcher(worktree / "briefcase", worktree, "brief", "read", "example")
    assert result.returncode != 0
    assert "worktree" in result.stderr.lower()
    assert "storage.yaml" in result.stderr
    assert not (worktree / ".briefcase").exists()


def test_worktree_without_config_can_show_help_and_initialize(consumer, worktree):
    config = worktree / "_project" / "storage.yaml"
    config.unlink()
    result = run_launcher(worktree / "briefcase", worktree, "--help")
    assert result.returncode == 0, result.stderr
    result = run_launcher(
        worktree / "briefcase", worktree, "setup", "--backend", "local"
    )
    assert result.returncode == 0, result.stderr
    assert config.is_file()
    assert "Main checkout" in (
        consumer / "_project" / "storage.yaml"
    ).read_text()


def test_explicit_project_dir_works_without_worktree_config(consumer, worktree):
    (worktree / "_project" / "storage.yaml").unlink()
    result = run_launcher(
        worktree / "briefcase", worktree,
        "brief", "read", "example", "--project-dir", str(consumer),
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["data"]["title"] == "Main title"


def test_worktree_runtime_cache_does_not_hide_shared_framework(consumer, worktree):
    (worktree / ".briefcase" / "git-sync" / "example").mkdir(parents=True)
    result = run_launcher(worktree / "briefcase", worktree, "brief", "read", "example")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["data"]["title"] == "Worktree title"


def test_main_checkout_subdirectory_keeps_project_root_and_relative_file(consumer):
    subdir = consumer / "nested"
    subdir.mkdir()
    (subdir / "partial.md").write_text("## Problem\nMain subdirectory update\n")
    result = run_launcher(
        consumer / "briefcase", subdir,
        "brief", "write", "example", "--file", "partial.md",
    )
    assert result.returncode == 0, result.stderr
    assert LocalBackend(str(consumer)).read_brief("example")["problem"] == (
        "Main subdirectory update"
    )
    assert not (subdir / "docs").exists()


def test_non_git_project_keeps_sentinel_root_behavior(consumer, tmp_path):
    root = tmp_path / "non-git consumer"
    root.mkdir()
    (root / ".briefcase").symlink_to(
        consumer / ".briefcase", target_is_directory=True
    )
    generate_launcher(root)
    LocalBackend(str(root)).write_brief("example", {"title": "Non-Git title"})
    subdir = root / "nested"
    subdir.mkdir()
    result = run_launcher(root / "briefcase", subdir, "brief", "read", "example")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["data"]["title"] == "Non-Git title"


def test_every_project_option_uses_launcher_default():
    def check(command):
        for param in command.params:
            if param.name == "project_dir":
                assert param.envvar == "BRIEFCASE_PROJECT_ROOT", command.name
        if isinstance(command, click.Group):
            for child in command.commands.values():
                check(child)

    check(cli)
