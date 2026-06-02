import pytest

from algomancy_scenario import (
    CoreConfig,
    ScenarioManager,
    SessionManager,
)


def _make_core_config(mock_configs) -> CoreConfig:
    return CoreConfig(
        data_path=mock_configs["data_path"],
        has_persistent_state=mock_configs["has_persistent_state"],
        save_type=mock_configs["save_type"],
        data_object_type=mock_configs["data_object_type"],
        etl_factory=mock_configs["etl_factory"],
        kpi_templates=mock_configs["kpi_templates"],
        algo_templates=mock_configs["algo_templates"],
        schemas=mock_configs["schemas"],
        autocreate=False,
        autorun=False,
    )


class _AppConfigLike:
    """Minimal duck-type that wraps a CoreConfig as `.core`, mimicking AppConfig."""

    def __init__(self, core: CoreConfig) -> None:
        self.core = core


def test_session_manager_from_core_config(mock_configs):
    cfg = _make_core_config(mock_configs)
    sm = SessionManager.from_config(cfg)
    assert len(sm.session_ids) >= 1
    assert isinstance(sm.get_scenario_manager(sm.start_session_id), ScenarioManager)


def test_session_manager_from_app_config_like(mock_configs):
    cfg = _AppConfigLike(_make_core_config(mock_configs))
    sm = SessionManager.from_config(cfg)
    assert sm.start_session_id in sm.session_ids


def test_session_manager_from_config_rejects_garbage():
    with pytest.raises(TypeError):
        SessionManager.from_config(object())


def test_scenario_manager_from_core_config(mock_configs):
    cfg = _make_core_config(mock_configs)
    sm = ScenarioManager.from_config(cfg)
    assert sm is not None
    assert sm.get_data_keys() is not None  # delegated to data manager, must not error


def test_scenario_manager_from_app_config_like(mock_configs):
    cfg = _AppConfigLike(_make_core_config(mock_configs))
    sm = ScenarioManager.from_config(cfg)
    assert sm is not None


def test_scenario_manager_from_config_rejects_garbage():
    with pytest.raises(TypeError):
        ScenarioManager.from_config(object())


def test_session_manager_get_unknown_session_raises(mock_configs):
    sm = SessionManager.from_config(_make_core_config(mock_configs))
    with pytest.raises(KeyError):
        sm.get_scenario_manager("does-not-exist")


def test_session_manager_create_and_copy(mock_configs, tmp_path):
    # Use tmp_path so persistent state from this test doesn't leak into the
    # checked-in test data folder.
    isolated = dict(mock_configs)
    isolated["data_path"] = str(tmp_path)
    sm = SessionManager.from_config(_make_core_config(isolated))
    start = sm.start_session_id

    new_id = sm.create_new_session("brand-new")
    assert sm.has_session(new_id)
    assert sm.get_display_name(new_id) == "brand-new"

    with pytest.raises(ValueError):
        sm.create_new_session("brand-new")  # duplicate display name

    copied_id = sm.copy_session(start, "copied")
    assert sm.has_session(copied_id)
    # copied session should expose the same data keys as the source
    assert set(sm.get_scenario_manager(copied_id).get_data_keys()) == set(
        sm.get_scenario_manager(start).get_data_keys()
    )

    with pytest.raises(ValueError):
        sm.copy_session(start, "copied")  # duplicate display name


def test_rename_session_updates_display_name(mock_configs, tmp_path):
    isolated = dict(mock_configs)
    isolated["data_path"] = str(tmp_path)
    sm = SessionManager.from_config(_make_core_config(isolated))
    new_id = sm.create_new_session("original")
    sm.rename_session(new_id, "renamed")
    assert sm.get_display_name(new_id) == "renamed"
    # The id itself does not change.
    assert new_id in sm.session_ids


def test_rename_session_rejects_duplicate(mock_configs, tmp_path):
    isolated = dict(mock_configs)
    isolated["data_path"] = str(tmp_path)
    sm = SessionManager.from_config(_make_core_config(isolated))
    a = sm.create_new_session("alpha")
    sm.create_new_session("beta")
    with pytest.raises(ValueError):
        sm.rename_session(a, "beta")


def test_meta_json_persists_session_id(mock_configs, tmp_path):
    """A meta.json written into each session directory carries id + name."""
    import json
    import os

    isolated = dict(mock_configs)
    isolated["data_path"] = str(tmp_path)
    sm = SessionManager.from_config(_make_core_config(isolated))
    new_id = sm.create_new_session("first")

    # Find the directory and verify meta.json.
    dirs = [d for d in os.listdir(tmp_path) if os.path.isdir(tmp_path / d)]
    matching = [d for d in dirs if os.path.exists(tmp_path / d / "meta.json")]
    assert matching, "expected meta.json in at least one session dir"
    # Locate the meta file for the new session by id.
    for d in matching:
        with open(tmp_path / d / "meta.json", encoding="utf-8") as f:
            meta = json.load(f)
        if meta["id"] == new_id:
            assert meta["display_name"] == "first"
            break
    else:
        pytest.fail(f"no meta.json found referencing session id {new_id}")


def test_legacy_directory_gets_meta_on_discovery(mock_configs, tmp_path):
    """A pre-M14 session directory (no meta.json) is migrated transparently."""
    import json
    import os

    (tmp_path / "legacy-session").mkdir()
    isolated = dict(mock_configs)
    isolated["data_path"] = str(tmp_path)
    sm = SessionManager.from_config(_make_core_config(isolated))

    # meta.json should now exist with the directory name as display_name.
    assert os.path.exists(tmp_path / "legacy-session" / "meta.json")
    with open(tmp_path / "legacy-session" / "meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["display_name"] == "legacy-session"
    assert sm.get_display_name(meta["id"]) == "legacy-session"


def test_gui_reexport_still_works(mock_configs):
    """The legacy import path algomancy_gui.managers.sessionmanager.SessionManager
    must continue to resolve to the relocated class."""
    from algomancy_gui.managers.sessionmanager import (
        SessionManager as ReexportedSessionManager,
    )

    assert ReexportedSessionManager is SessionManager
