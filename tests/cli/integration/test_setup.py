"""Tests for the agent setup CLI command."""

import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from src.cli.commands.setup import setup


@pytest.fixture
def project(tmp_path):
    (tmp_path / "_project").mkdir()
    (tmp_path / "docs" / "plan" / "_shared").mkdir(parents=True)
    tpl = tmp_path / "template"
    tpl.mkdir()
    (tpl / "brief.md").write_text("# {Feature Name} (v3)\n\n**Status: draft**\n")
    (tpl / "tasks.md").write_text("# Tasks (v2)\n")
    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


def test_setup_local_backend(runner, project):
    result = runner.invoke(setup, ["--backend", "local", "--project-dir", str(project)])
    assert result.exit_code == 0
    assert "Backend: local" in result.output

    config_path = project / "_project" / "storage.yaml"
    assert config_path.exists()
    data = yaml.safe_load(config_path.read_text())
    assert data["backend"] == "local"


def test_setup_notion_backend_provisions_and_saves_db_ids(runner, project):
    """Blocking #1-3: Setup must call provisioner, seed templates, save DB IDs."""
    from src.integrations.notion.provisioner import ProvisionResult

    mock_result = ProvisionResult()
    mock_result.databases_created = ["intake", "briefs", "decisions", "backlog", "templates"]
    mock_result.templates_seeded = ["brief", "tasks"]

    mock_db_ids = {
        "intake": "db-i1",
        "briefs": "db-b1",
        "decisions": "db-d1",
        "backlog": "db-bl1",
        "templates": "db-t1",
    }

    with patch("src.integrations.notion.client.NotionClient") as mock_client_cls, \
         patch("src.integrations.notion.provisioner.NotionProvisioner") as mock_prov_cls:

        mock_prov = MagicMock()
        mock_prov.provision.return_value = (mock_db_ids, mock_result)
        mock_prov_cls.return_value = mock_prov

        result = runner.invoke(
            setup,
            ["--backend", "notion", "--project-dir", str(project)],
            input="test-token-123\nabc-page-id\n",
        )

    assert result.exit_code == 0, result.output
    assert "Databases created: 5" in result.output
    assert "Templates seeded: 2" in result.output

    # Verify DB IDs saved in storage.yaml
    config_path = project / "_project" / "storage.yaml"
    data = yaml.safe_load(config_path.read_text())
    assert data["backend"] == "notion"
    assert data["notion"]["databases"]["intake"] == "db-i1"
    assert data["notion"]["databases"]["templates"] == "db-t1"
    assert data["notion"]["parent_page_id"] == "abc-page-id"

    # Verify seeded template versions recorded
    assert data["notion"]["seeded_template_versions"]["brief"] == "v3"
    assert data["notion"]["seeded_template_versions"]["tasks"] == "v2"

    # Verify .env token
    env_path = project / ".env"
    assert env_path.exists()
    assert "NOTION_API_TOKEN=test-token-123" in env_path.read_text()


def test_setup_notion_fails_on_provision_error(runner, project):
    from src.integrations.notion.provisioner import ProvisionResult

    mock_result = ProvisionResult()
    mock_result.errors = ["Failed to create database 'intake': API error"]

    with patch("src.integrations.notion.client.NotionClient"), \
         patch("src.integrations.notion.provisioner.NotionProvisioner") as mock_prov_cls:

        mock_prov = MagicMock()
        mock_prov.provision.return_value = ({}, mock_result)
        mock_prov_cls.return_value = mock_prov

        result = runner.invoke(
            setup,
            ["--backend", "notion", "--project-dir", str(project)],
            input="token\npage-id\n",
        )

    assert result.exit_code != 0
    assert "provisioning failed" in result.output.lower()


def test_setup_notion_adds_env_to_gitignore(runner, project):
    gitignore = project / ".gitignore"
    gitignore.write_text("*.pyc\n")

    with patch("src.integrations.notion.client.NotionClient"), \
         patch("src.integrations.notion.provisioner.NotionProvisioner") as mock_prov_cls:
        from src.integrations.notion.provisioner import ProvisionResult
        mock_result = ProvisionResult()
        mock_result.databases_created = ["intake", "briefs", "decisions", "backlog", "templates"]
        mock_prov = MagicMock()
        mock_prov.provision.return_value = ({"intake": "x", "briefs": "x", "decisions": "x", "backlog": "x", "templates": "x"}, mock_result)
        mock_prov_cls.return_value = mock_prov

        runner.invoke(
            setup,
            ["--backend", "notion", "--project-dir", str(project)],
            input="token\npage-id\n",
        )

    assert ".env" in gitignore.read_text()


def test_setup_interactive_defaults_to_local(runner, project):
    result = runner.invoke(
        setup,
        ["--project-dir", str(project)],
        input="local\n",
    )
    assert result.exit_code == 0
    assert "Backend: local" in result.output
