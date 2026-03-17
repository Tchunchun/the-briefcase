"""Tests for NotionClient wrapper with mocked HTTP."""

import pytest
from unittest.mock import MagicMock, patch

from src.integrations.notion.client import NotionClient, get_notion_client


# --- Token resolution ---


def test_get_notion_client_with_explicit_token():
    with patch("src.integrations.notion.client.Client") as mock_cls:
        client = get_notion_client(token="test-token")
        mock_cls.assert_called_once_with(auth="test-token")


def test_get_notion_client_from_env(monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "env-token")
    monkeypatch.delenv("NOTION_API_TOKEN", raising=False)
    with patch("src.integrations.notion.client.Client") as mock_cls:
        client = get_notion_client()
        mock_cls.assert_called_once_with(auth="env-token")


def test_get_notion_client_raises_without_token(monkeypatch):
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_API_TOKEN", raising=False)
    with pytest.raises(ValueError, match="Notion API key not found"):
        get_notion_client()


# --- NotionClient methods ---


@pytest.fixture
def client():
    with patch("src.integrations.notion.client.Client") as mock_cls:
        mock_api = MagicMock()
        mock_cls.return_value = mock_api
        nc = NotionClient(token="test")
        nc._mock_api = mock_api  # expose for assertions
        yield nc


def test_create_page(client):
    client._mock_api.pages.create.return_value = {"id": "page-1"}
    result = client.create_page("parent-1", "Test Page", icon="📋")
    assert result["id"] == "page-1"
    call_kwargs = client._mock_api.pages.create.call_args
    assert call_kwargs.kwargs["parent"] == {"type": "page_id", "page_id": "parent-1"}


def test_get_page(client):
    client._mock_api.pages.retrieve.return_value = {"id": "page-1"}
    result = client.get_page("page-1")
    assert result["id"] == "page-1"


def test_create_database(client):
    """Test create_database uses httpx directly."""
    import httpx
    from unittest.mock import patch as _patch
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "db-1", "properties": {"Name": {"title": {}}}}
    mock_resp.raise_for_status = MagicMock()
    with _patch("httpx.post", return_value=mock_resp) as mock_post:
        props = {"Name": {"title": {}}}
        result = client.create_database("parent-1", "Test DB", props, icon="\U0001f4ca")
        assert result["id"] == "db-1"
        mock_post.assert_called_once()


def test_query_database_single_page(client):
    from unittest.mock import patch as _patch
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [{"id": "row-1"}, {"id": "row-2"}],
        "has_more": False,
        "next_cursor": None,
    }
    mock_resp.raise_for_status = MagicMock()
    with _patch("httpx.post", return_value=mock_resp):
        results = client.query_database("db-1")
    assert len(results) == 2


def test_query_database_pagination(client):
    from unittest.mock import patch as _patch
    mock_resp_1 = MagicMock()
    mock_resp_1.status_code = 200
    mock_resp_1.json.return_value = {
        "results": [{"id": "row-1"}],
        "has_more": True,
        "next_cursor": "cursor-2",
    }
    mock_resp_1.raise_for_status = MagicMock()

    mock_resp_2 = MagicMock()
    mock_resp_2.status_code = 200
    mock_resp_2.json.return_value = {
        "results": [{"id": "row-2"}],
        "has_more": False,
        "next_cursor": None,
    }
    mock_resp_2.raise_for_status = MagicMock()

    with _patch("httpx.post", side_effect=[mock_resp_1, mock_resp_2]) as mock_post:
        results = client.query_database("db-1")
    assert len(results) == 2
    assert mock_post.call_count == 2


def test_create_database_page(client):
    client._mock_api.pages.create.return_value = {"id": "row-1"}
    result = client.create_database_page("db-1", {"Title": {"title": []}})
    assert result["id"] == "row-1"
    call_kwargs = client._mock_api.pages.create.call_args
    assert call_kwargs.kwargs["parent"] == {"type": "database_id", "database_id": "db-1"}


def test_get_block_children_pagination(client):
    client._mock_api.blocks.children.list.side_effect = [
        {
            "results": [{"type": "paragraph", "id": "b1"}],
            "has_more": True,
            "next_cursor": "c2",
        },
        {
            "results": [{"type": "heading_1", "id": "b2"}],
            "has_more": False,
            "next_cursor": None,
        },
    ]
    blocks = client.get_block_children("page-1")
    assert len(blocks) == 2


def test_append_block_children(client):
    client._mock_api.blocks.children.append.return_value = {"results": []}
    children = [{"type": "paragraph", "paragraph": {"rich_text": []}}]
    client.append_block_children("page-1", children)
    client._mock_api.blocks.children.append.assert_called_once()


def test_search_pages(client):
    client._mock_api.search.return_value = {"results": [{"id": "p1"}]}
    results = client.search_pages("test", filter_type="page")
    assert len(results) == 1
