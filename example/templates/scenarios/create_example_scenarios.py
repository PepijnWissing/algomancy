from algomancy_gui.sessionmanager import SessionManager


def debug_create_example_scenarios(session_manager: SessionManager):
    first_session = session_manager.start_session_name
    scenario_manager = session_manager.get_scenario_manager(first_session)
    scenario_manager.toggle_autorun(True)
    data_key = scenario_manager.get_data_keys()[0]
    names = [
        "Base line",
        "Change",
        "To-be",
        "Test",
        "Validate",
    ]

    # create scenarios
    for name in names:
        scenario_manager.create_scenario(
            dataset_key=data_key,
            tag=name,
            algo_name="As is",
        )
