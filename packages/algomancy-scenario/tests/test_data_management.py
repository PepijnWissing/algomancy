import pytest

from algomancy_scenario import ScenarioManager


@pytest.fixture
def derived_data_key():
    return "derived_data"


def test_derive_data(
    mock_scenario_manager_with_data: ScenarioManager, derived_data_key: str
):
    # fetch available data keys
    sm = mock_scenario_manager_with_data
    data_keys = sm.get_data_keys()
    test_key = data_keys[0]  # may throw IndexError in case fixture is bad

    # store hash of original
    # original_hash = sm.get_data(test_key).hash()

    # derive data
    sm.derive_data(test_key, derived_data_key)

    # check if derived data is available
    assert derived_data_key in sm.get_data_keys(), "Derived data not available."
