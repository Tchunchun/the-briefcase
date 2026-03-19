"""Canonical .gitignore policy for consumer installs.

Defines the entries the framework manages and provides an idempotent-append
helper used by both ``install.sh`` and ``agent setup``.
"""

from __future__ import annotations

from pathlib import Path


# --- Canonical entries -------------------------------------------------------
# Each tuple: (gitignore pattern, explanatory comment).
# .briefcase/ covers ALL framework code *and* runtime config (storage.yaml).

BASELINE_ENTRIES: list[tuple[str, str]] = [
    (".briefcase/", "Framework code (installed by install.sh, regenerated on update)"),
    (".env", "Environment secrets — never commit"),
]

NOTION_ENTRIES: list[tuple[str, str]] = [
    ("docs/plan/", "Notion is source of truth; local copy is transient"),
]


def entries_for_backend(backend: str = "local") -> list[tuple[str, str]]:
    """Return the gitignore entries appropriate for *backend*."""
    entries = list(BASELINE_ENTRIES)
    if backend == "notion":
        entries.extend(NOTION_ENTRIES)
    return entries


def ensure_gitignore(
    project_root: str | Path,
    entries: list[tuple[str, str]],
) -> list[str]:
    """Append missing *entries* to ``.gitignore`` — idempotent, append-only.

    * Creates the file if it does not exist.
    * Skips entries whose pattern already appears anywhere in the file.
    * Never removes or modifies existing lines.

    Returns the list of patterns that were actually appended.
    """
    path = Path(project_root) / ".gitignore"
    existing = path.read_text() if path.exists() else ""

    appended: list[str] = []
    with open(path, "a") as fh:
        for pattern, comment in entries:
            if pattern not in existing:
                fh.write(f"\n# {comment}\n{pattern}\n")
                appended.append(pattern)

    return appended
