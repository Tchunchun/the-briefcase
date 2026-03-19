"""One-time migration: create Briefs and Release Notes container pages
in the existing Notion workspace, copy existing briefs into the Briefs
container, and create release notes from local files.

Usage:
    export $(grep -v '^#' .env | xargs)
    python3 scripts/migrate_notion_pages.py

Idempotent — re-running skips pages that already exist.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.storage.config import load_config, save_config
from src.integrations.notion.client import NotionClient


def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent / "_project"
    config = load_config(project_dir)

    if not config.is_notion() or config.notion is None:
        print("Backend is not Notion. Nothing to migrate.")
        return

    client = NotionClient()
    parent_page_id = config.notion.parent_page_id
    dbs = config.notion.databases

    # --- Discover existing child pages under project root ---
    children = client.get_block_children(parent_page_id)
    existing_pages: dict[str, str] = {}  # title -> id
    skip_titles = {"README", "Templates", "Briefs", "Release Notes"}

    brief_pages: list[dict] = []

    for child in children:
        if child.get("type") != "child_page":
            continue
        title = child.get("child_page", {}).get("title", "")
        existing_pages[title] = child["id"]

        if title not in skip_titles:
            # Check if it looks like a brief page
            # (not a database, not a known system page)
            brief_pages.append({"title": title, "id": child["id"]})

    print(f"Found {len(brief_pages)} brief pages under project root")
    for bp in brief_pages:
        print(f"  - {bp['title']}")

    # --- Create Briefs container page ---
    briefs_page_id = dbs.get("briefs")
    if "Briefs" in existing_pages:
        briefs_page_id = existing_pages["Briefs"]
        print(f"✓ Briefs page already exists: {briefs_page_id}")
    elif briefs_page_id:
        print(f"✓ Briefs page already in config: {briefs_page_id}")
    else:
        briefs_page = client.create_page(parent_page_id, "Briefs", icon="📋")
        briefs_page_id = briefs_page["id"]
        print(f"✓ Created Briefs page: {briefs_page_id}")

    # --- Create Release Notes container page ---
    release_notes_page_id = dbs.get("release_notes")
    if "Release Notes" in existing_pages:
        release_notes_page_id = existing_pages["Release Notes"]
        print(f"✓ Release Notes page already exists: {release_notes_page_id}")
    elif release_notes_page_id:
        print(f"✓ Release Notes page already in config: {release_notes_page_id}")
    else:
        rn_page = client.create_page(parent_page_id, "Release Notes", icon="🚀")
        release_notes_page_id = rn_page["id"]
        print(f"✓ Created Release Notes page: {release_notes_page_id}")

    # --- Copy briefs into Briefs container ---
    # Read content from existing brief pages and create copies under Briefs page
    briefs_children = client.get_block_children(briefs_page_id)
    existing_brief_titles = set()
    for child in briefs_children:
        if child.get("type") == "child_page":
            existing_brief_titles.add(
                child.get("child_page", {}).get("title", "")
            )

    for bp in brief_pages:
        if bp["title"] in existing_brief_titles:
            print(f"  ⏭ Brief '{bp['title']}' already in Briefs page, skipping")
            continue

        # Read the body content from the existing page
        blocks = client.get_block_children(bp["id"])
        # Filter to supported block types for re-creation
        copyable_blocks = _filter_copyable_blocks(blocks)

        # Notion API limits children to 100 blocks per request
        client.create_page(
            briefs_page_id,
            bp["title"],
            icon="📄",
            children=copyable_blocks[:100],
        )
        print(f"  ✓ Copied brief '{bp['title']}' to Briefs page")

    # --- Create release notes from local files ---
    releases_dir = (
        Path(__file__).resolve().parent.parent / "docs" / "plan" / "_releases"
    )
    rn_children = client.get_block_children(release_notes_page_id)
    existing_rn_titles = set()
    for child in rn_children:
        if child.get("type") == "child_page":
            existing_rn_titles.add(
                child.get("child_page", {}).get("title", "")
            )

    if releases_dir.exists():
        for version_dir in sorted(releases_dir.iterdir()):
            if not version_dir.is_dir():
                continue
            rn_file = version_dir / "release-notes.md"
            if not rn_file.exists():
                continue

            version = version_dir.name
            page_title = f"{version} Release Notes"

            if page_title in existing_rn_titles:
                print(f"  ⏭ Release note '{page_title}' already exists, skipping")
                continue

            content = rn_file.read_text()
            blocks = _markdown_to_blocks(content)

            client.create_page(
                release_notes_page_id,
                page_title,
                icon="📦",
                children=blocks[:100],
            )
            print(f"  ✓ Created release note '{page_title}'")
    else:
        print("  No local release notes directory found")

    # --- Update storage.yaml ---
    config.notion.databases["briefs"] = briefs_page_id
    config.notion.databases["release_notes"] = release_notes_page_id
    save_config(config, project_dir)
    print(f"\n✓ Updated storage.yaml with briefs and release_notes page IDs")

    print("\nMigration complete!")
    print(
        "\nNote: Original brief pages under the project root still exist.\n"
        "You can archive them manually in Notion after verifying the copies."
    )


def _filter_copyable_blocks(blocks: list[dict]) -> list[dict]:
    """Extract blocks that can be re-created via the Notion API."""
    result = []
    for block in blocks:
        btype = block.get("type", "")
        if btype not in (
            "paragraph",
            "heading_1",
            "heading_2",
            "heading_3",
            "bulleted_list_item",
            "numbered_list_item",
            "to_do",
            "divider",
        ):
            continue

        data = block.get(btype, {})
        new_block: dict = {"type": btype}

        if btype == "divider":
            new_block["divider"] = {}
        else:
            rich_text = data.get("rich_text", [])
            # Strip annotation/link metadata for clean copy
            clean_rt = []
            for rt in rich_text:
                clean_rt.append(
                    {"type": "text", "text": {"content": rt.get("plain_text", "")}}
                )
            new_data: dict = {"rich_text": clean_rt}

            if btype == "to_do":
                new_data["checked"] = data.get("checked", False)

            new_block[btype] = new_data

        result.append(new_block)
    return result


def _markdown_to_blocks(content: str) -> list[dict]:
    """Convert markdown text to Notion block objects (simplified)."""
    blocks = []
    for line in content.split("\n"):
        if not line.strip():
            continue
        if line.startswith("# "):
            blocks.append(
                {
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": line[2:].strip()}}]
                    },
                }
            )
        elif line.startswith("## "):
            blocks.append(
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": line[3:].strip()}}]
                    },
                }
            )
        elif line.startswith("### "):
            blocks.append(
                {
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": line[4:].strip()}}]
                    },
                }
            )
        elif line.startswith("- [ ] ") or line.startswith("- [x] "):
            checked = line.startswith("- [x] ")
            blocks.append(
                {
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"text": {"content": line[6:].strip()}}],
                        "checked": checked,
                    },
                }
            )
        elif line.startswith("- "):
            blocks.append(
                {
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": line[2:].strip()}}]
                    },
                }
            )
        elif line.startswith("| "):
            # Tables can't be created as individual blocks in Notion API
            # Convert to paragraph
            blocks.append(
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": line}}]
                    },
                }
            )
        elif line.startswith("```"):
            # Skip code fence markers (content becomes paragraphs)
            continue
        else:
            blocks.append(
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": line}}]
                    },
                }
            )
    return blocks


if __name__ == "__main__":
    main()
