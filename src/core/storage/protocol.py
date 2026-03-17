"""Storage interface protocols for pluggable artifact backends.

Defines ArtifactStore (required for all backends) and SyncableStore
(required for cloud backends that support syncing to local files).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ArtifactStore(Protocol):
    """Protocol for pluggable artifact storage backends.

    Every backend (local, Notion, future) must implement all methods.
    Agents and CLI commands interact with artifacts exclusively through
    this interface — never by accessing file paths or APIs directly.
    """

    # -- Inbox --

    def read_inbox(self) -> list[dict]:
        """Return all inbox entries.

        Each entry is a dict with at least: {text, type, status, notes}.
        text is a short title (3-7 words). notes holds the longer description.
        """
        ...

    def append_inbox(self, entry: dict) -> None:
        """Append a single entry to the inbox.

        entry must include at least: {text, type}.
        Optional: {notes} for longer description/context.
        text should be a short title (3-7 words).
        """
        ...

    # -- Briefs --

    def read_brief(self, brief_name: str) -> dict:
        """Return structured brief data for a given brief.

        Returns a dict with keys matching brief.md sections:
        {name, status, problem, goal, acceptance_criteria, nfrs,
         out_of_scope, open_questions, technical_approach}.
        Raises KeyError if brief_name does not exist.
        """
        ...

    def write_brief(self, brief_name: str, data: dict) -> None:
        """Create or update a brief.

        data must include at least: {status, problem, goal, acceptance_criteria}.
        """
        ...

    def list_briefs(self) -> list[dict]:
        """Return summaries of all briefs.

        Each summary is a dict with: {name, status, title}.
        """
        ...

    # -- Decisions --

    def read_decisions(self) -> list[dict]:
        """Return all decision log entries.

        Each entry is a dict with: {id, title, date, status, why,
        alternatives_rejected, adr_link}.
        """
        ...

    def append_decision(self, entry: dict) -> None:
        """Append a decision to the log.

        entry must include at least: {id, title, date, status, why}.
        """
        ...

    # -- Backlog --

    def read_backlog(self) -> list[dict]:
        """Return all backlog rows.

        Each row is a dict with: {id, type, use_case, feature, title,
        priority, status, notes}.
        """
        ...

    def write_backlog_row(self, row: dict) -> None:
        """Create or update a backlog row by ID.

        row must include at least: {id, type, feature, title, priority, status}.
        If a row with the same ID exists, it is updated. Otherwise, appended.
        """
        ...

    # -- Release Notes --

    def write_release_note(self, version: str, content: str) -> None:
        """Create or overwrite a release note for the given version.

        version: version string (e.g., 'v0.5.0'), used as primary key.
        content: full release note text in markdown.
        """
        ...

    def read_release_note(self, version: str) -> dict:
        """Return release note data for a given version.

        Returns a dict with at least: {version, title, content}.
        Backend-specific metadata (e.g., notion_id) may be included.
        Raises KeyError if the version does not exist.
        """
        ...

    def list_release_notes(self) -> list[dict]:
        """Return summaries of all release notes.

        Each entry is a dict with at least: {version, title}.
        """
        ...

    # -- Templates --

    def read_templates(self) -> list[dict]:
        """Return all templates with name, version, and content.

        Each entry is a dict with: {name, version, content}.
        """
        ...

    def write_template(self, name: str, content: str, version: str) -> None:
        """Create or update a template.

        name: template identifier (e.g., 'brief', 'tasks').
        content: full template text.
        version: version string (e.g., 'v3').
        """
        ...


@runtime_checkable
class SyncableStore(Protocol):
    """Protocol for cloud backends that support syncing to local files.

    Cloud backends (Notion, future) implement this in addition to
    ArtifactStore. The local backend does NOT implement this.
    """

    def sync_to_local(self, target_dir: str, *, dry_run: bool = False) -> dict:
        """Generate local markdown files from the cloud backend.

        target_dir: root project directory containing docs/plan/, _project/, etc.
        dry_run: if True, compute what would change but write nothing.

        Returns a summary dict: {fetched: int, created: int, skipped: int, failed: int}.
        """
        ...

    def sync_templates_to_local(
        self, template_dir: str, *, dry_run: bool = False
    ) -> dict:
        """Pull templates from the cloud backend to local template/ files.

        Compares versions before overwriting. Skips if local is same or newer.

        Returns a summary dict: {fetched: int, updated: int, skipped: int, failed: int}.
        """
        ...
