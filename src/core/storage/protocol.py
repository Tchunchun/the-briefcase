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

    def read_inbox(self, since: str | None = None) -> list[dict]:
        """Return all inbox entries.

        Each entry is a dict with at least:
        {text, type, status, notes, created_at, updated_at}.
        text is a short title (3-7 words). notes holds the longer description.
        If since is provided (YYYY-MM-DD), return only entries with
        updated_at on/after that date.
        """
        ...

    def append_inbox(self, entry: dict) -> None:
        """Append a single entry to the inbox.

        entry must include at least: {text, type}.
        Optional: {notes, priority} for longer description/context and
        priority classification.
        text should be a short title (3-7 words).
        """
        ...

    # -- Briefs --

    def read_brief(self, brief_name: str) -> dict:
        """Return structured brief data for a given brief.

        Returns a dict with keys matching brief.md sections:
        {name, status, problem, goal, acceptance_criteria,
         non_functional_requirements, out_of_scope, open_questions,
         technical_approach}.
        Raises KeyError if brief_name does not exist.
        """
        ...

    def write_brief(self, brief_name: str, data: dict) -> None:
        """Create or update a brief.

        data must include at least: {status, problem, goal, acceptance_criteria}.

        Optional revision-tracking keys (consumed by backends, not stored
        in the brief body):
          _actor: str — who made the change (defaults to $USER).
          _change_summary: str — human description of the change.
        """
        ...

    def list_briefs(self) -> list[dict]:
        """Return summaries of all briefs, sorted newest-first.

        Each summary is a dict with: {name, status, title, date}.
        date is an ISO-8601 date string (YYYY-MM-DD) derived from the
        page's last-modified time (Notion) or file mtime (local).
        Results are sorted by date descending (most recent first).
        """
        ...

    def list_brief_revisions(self, brief_name: str) -> list[dict]:
        """Return revision metadata for a brief, newest first."""
        ...

    def read_brief_revision(self, brief_name: str, revision_id: str) -> dict:
        """Return a stored brief revision plus its snapshot content."""
        ...

    def restore_brief_revision(
        self,
        brief_name: str,
        revision_id: str,
        *,
        actor: str = "",
        change_summary: str = "",
    ) -> dict:
        """Restore a revision into the brief head without mutating history."""
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

    def read_backlog(self, since: str | None = None) -> list[dict]:
        """Return all backlog rows.

        Each row is a dict with: {id, type, use_case, feature, title,
        priority, status, notes, created_at, updated_at}.
        If since is provided (YYYY-MM-DD), return only rows with
        updated_at on/after that date.
        """
        ...

    def write_backlog_row(self, row: dict) -> None:
        """Create or update a backlog row.

        row must include at least: {title, type, status}.
        Optional: {id, feature, use_case, priority, notes, brief_link,
        release_note_link, review_verdict, route_state, parent_ids}.

        Lookup precedence: by id if present, then by title + type.
        If no match is found, a new row is appended.
        """
        ...

    def list_children(self, parent_id: str) -> list[dict]:
        """Return child Feature rows for the given parent backlog item id.

        parent_id should be a Notion/local row identifier used in parent_ids.
        Returns only Feature rows directly linked to parent_id (one level).
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
