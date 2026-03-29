"""Unit tests for the release command version helpers."""

from __future__ import annotations

import pytest

from src.cli.commands.release import _read_pyproject_version


@pytest.fixture
def pyproject(tmp_path):
    p = tmp_path / "pyproject.toml"
    p.write_text('[project]\nname = "my-pkg"\nversion = "1.2.3"\n')
    return tmp_path


def test_current_version_reads_pyproject(pyproject):
    assert _read_pyproject_version(str(pyproject)) == "1.2.3"


def test_current_version_missing_pyproject(tmp_path):
    assert _read_pyproject_version(str(tmp_path)) is None


def test_current_version_no_version_field(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-pkg"\n')
    assert _read_pyproject_version(str(tmp_path)) is None
