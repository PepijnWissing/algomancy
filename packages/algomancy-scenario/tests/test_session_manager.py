import pytest

from algomancy_scenario import (
    CoreConfig,
    ScenarioManager,
    SessionManager,
)


def _make_core_config(mock_configs) -> CoreConfig:
    return CoreConfig(
        use_sessions=True,
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
    assert "main" in sm.sessions_names or len(sm.sessions_names) >= 1
    assert isinstance(sm.get_scenario_manager(sm.start_session_name), ScenarioManager)


def test_session_manager_from_app_config_like(mock_configs):
    cfg = _AppConfigLike(_make_core_config(mock_configs))
    sm = SessionManager.from_config(cfg)
    assert sm.start_session_name in sm.sessions_names


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


def test_session_manager_create_and_copy(mock_configs):
    sm = SessionManager.from_config(_make_core_config(mock_configs))
    start = sm.start_session_name

    sm.create_new_session("brand-new")
    assert sm.has_session("brand-new")

    with pytest.raises(ValueError):
        sm.create_new_session("brand-new")  # duplicate

    sm.copy_session(start, "copied")
    assert sm.has_session("copied")
    # copied session should expose the same data keys as the source
    assert set(sm.get_scenario_manager("copied").get_data_keys()) == set(
        sm.get_scenario_manager(start).get_data_keys()
    )

    with pytest.raises(ValueError):
        sm.copy_session(start, "copied")  # destination already exists


def test_gui_reexport_still_works(mock_configs):
    """The legacy import path algomancy_gui.managers.sessionmanager.SessionManager
    must continue to resolve to the relocated class."""
    from algomancy_gui.managers.sessionmanager import (
        SessionManager as ReexportedSessionManager,
    )

    assert ReexportedSessionManager is SessionManager
