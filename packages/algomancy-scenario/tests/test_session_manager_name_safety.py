"""Session-name validation and session-discovery gating.

Covers the per-tenant data-isolation hazards on the SessionManager that the
headless API surfaces: name traversal via ``create_new_session`` and unintended
subdirectory auto-registration when ``use_sessions=False``.
"""

from __future__ import annotations

import os

import pytest

from algomancy_scenario import CoreConfig, SessionManager


def _build_manager(mock_configs, tmp_path, **extra) -> SessionManager:
    """Construct a SessionManager from the shared mock_configs fixture, with
    an isolated data folder."""
    kwargs = dict(mock_configs)
    kwargs["data_path"] = str(tmp_path)
    kwargs.setdefault("autocreate", False)
    kwargs.setdefault("autorun", False)
    cfg = CoreConfig(**kwargs, **extra)
    return SessionManager.from_config(cfg)


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "..\\escape",
        "..",
        ".",
        "foo/bar",
        "foo\\bar",
        "",
        "C:somewhere",
    ],
)
def test_create_new_session_rejects_unsafe_names(mock_configs, tmp_path, name):
    sm = _build_manager(mock_configs, tmp_path, use_sessions=True)
    with pytest.raises(ValueError):
        sm.create_new_session(name)


def test_copy_session_validates_destination_name(mock_configs, tmp_path):
    sm = _build_manager(mock_configs, tmp_path, use_sessions=True)
    with pytest.raises(ValueError):
        sm.copy_session(sm.start_session_name, "../escape")


def test_create_new_session_does_not_create_dirs_outside_root(mock_configs, tmp_path):
    sm = _build_manager(mock_configs, tmp_path, use_sessions=True)
    parent_before = set(os.listdir(tmp_path.parent))
    with pytest.raises(ValueError):
        sm.create_new_session("../sneaky")
    parent_after = set(os.listdir(tmp_path.parent))
    assert parent_before == parent_after


def test_use_sessions_false_does_not_scan_data_folder(mock_configs, tmp_path):
    # Pre-seed the data folder with subdirectories that look like sessions.
    (tmp_path / "cache").mkdir()
    (tmp_path / "junk").mkdir()
    (tmp_path / ".git").mkdir()

    sm = _build_manager(mock_configs, tmp_path, use_sessions=False)

    # With sessions disabled the only registered session is the default "main".
    assert sm.sessions_names == ["main"]


def test_use_sessions_true_still_discovers_existing_sessions(mock_configs, tmp_path):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()

    sm = _build_manager(mock_configs, tmp_path, use_sessions=True)

    assert set(sm.sessions_names) >= {"alpha", "beta"}
