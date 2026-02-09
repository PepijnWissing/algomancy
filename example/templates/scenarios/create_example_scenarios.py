from algomancy_scenario import ScenarioManager


def debug_create_example_scenarios(scenario_manager: ScenarioManager):
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
