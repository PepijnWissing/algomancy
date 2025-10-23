from algomancy.scenarioengine import ScenarioManager


def debug_create_example_scenarios(sm: ScenarioManager):
    # create scenarios
    sm.create_scenario(
        tag="Fast algorithm",
        algo_name="As is",
    )

    sm.create_scenario(
        tag="Slow algorithm 1", algo_name="Slow", algo_params={"duration": 10}
    )

    sm.create_scenario(
        tag="Slow algorithm 2", algo_name="Slow", algo_params={"duration": 12}
    )

    sm.create_scenario(
        tag="Slow algorithm 3", algo_name="Slow", algo_params={"duration": 16}
    )
