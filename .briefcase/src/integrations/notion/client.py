"""Thin wrapper around the notion-client SDK.

Provides a simplified interface for the operations needed by the storage
backend: create/query databases, create/update/query pages, and manage blocks.
All Notion API errors are allowed to propagate — callers handle them.
"""

from __future__ import annotations

import os
from typing import Any

from notion_client import Client


def get_notion_client(token: str | None = None) -> Client:
    """Create a Notion API client.

    Token resolution order:
    1. Explicit token parameter
    2. NOTION_API_KEY environment variable
    3. NOTION_API_TOKEN environment variable (legacy)
    4. Raises ValueError
    """
    token = token or os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_API_TOKEN")
    if not token:
        raise ValueError(
            "Notion API key not found. Set NOTION_API_KEY environment variable "
            "or pass token explicitly."
        )
    return Client(auth=token)


class NotionClient:
    """Simplified Notion API client for artifact storage operations."""

    def __init__(self, token: str | None = None) -> None:
        resolved_token = (
            token
            or os.environ.get("NOTION_API_KEY")
            or os.environ.get("NOTION_API_TOKEN")
        )
        if not resolved_token:
            raise ValueError(
                "Notion API key not found. Set NOTION_API_KEY environment variable "
                "or pass token explicitly."
            )
        self._token = resolved_token
        self._client = Client(auth=resolved_token)

    # -- Pages --

    def create_page(
        self,
        parent_id: str,
        title: str,
        *,
        icon: str | None = None,
        children: list[dict] | None = None,
    ) -> dict:
        """Create a page under a parent page."""
        properties = {"title": [{"text": {"content": title}}]}
        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "properties": properties,
        }
        if icon:
            params["icon"] = {"type": "emoji", "emoji": icon}
        if children:
            params["children"] = children
        return self._client.pages.create(**params)

    def get_page(self, page_id: str) -> dict:
        """Retrieve a page by ID."""
        return self._client.pages.retrieve(page_id=page_id)

    def update_page(self, page_id: str, properties: dict) -> dict:
        """Update page properties."""
        return self._client.pages.update(page_id=page_id, properties=properties)

    # -- Databases --

    def create_database(
        self,
        parent_id: str,
        title: str,
        properties: dict[str, dict],
        *,
        icon: str | None = None,
    ) -> dict:
        """Create a database under a parent page.

        Uses httpx directly because notion-client v3.0.0 SDK does not
        reliably pass custom properties through databases.create.
        """
        import httpx

        body: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }
        if icon:
            body["icon"] = {"type": "emoji", "emoji": icon}

        headers = {
            "Authorization": f"Bearer {self._client.options.auth}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        resp = httpx.post(
            "https://api.notion.com/v1/databases",
            headers=headers,
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def query_database(
        self,
        database_id: str,
        *,
        filter: dict | None = None,
        sorts: list[dict] | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """Query all pages in a database (handles pagination).

        Uses raw HTTP POST to /v1/databases/{id}/query since
        notion-client v3 removed databases.query().
        """
        import httpx

        body: dict[str, Any] = {
            "page_size": min(page_size, 100),
        }
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        results = []
        has_more = True
        start_cursor = None

        while has_more:
            if start_cursor:
                body["start_cursor"] = start_cursor
            resp = httpx.post(
                f"https://api.notion.com/v1/databases/{database_id}/query",
                json=body,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return results

    def get_database(self, database_id: str) -> dict:
        """Retrieve database metadata."""
        return self._client.databases.retrieve(database_id=database_id)

    def update_database(
        self,
        database_id: str,
        properties: dict[str, dict],
    ) -> dict:
        """Update a database's properties (e.g., add a self-relation).

        Uses httpx directly because notion-client v3.0.0 SDK does not
        reliably pass property updates through databases.update.
        """
        import httpx

        body: dict[str, Any] = {"properties": properties}
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        resp = httpx.patch(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=headers,
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # -- Database pages (rows) --

    def create_database_page(
        self,
        database_id: str,
        properties: dict,
        *,
        children: list[dict] | None = None,
    ) -> dict:
        """Create a page (row) in a database."""
        params: dict[str, Any] = {
            "parent": {"type": "database_id", "database_id": database_id},
            "properties": properties,
        }
        if children:
            params["children"] = children
        return self._client.pages.create(**params)

    def update_database_page(self, page_id: str, properties: dict) -> dict:
        """Update a database page's properties."""
        return self._client.pages.update(page_id=page_id, properties=properties)

    # -- Blocks (page content) --

    def get_block_children(self, block_id: str) -> list[dict]:
        """Get all child blocks of a page/block (handles pagination)."""
        results = []
        has_more = True
        start_cursor = None

        while has_more:
            params: dict[str, Any] = {"block_id": block_id, "page_size": 100}
            if start_cursor:
                params["start_cursor"] = start_cursor
            response = self._client.blocks.children.list(**params)
            results.extend(response.get("results", []))
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return results

    def append_block_children(self, block_id: str, children: list[dict]) -> dict:
        """Append child blocks to a page/block."""
        return self._client.blocks.children.append(
            block_id=block_id, children=children
        )

    # -- Search --

    def search_pages(
        self, query: str, *, filter_type: str | None = None
    ) -> list[dict]:
        """Search for pages/databases by title."""
        params: dict[str, Any] = {"query": query}
        if filter_type:
            params["filter"] = {"property": "object", "value": filter_type}
        response = self._client.search(**params)
        return response.get("results", [])
