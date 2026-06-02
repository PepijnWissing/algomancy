from algomancy_scenario import ScenarioManager, SessionManager


def get_scenario_manager(
    server, active_session_name: str | None = None
) -> ScenarioManager:
    """Resolve the ScenarioManager for ``active_session_name`` via the server's
    SessionManager. ``active_session_name`` falls back to the SessionManager's
    starting session when None.
    """
    sm: SessionManager = server.session_manager
    if active_session_name is None:
        active_session_name = sm.start_session_id
    return sm.get_scenario_manager(active_session_name)


def get_manager(server) -> SessionManager:
    """Return the SessionManager registered on the server object."""
    return server.session_manager
