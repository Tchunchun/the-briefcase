"""ArtifactService — first-class callable surface for agent artifact access.

Wraps ``ArtifactStore`` with typed methods, normalised error handling,
and structured result envelopes.  Both the CLI and in-process agent
runtimes share this single code-path.

Errors are surfaced as ``ArtifactError`` subclasses (never raw backend
exceptions), keeping callers backend-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.storage.config import load_config
from src.core.storage.factory import get_store
from src.core.storage.protocol import ArtifactStore


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

class ErrorKind(str, Enum):
    NOT_FOUND = "not_found"
    VALIDATION = "validation_error"
    UNSUPPORTED = "unsupported_operation"
    BACKEND = "backend_error"


class ArtifactError(Exception):
    """Base error surfaced by ArtifactService."""

    def __init__(self, kind: ErrorKind, message: str) -> None:
        self.kind = kind
        super().__init__(message)


class NotFoundError(ArtifactError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorKind.NOT_FOUND, message)


class ValidationError(ArtifactError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorKind.VALIDATION, message)


class BackendError(ArtifactError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorKind.BACKEND, message)


# ---------------------------------------------------------------------------
# Result envelope
# ---------------------------------------------------------------------------

@dataclass
class Result:
    """Uniform result envelope for every operation."""

    success: bool
    data: Any = None
    error: str | None = None
    error_kind: ErrorKind | None = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"success": self.success, "data": self.data}
        if self.error is not None:
            d["error"] = self.error
            d["error_kind"] = self.error_kind.value if self.error_kind else None
        return d


# ---------------------------------------------------------------------------
# Service facade
# ---------------------------------------------------------------------------

class ArtifactService:
    """Agent-facing artifact access facade.

    Instantiate once per session with a project root; all operations go
    through the resolved ``ArtifactStore`` backend.
    """

    def __init__(self, store: ArtifactStore) -> None:
        self._store = store

    # -- Factory ----------------------------------------------------------

    @classmethod
    def from_project_dir(cls, project_dir: str = ".") -> "ArtifactService":
        """Resolve config and return a ready-to-use service instance."""
        root = Path(project_dir).resolve()
        briefcase_dir = root / ".briefcase"
        project_config_dir = root / "_project"

        if (briefcase_dir / "storage.yaml").exists():
            config = load_config(briefcase_dir)
        elif project_config_dir.exists():
            config = load_config(project_config_dir)
        else:
            config = load_config(project_config_dir)

        store = get_store(config, str(root))
        return cls(store)

    # -- Inbox ------------------------------------------------------------

    def list_inbox(self) -> Result:
        return self._safe(lambda: self._store.read_inbox())

    def add_inbox(self, *, text: str, entry_type: str = "idea", notes: str = "") -> Result:
        if not text:
            return self._validation("text is required")
        entry: dict[str, str] = {"text": text, "type": entry_type}
        if notes:
            entry["notes"] = notes
        return self._safe(lambda: (self._store.append_inbox(entry), entry)[1])

    # -- Briefs -----------------------------------------------------------

    def read_brief(self, brief_name: str) -> Result:
        if not brief_name:
            return self._validation("brief_name is required")
        return self._safe(lambda: self._store.read_brief(brief_name), brief_name)

    def write_brief(self, brief_name: str, data: dict) -> Result:
        if not brief_name:
            return self._validation("brief_name is required")
        if not data.get("status"):
            return self._validation("status is required in brief data")
        return self._safe(lambda: (self._store.write_brief(brief_name, data), data)[1])

    def list_briefs(self) -> Result:
        return self._safe(lambda: self._store.list_briefs())

    # -- Decisions --------------------------------------------------------

    def list_decisions(self) -> Result:
        return self._safe(lambda: self._store.read_decisions())

    def add_decision(self, entry: dict) -> Result:
        for key in ("id", "title", "date", "why"):
            if not entry.get(key):
                return self._validation(f"{key} is required")
        return self._safe(lambda: (self._store.append_decision(entry), entry)[1])

    # -- Backlog ----------------------------------------------------------

    def list_backlog(self) -> Result:
        return self._safe(lambda: self._store.read_backlog())

    def upsert_backlog(self, row: dict) -> Result:
        for key in ("title", "type", "status"):
            if not row.get(key):
                return self._validation(f"{key} is required")
        return self._safe(lambda: (self._store.write_backlog_row(row), row)[1])

    # -- Release Notes ----------------------------------------------------

    def read_release_note(self, version: str) -> Result:
        if not version:
            return self._validation("version is required")
        return self._safe(lambda: self._store.read_release_note(version), version)

    def write_release_note(self, version: str, content: str) -> Result:
        if not version:
            return self._validation("version is required")
        return self._safe(
            lambda: (self._store.write_release_note(version, content), {"version": version})[1]
        )

    def list_release_notes(self) -> Result:
        return self._safe(lambda: self._store.list_release_notes())

    # -- Internal helpers -------------------------------------------------

    def _safe(self, fn, lookup_key: str | None = None) -> Result:
        """Run *fn* and wrap the outcome in a Result envelope."""
        try:
            data = fn()
            return Result(success=True, data=data)
        except KeyError:
            name = lookup_key or "item"
            return Result(
                success=False,
                error=f"{name} not found",
                error_kind=ErrorKind.NOT_FOUND,
            )
        except ArtifactError as exc:
            return Result(success=False, error=str(exc), error_kind=exc.kind)
        except Exception as exc:  # noqa: BLE001  — normalise backend errors
            return Result(
                success=False,
                error=str(exc),
                error_kind=ErrorKind.BACKEND,
            )

    @staticmethod
    def _validation(msg: str) -> Result:
        return Result(success=False, error=msg, error_kind=ErrorKind.VALIDATION)
