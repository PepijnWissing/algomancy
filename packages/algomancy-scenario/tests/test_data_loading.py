import os

import pytest

from algomancy_scenario import ScenarioManager


@pytest.fixture
def datafiles_dir():
    return "example_data"


@pytest.fixture
def datafile_name():
    return "serialized_data.json"


def test_etl(mock_scenario_manager_no_data: ScenarioManager, datafiles_dir: str):
    print(f"Current working directory is: {os.getcwd()}")
    mock_scenario_manager_no_data.debug_etl_data(datafiles_dir)


def test_load_serialized_data(
    mock_scenario_manager_no_data: ScenarioManager, datafile_name: str
):
    mock_scenario_manager_no_data.debug_load_serialized_data(datafile_name)


@pytest.mark.xfail(reason="Not Implemented", raises=NotImplementedError)
def test_import_data(
    mock_scenario_manager_no_data: ScenarioManager, datafiles_dir: str
):
    mock_scenario_manager_no_data.debug_import_data(datafiles_dir)


@pytest.mark.xfail(reason="Not Implemented", raises=NotImplementedError)
def test_upload_data(
    mock_scenario_manager_no_data: ScenarioManager, datafile_name: str
):
    mock_scenario_manager_no_data.debug_upload_data(datafile_name)
