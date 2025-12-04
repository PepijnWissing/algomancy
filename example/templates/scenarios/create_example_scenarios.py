from src.algomancy import ScenarioManager


def debug_create_example_scenarios(sm: ScenarioManager):
    sm.toggle_autorun(True)

    # create scenarios
    sm.create_scenario(
        dataset_key="example_data",
        tag="Fast algorithm",
        algo_name="As is",
    )

    sm.create_scenario(
        tag="Slow algorithm 1", algo_name="Slow", algo_params={"duration": 1},
        dataset_key="example_data",
    )

    sm.create_scenario(
        tag="Slow algorithm 2", algo_name="Slow", algo_params={"duration": 2},
        dataset_key="example_data",
    )

    sm.create_scenario(
        tag="Slow algorithm 3", algo_name="Slow", algo_params={"duration": 3},
        dataset_key="example_data",
    )
