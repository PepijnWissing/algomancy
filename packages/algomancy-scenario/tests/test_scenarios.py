import pytest

from algomancy_scenario import ScenarioManager


@pytest.mark.parametrize(
    "tag, dataset_key, algo_name, params",
    [
        pytest.param("slow1", "example_data", "Slow", {"duration": 1}, id="slow1"),
        pytest.param("slow2", "example_data", "Slow", {"duration": 2}, id="slow2"),
        pytest.param(
            "slow3",
            "example_data",
            "Slow",
            {"duration": 100},
            marks=pytest.mark.xfail(reason="Too long"),
            id="slow3",
        ),
    ],
)
def test_scenario_execution(
    mock_scenario_manager_with_data: ScenarioManager,
    tag: str,
    dataset_key: str,
    algo_name: str,
    params,
):
    sm = mock_scenario_manager_with_data

    # create and run the scenario; wait for completion
    scenario = sm.debug_create_and_run_scenario(tag, dataset_key, algo_name, params)

    # check if the scenario was completed successfully
    assert scenario.is_completed()
