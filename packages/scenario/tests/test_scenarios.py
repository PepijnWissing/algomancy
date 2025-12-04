import pytest

from src.algomancy import ScenarioManager


def bparams(batch_size, direction, use_cache):
    """Helper function to create batching algorithm parameters"""
    return {
        "batch_size": batch_size,
        "search_direction": direction,
        "use_cache": use_cache,
    }


@pytest.mark.parametrize(
    "tag, dataset_key, algo_name, params",
    [
        pytest.param("as is", "example_data", "As is", {}, id="as is"),
        pytest.param(
            "batch1",
            "example_data",
            "Batching",
            bparams(1, "depth first", True),
            id="batch1",
        ),
        pytest.param(
            "batch2",
            "example_data",
            "Batching",
            bparams(2, "dept first", True),
            marks=pytest.mark.xfail(reason="typo"),
            id="batch2",
        ),
        pytest.param(
            "batch3",
            "example_data",
            "Batching",
            bparams(1, "breadth first", True),
            id="batch3",
        ),
        pytest.param(
            "batch4",
            "example_data",
            "Batching",
            bparams(2, "breadth first", True),
            id="batch4",
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
