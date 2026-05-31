from algomancy_scenario import ScenarioManager


def debug_create_example_scenarios(sm: ScenarioManager):
    sm.toggle_autorun(True)

    # create scenarios
    sm.create_scenario(
        dataset_key="example_data",
        tag="Fast algorithm",
        algo_name="As is",
    )

    sm.create_scenario(
        tag="Slow algorithm 1",
        algo_name="Slow",
        algo_params={"duration": 1},
        dataset_key="example_data",
    )

    sm.create_scenario(
        tag="Slow algorithm 2",
        algo_name="Slow",
        algo_params={"duration": 2},
        dataset_key="example_data",
    )

    sm.create_scenario(
        tag="Slow algorithm 3",
        algo_name="Slow",
        algo_params={"duration": 3},
        dataset_key="example_data",
    )


def seed_warehouse_scenarios(
    sm: ScenarioManager, dataset_key: str = "example_data"
) -> None:
    """Seed five realistic warehouse slotting scenarios on first boot."""
    sm.toggle_autorun(True)

    _tags_and_params = [
        (
            "realistic-asis-baseline",
            "AsIs Slotting",
            {"depot_x": 0.0, "depot_y": 0.0, "respect_zones": False},
        ),
        (
            "realistic-greedy-default",
            "Greedy Slotting",
            {"depot_x": 0.0, "depot_y": 0.0, "respect_zones": False},
        ),
        (
            "realistic-sa-hot",
            "SA Slotting",
            {
                "depot_x": 0.0,
                "depot_y": 0.0,
                "respect_zones": False,
                "iterations": 2000,
                "start_temperature": 200.0,
                "cooling_rate": 0.995,
                "seed": 1,
            },
        ),
        (
            "realistic-sa-warm",
            "SA Slotting",
            {
                "depot_x": 0.0,
                "depot_y": 0.0,
                "respect_zones": False,
                "iterations": 2000,
                "start_temperature": 50.0,
                "cooling_rate": 0.99,
                "seed": 2,
            },
        ),
        (
            "realistic-sa-cold",
            "SA Slotting",
            {
                "depot_x": 0.0,
                "depot_y": 0.0,
                "respect_zones": False,
                "iterations": 2000,
                "start_temperature": 10.0,
                "cooling_rate": 0.98,
                "seed": 3,
            },
        ),
    ]

    for tag, algo_name, algo_params in _tags_and_params:
        try:
            sm.create_scenario(
                dataset_key=dataset_key,
                tag=tag,
                algo_name=algo_name,
                algo_params=algo_params,
            )
        except ValueError:
            pass  # already exists — skip on subsequent boots
