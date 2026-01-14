from algomancy_scenario import ScenarioManager


def get_scenario_manager(
    server, active_session_name: str | None = None
) -> ScenarioManager:
    """Returns the scenario manager.
    When sessions are enabled, this will return the active scenario manager via the session manager.
    When sessions are disabled, this will return the scenario manager which was registered on the server object
    """
    if hasattr(server, "session_manager"):
        sm: ScenarioManager = server.session_manager.get_scenario_manager(
            active_session_name
        )
    elif hasattr(server, "scenario_manager"):
        sm: ScenarioManager = server.scenario_manager
    else:
        raise Exception("No sessionmanager or scenario manager available")
    return sm


def get_manager(server):
    if hasattr(server, "session_manager"):
        return server.session_manager
    elif hasattr(server, "scenario_manager"):
        return server.scenario_manager
    else:
        raise Exception("No sessionmanager or scenario manager available")
