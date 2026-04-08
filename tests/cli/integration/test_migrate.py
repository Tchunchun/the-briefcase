"""Integration tests for migrate CLI commands."""

import yaml
from click.testing import CliRunner
from unittest.mock import patch

from src.cli.main import cli
from src.core.storage.config import load_config


def test_migrate_notion_to_git_rewrites_storage_and_pushes(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "_project").mkdir()
    (root / "docs" / "plan" / "_shared").mkdir(parents=True)
    (root / "template").mkdir()
    (root / ".env").write_text("NOTION_API_KEY=test-token\n")
    (root / "_project" / "storage.yaml").write_text(
        yaml.safe_dump(
            {
                "backend": "notion",
                "notion": {
                    "parent_page_id": "parent-1",
                    "parent_page_url": "https://notion.so/parent-1",
                    "databases": {
                        "intake": "db-i",
                        "briefs": "db-b",
                        "decisions": "db-d",
                        "backlog": "db-bl",
                        "templates": "db-t",
                    },
                },
            },
            sort_keys=False,
        )
    )

    runner = CliRunner()

    with patch("src.sync.to_local.sync_to_local") as mock_sync, patch(
        "src.sync.git_sync.GitSync.configure_remote"
    ) as mock_configure_remote, patch(
        "src.sync.git_sync.GitSync.push"
    ) as mock_push:
        mock_sync.return_value = {
            "fetched": 3,
            "created": 3,
            "skipped": 0,
            "failed": 0,
            "conflicts": 0,
        }
        mock_configure_remote.return_value = True
        mock_push.return_value = {
            "committed": 1,
            "pushed": True,
            "dry_run": False,
            "message": "Pushed artifact snapshot for demo-project to origin/main.",
        }

        result = runner.invoke(
            cli,
            [
                "migrate",
                "notion-to-git",
                "--remote-url",
                "https://github.com/example/private-artifacts.git",
                "--project-dir",
                str(root),
            ],
            input="y\n",
        )

    assert result.exit_code == 0, result.output
    assert "Migration complete" in result.output
    assert "sync shakedown-git" in result.output or "Next steps:" in result.output

    config = load_config(root / "_project")
    assert config.backend == "git"
    assert config.git is not None
    assert config.git.remote_url == "https://github.com/example/private-artifacts.git"
    assert config.git.remote == "origin"
    assert config.git.branch == "main"
    mock_sync.assert_called_once()
    mock_configure_remote.assert_called_once_with(
        "https://github.com/example/private-artifacts.git"
    )
    mock_push.assert_called_once_with(dry_run=False)