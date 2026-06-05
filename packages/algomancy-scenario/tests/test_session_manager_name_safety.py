"""Display-name validation on the SessionManager.

Display names go through validation only enough to reject empty/whitespace
strings — the storage layer is keyed by UUIDs so display strings cannot
escape the data folder. The cross-platform path-segment hazards (``..``,
separators, drive prefixes) are guarded at the directory-slug layer instead,
which is fed only the slugified version of the display name.
"""

from __future__ import annotations

import pytest

from algomancy_scenario import CoreConfig, SessionManager


def _build_manager(mock_configs, tmp_path) -> SessionManager:
    """Construct a SessionManager from the shared mock_configs fixture, with
    an isolated data folder."""
    kwargs = dict(mock_configs)
    kwargs["data_path"] = str(tmp_path)
    kwargs.setdefault("autocreate", False)
    kwargs.setdefault("autorun", False)
    cfg = CoreConfig(**kwargs)
    return SessionManager.from_config(cfg)


@pytest.mark.parametrize("name", ["", " ", "\t", "\n\n"])
def test_create_new_session_rejects_empty_display_names(mock_configs, tmp_path, name):
    sm = _build_manager(mock_configs, tmp_path)
    with pytest.raises(ValueError):
        sm.create_new_session(name)


def test_create_new_session_accepts_unicode_and_spaces(mock_configs, tmp_path):
    sm = _build_manager(mock_configs, tmp_path)
    new_id = sm.create_new_session("Alice's experiment v2 — Q1")
    assert sm.get_display_name(new_id) == "Alice's experiment v2 — Q1"


def test_create_new_session_handles_path_traversal_in_display_name(
    mock_configs, tmp_path
):
    """Display names with path traversal characters slugify to a safe segment
    instead of escaping the data folder."""
    import os

    sm = _build_manager(mock_configs, tmp_path)
    parent_before = set(os.listdir(tmp_path.parent))
    sm.create_new_session("../escape")
    parent_after = set(os.listdir(tmp_path.parent))
    assert parent_before == parent_after


def test_discovers_existing_session_directories(mock_configs, tmp_path):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()

    sm = _build_manager(mock_configs, tmp_path)

    display_names = {s["display_name"] for s in sm.list_sessions()}
    assert {"alpha", "beta"} <= display_names
