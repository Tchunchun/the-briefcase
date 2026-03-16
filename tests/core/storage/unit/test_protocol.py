"""Tests for ArtifactStore and SyncableStore protocol definitions."""

from src.core.storage.protocol import ArtifactStore, SyncableStore


class _MockLocalBackend:
    """Minimal mock that satisfies ArtifactStore but NOT SyncableStore."""

    def read_inbox(self) -> list[dict]:
        return []

    def append_inbox(self, entry: dict) -> None:
        pass

    def read_brief(self, brief_name: str) -> dict:
        return {}

    def write_brief(self, brief_name: str, data: dict) -> None:
        pass

    def list_briefs(self) -> list[dict]:
        return []

    def read_decisions(self) -> list[dict]:
        return []

    def append_decision(self, entry: dict) -> None:
        pass

    def read_backlog(self) -> list[dict]:
        return []

    def write_backlog_row(self, row: dict) -> None:
        pass

    def read_templates(self) -> list[dict]:
        return []

    def write_template(self, name: str, content: str, version: str) -> None:
        pass


class _MockCloudBackend(_MockLocalBackend):
    """Minimal mock that satisfies both ArtifactStore and SyncableStore."""

    def sync_to_local(self, target_dir: str, *, dry_run: bool = False) -> dict:
        return {"fetched": 0, "created": 0, "skipped": 0, "failed": 0}

    def sync_templates_to_local(
        self, template_dir: str, *, dry_run: bool = False
    ) -> dict:
        return {"fetched": 0, "updated": 0, "skipped": 0, "failed": 0}


class _IncompleteBackend:
    """Does NOT implement all ArtifactStore methods."""

    def read_inbox(self) -> list[dict]:
        return []


# --- Protocol compliance tests ---


def test_local_backend_satisfies_artifact_store():
    backend = _MockLocalBackend()
    assert isinstance(backend, ArtifactStore)


def test_local_backend_does_not_satisfy_syncable_store():
    backend = _MockLocalBackend()
    assert not isinstance(backend, SyncableStore)


def test_cloud_backend_satisfies_artifact_store():
    backend = _MockCloudBackend()
    assert isinstance(backend, ArtifactStore)


def test_cloud_backend_satisfies_syncable_store():
    backend = _MockCloudBackend()
    assert isinstance(backend, SyncableStore)


def test_incomplete_backend_does_not_satisfy_artifact_store():
    backend = _IncompleteBackend()
    assert not isinstance(backend, ArtifactStore)


# --- Method signature tests ---


def test_artifact_store_has_all_required_methods():
    expected_methods = [
        "read_inbox",
        "append_inbox",
        "read_brief",
        "write_brief",
        "list_briefs",
        "read_decisions",
        "append_decision",
        "read_backlog",
        "write_backlog_row",
        "read_templates",
        "write_template",
    ]
    for method_name in expected_methods:
        assert hasattr(ArtifactStore, method_name), (
            f"ArtifactStore missing method: {method_name}"
        )


def test_syncable_store_has_sync_methods():
    expected_methods = ["sync_to_local", "sync_templates_to_local"]
    for method_name in expected_methods:
        assert hasattr(SyncableStore, method_name), (
            f"SyncableStore missing method: {method_name}"
        )
