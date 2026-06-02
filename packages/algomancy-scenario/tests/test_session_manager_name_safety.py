"""Session-name validation on the SessionManager.

Covers per-tenant data-isolation hazards: name traversal via
``create_new_session`` and ``copy_session`` must reject anything that would
escape the data folder.
"""

from __future__ import annotations

import os

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
    sm = _build_manager(mock_configs, tmp_path)
    with pytest.raises(ValueError):
        sm.create_new_session(name)


def test_copy_session_validates_destination_name(mock_configs, tmp_path):
    sm = _build_manager(mock_configs, tmp_path)
    with pytest.raises(ValueError):
        sm.copy_session(sm.start_session_name, "../escape")


def test_create_new_session_does_not_create_dirs_outside_root(mock_configs, tmp_path):
    sm = _build_manager(mock_configs, tmp_path)
    parent_before = set(os.listdir(tmp_path.parent))
    with pytest.raises(ValueError):
        sm.create_new_session("../sneaky")
    parent_after = set(os.listdir(tmp_path.parent))
    assert parent_before == parent_after


def test_discovers_existing_session_directories(mock_configs, tmp_path):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "beta").mkdir()

    sm = _build_manager(mock_configs, tmp_path)

    assert set(sm.sessions_names) >= {"alpha", "beta"}
