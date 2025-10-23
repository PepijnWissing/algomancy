import pytest

from algomancy.scenarioengine import ScenarioManager


@pytest.fixture
def datafiles_dir():
    return "example_data"


@pytest.fixture
def datafile_name():
    return "serialized_data.json"


# @pytest.mark.xfail(reason="DataManager is stateless", raises=AttributeError) # include if your project is stateless
def test_etl(mock_scenario_manager_no_data: ScenarioManager, datafiles_dir: str):
    sm = mock_scenario_manager_no_data
    sm.debug_etl_data(datafiles_dir)


# @pytest.mark.xfail(reason="DataManager is stateless", raises=AttributeError) # include if your project is stateless
@pytest.mark.xfail(reason="DataSource.id has no setter.", raises=AttributeError)
def test_load_serialized_data(
    mock_scenario_manager_no_data: ScenarioManager, datafile_name: str
):
    sm = mock_scenario_manager_no_data
    sm.debug_load_serialized_data(datafile_name)


def test_import_data(
    mock_scenario_manager_no_data: ScenarioManager, datafiles_dir: str
):
    sm = mock_scenario_manager_no_data
    sm.debug_import_data(datafiles_dir)


def test_upload_data(
    mock_scenario_manager_no_data: ScenarioManager, datafile_name: str
):
    sm = mock_scenario_manager_no_data
    sm.debug_upload_data(datafile_name)
