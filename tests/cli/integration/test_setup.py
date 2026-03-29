"""Tests for the agent setup CLI command."""

import click
import pytest
import yaml
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
            input="test-token-123\n325b5a09fa4a806a815cdd28b79e38cb\n",
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
    assert data["notion"]["parent_page_id"] == "325b5a09fa4a806a815cdd28b79e38cb"

    # Verify seeded template versions recorded
    assert data["notion"]["seeded_template_versions"]["brief"] == "v3"
    assert data["notion"]["seeded_template_versions"]["tasks"] == "v2"

    # Verify .env token
    env_path = project / ".env"
    assert env_path.exists()
    assert "NOTION_API_KEY=test-token-123" in env_path.read_text()


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
            input="token\n325b5a09fa4a806a815cdd28b79e38cb\n",
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
            input="token\n325b5a09fa4a806a815cdd28b79e38cb\n",
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


# --- Guided Notion onboarding tests ---

class TestParsePageId:
    """Unit tests for _parse_page_id helper (AC 4)."""

    def test_raw_hex_32(self):
        from src.cli.commands.setup import _parse_page_id
        assert _parse_page_id("325b5a09fa4a806a815cdd28b79e38cb") == "325b5a09fa4a806a815cdd28b79e38cb"

    def test_hex_with_hyphens(self):
        from src.cli.commands.setup import _parse_page_id
        assert _parse_page_id("325b5a09-fa4a-806a-815c-dd28b79e38cb") == "325b5a09fa4a806a815cdd28b79e38cb"

    def test_full_notion_url(self):
        from src.cli.commands.setup import _parse_page_id
        url = "https://www.notion.so/My-Page-Title-325b5a09fa4a806a815cdd28b79e38cb"
        assert _parse_page_id(url) == "325b5a09fa4a806a815cdd28b79e38cb"

    def test_notion_url_with_query_params(self):
        from src.cli.commands.setup import _parse_page_id
        url = "https://www.notion.so/325b5a09fa4a806a815cdd28b79e38cb?v=abc"
        assert _parse_page_id(url) == "325b5a09fa4a806a815cdd28b79e38cb"

    def test_whitespace_stripped(self):
        from src.cli.commands.setup import _parse_page_id
        assert _parse_page_id("  325b5a09fa4a806a815cdd28b79e38cb  ") == "325b5a09fa4a806a815cdd28b79e38cb"

    def test_invalid_input_raises(self):
        from src.cli.commands.setup import _parse_page_id
        with pytest.raises(click.BadParameter):
            _parse_page_id("not-a-valid-id")

    def test_short_hex_raises(self):
        from src.cli.commands.setup import _parse_page_id
        with pytest.raises(click.BadParameter):
            _parse_page_id("325b5a09fa4a")


class TestGuidedOnboardingOutput:
    """Integration tests for guided onboarding output (AC 1-3, 5)."""

    def test_inline_checklist_shown(self, runner, project):
        """AC 1: Inline checklist is printed before token prompt."""
        from src.integrations.notion.provisioner import ProvisionResult
        mock_result = ProvisionResult()
        mock_result.databases_created = ["backlog"]

        with patch("src.integrations.notion.client.NotionClient"), \
             patch("src.integrations.notion.provisioner.NotionProvisioner") as mock_prov_cls:
            mock_prov = MagicMock()
            mock_prov.provision.return_value = ({"backlog": "x"}, mock_result)
            mock_prov_cls.return_value = mock_prov

            result = runner.invoke(
                setup,
                ["--backend", "notion", "--project-dir", str(project)],
                input="tok\n325b5a09fa4a806a815cdd28b79e38cb\n",
            )

        assert "Before you begin" in result.output
        assert "notion.so/my-integrations" in result.output
        assert "parent" in result.output.lower()
        assert "Connect to" in result.output

    def test_token_prompt_has_hint(self, runner, project):
        """AC 2: Token prompt includes notion.so/my-integrations hint."""
        from src.integrations.notion.provisioner import ProvisionResult
        mock_result = ProvisionResult()
        mock_result.databases_created = ["backlog"]

        with patch("src.integrations.notion.client.NotionClient"), \
             patch("src.integrations.notion.provisioner.NotionProvisioner") as mock_prov_cls:
            mock_prov = MagicMock()
            mock_prov.provision.return_value = ({"backlog": "x"}, mock_result)
            mock_prov_cls.return_value = mock_prov

            result = runner.invoke(
                setup,
                ["--backend", "notion", "--project-dir", str(project)],
                input="tok\n325b5a09fa4a806a815cdd28b79e38cb\n",
            )

        assert "Notion API token (from https://www.notion.so/my-integrations)" in result.output

    def test_sharing_reminder_shown(self, runner, project):
        """AC 3: Sharing reminder printed above parent page prompt."""
        from src.integrations.notion.provisioner import ProvisionResult
        mock_result = ProvisionResult()
        mock_result.databases_created = ["backlog"]

        with patch("src.integrations.notion.client.NotionClient"), \
             patch("src.integrations.notion.provisioner.NotionProvisioner") as mock_prov_cls:
            mock_prov = MagicMock()
            mock_prov.provision.return_value = ({"backlog": "x"}, mock_result)
            mock_prov_cls.return_value = mock_prov

            result = runner.invoke(
                setup,
                ["--backend", "notion", "--project-dir", str(project)],
                input="tok\n325b5a09fa4a806a815cdd28b79e38cb\n",
            )

        assert "Reminder: the parent page must be shared" in result.output

    def test_notion_url_accepted_as_parent_page(self, runner, project):
        """AC 4: Full Notion URL accepted and ID extracted."""
        from src.integrations.notion.provisioner import ProvisionResult
        mock_result = ProvisionResult()
        mock_result.databases_created = ["backlog"]

        with patch("src.integrations.notion.client.NotionClient"), \
             patch("src.integrations.notion.provisioner.NotionProvisioner") as mock_prov_cls:
            mock_prov = MagicMock()
            mock_prov.provision.return_value = ({"backlog": "x"}, mock_result)
            mock_prov_cls.return_value = mock_prov

            result = runner.invoke(
                setup,
                ["--backend", "notion", "--project-dir", str(project)],
                input="tok\nhttps://www.notion.so/My-Page-325b5a09fa4a806a815cdd28b79e38cb\n",
            )

        assert result.exit_code == 0, result.output
        config_path = project / "_project" / "storage.yaml"
        data = yaml.safe_load(config_path.read_text())
        assert data["notion"]["parent_page_id"] == "325b5a09fa4a806a815cdd28b79e38cb"

    def test_piped_stdin_works(self, runner, project):
        """AC 5: Non-interactive piped-stdin usage still works."""
        from src.integrations.notion.provisioner import ProvisionResult
        mock_result = ProvisionResult()
        mock_result.databases_created = ["backlog"]

        with patch("src.integrations.notion.client.NotionClient"), \
             patch("src.integrations.notion.provisioner.NotionProvisioner") as mock_prov_cls:
            mock_prov = MagicMock()
            mock_prov.provision.return_value = ({"backlog": "x"}, mock_result)
            mock_prov_cls.return_value = mock_prov

            result = runner.invoke(
                setup,
                ["--backend", "notion", "--project-dir", str(project)],
                input="tok\n325b5a09fa4a806a815cdd28b79e38cb\n",
            )

        assert result.exit_code == 0, result.output
