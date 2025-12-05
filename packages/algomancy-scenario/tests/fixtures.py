import pytest

from src.algomancy import Logger
from algomancy_data import DataSource
from scenario import ScenarioManager
from example_implementation.data_handling.factories import ExampleETLFactory
from example_implementation.data_handling.input_configs import example_input_configs
from example_implementation.templates import kpi_templates, algorithm_templates


@pytest.fixture
def mock_configs():
    # framework configuration
    return {
        "data_path": "tests/data",
        "has_persistent_state": True,
        "save_type": "json",
        "data_object_type": DataSource,  # Plug in your own data object type here
        "etl_factory": ExampleETLFactory,  # Plug in your own ETL factory here
        "input_configs": example_input_configs,  # Plug in your own input configs here
        "autorun": False,
        "kpi_templates": kpi_templates,
        "algo_templates": algorithm_templates,
    }


@pytest.fixture
def quiet_logger():
    logger = Logger()
    logger.toggle_print_to_console(False)
    return logger


@pytest.fixture
def mock_scenario_manager_no_data(mock_configs, quiet_logger: Logger):
    sm: ScenarioManager = ScenarioManager(
        etl_factory=mock_configs["etl_factory"],
        kpi_templates=mock_configs["kpi_templates"],
        algo_templates=mock_configs["algo_templates"],
        data_folder=mock_configs["data_path"],
        input_configs=mock_configs["input_configs"],
        has_persistent_state=mock_configs["has_persistent_state"],
        save_type=mock_configs["save_type"],
        data_object_type=mock_configs["data_object_type"],
        logger=quiet_logger,
    )
    return sm


@pytest.fixture
def mock_scenario_manager_with_data(mock_configs, quiet_logger: Logger):
    sm: ScenarioManager = ScenarioManager(
        etl_factory=mock_configs["etl_factory"],
        kpi_templates=mock_configs["kpi_templates"],
        algo_templates=mock_configs["algo_templates"],
        data_folder=mock_configs["data_path"],
        input_configs=mock_configs["input_configs"],
        has_persistent_state=mock_configs["has_persistent_state"],
        save_type=mock_configs["save_type"],
        data_object_type=mock_configs["data_object_type"],
    )

    sm.debug_load_data("example_data")

    return sm
