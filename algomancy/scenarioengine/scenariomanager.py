from typing import Dict, List, Optional, TypeVar, Type

from algomancy.dataengine import (
    ETLFactory,
    InputFileConfiguration,
    StatefulDataManager,
    StatelessDataManager,
    BASE_DATA_BOUND,
)
from algomancy.dashboardlogger.logger import Logger, MessageStatus
from .basealgorithm import ALGORITHM
from .basealgorithmparameters import BASE_PARAMS_BOUND

from .keyperformanceindicator import BASE_KPI
from .scenario import Scenario
from .scenarioregistry import ScenarioRegistry
from .scenariofactory import ScenarioFactory
from .scenarioprocessor import ScenarioProcessor


class ScenarioManager:
    """
    Facade that coordinates data management, scenario creation/registry, and processing.
    """

    E = TypeVar("E", bound=ETLFactory)

    def __init__(
        self,
        etl_factory: type[E],
        kpi_templates: Dict[str, Type[BASE_KPI]],
        algo_templates: Dict[str, Type[ALGORITHM]],
        input_configs: List[InputFileConfiguration],
        data_object_type: type[BASE_DATA_BOUND],  # for extensions of datasource
        data_folder: str = None,
        logger: Logger = None,
        scenario_save_location: str = "scenarios.json",
        has_persistent_state: bool = False,
        save_type: str = "json",  # adjusts the format
        autocreate: bool = False,
        default_algo_name: str = None,
        default_param_values: Dict[str, any] = None,
        autorun: bool = False,
    ) -> None:
        self.logger = logger if logger else Logger()
        self.scenario_save_location = scenario_save_location
        self._has_persistent_state = has_persistent_state
        self._auto_create_scenario = autocreate
        self._default_algo_name = default_algo_name
        self._default_param_values = default_param_values

        assert save_type in ["json"], "Save type must be parquet or json."
        self._save_type = save_type

        # Components
        if self._has_persistent_state:
            assert (
                data_folder
            ), "Data folder must be specified if data manager has state."
            self._dm = StatefulDataManager(
                etl_factory=etl_factory,
                input_configs=input_configs,
                data_folder=data_folder,
                save_type=save_type,
                data_object_type=data_object_type,
                logger=self.logger,
            )
        else:
            self._dm = StatelessDataManager(
                etl_factory=etl_factory,
                input_configs=input_configs,
                save_type=save_type,
                logger=self.logger,
                data_object_type=data_object_type,
            )

        self._registry = ScenarioRegistry(logger=self.logger)
        self._factory = ScenarioFactory(
            kpi_templates=kpi_templates,
            algo_templates=algo_templates,
            data_manager=self._dm,
            logger=self.logger,
        )
        self._processor = ScenarioProcessor(logger=self.logger)
        self.toggle_autorun(autorun)

        # Keep inputs for accessors
        # self._algo_templates = algo_templates
        self._input_configs = input_configs

        # Load initial data
        try:
            self._dm.startup()
            if self._auto_create_scenario:
                self.auto_create_scenarios(self._dm.get_data_keys())
        except Exception as e:
            self.log(f"Error loading initial data: {e}", status=MessageStatus.ERROR)

        self.log("ScenarioManager initialized.")

    # Logging
    def log(self, message: str, status: MessageStatus = MessageStatus.INFO) -> None:
        if self.logger:
            self.logger.log(message, status)

    @property
    def has_persistent_state(self):
        return self._has_persistent_state

    # Accessors
    @property
    def save_type(self):
        return self._save_type

    @property
    def input_configurations(self):
        return self._input_configs

    @property
    def available_algorithms(self):
        return self._factory.available_algorithms

    @property
    def auto_run_scenarios(self):
        return self._processor.auto_run_scenarios

    @property
    def currently_processing(self) -> Optional[Scenario]:
        return self._processor.currently_processing

    def get_algorithm_parameters(self, key) -> BASE_PARAMS_BOUND:
        return self._factory.algo_templates.get(key).initialize_parameters()

    # Data operations (delegated)
    def get_data_keys(self) -> List[str]:
        return self._dm.get_data_keys()

    def get_data(self, data_key):
        return self._dm.get_data(data_key)

    def set_data(self, data_key, data):
        self._dm.set_data(data_key, data)

    def derive_data(self, derive_from_key: str, new_data_key: str) -> None:
        self._dm.derive_data(derive_from_key, new_data_key)
        if self._auto_create_scenario:
            self.auto_create_scenarios([new_data_key])

    def delete_data(
        self, data_key: str, prevent_masterdata_removal: bool = False
    ) -> None:
        # prevent delete if used by scenarios
        assert (
            data_key not in self._registry.used_datasets()
        ), "Cannot delete data used in scenarios."
        self._dm.delete_data(data_key, prevent_masterdata_removal)

    def store_data(self, dataset_name: str, data):
        if isinstance(self._dm, StatefulDataManager):
            self._dm.store_data(dataset_name, data)
        else:
            if self.logger:
                self.logger.error(
                    "Store data is not supported for stateless data manager. "
                )
            pass

    def toggle_autorun(self, value: bool = None) -> None:
        if value is None:
            self._processor.auto_run_scenarios = not self._processor.auto_run_scenarios
        else:
            self._processor.auto_run_scenarios = value
        self.log(f"Auto-run scenarios set to {self._processor.auto_run_scenarios}")

    # Processing operations (delegated)
    def process_scenario_async(self, scenario):
        self._processor.enqueue(scenario)

    def wait_for_processing(self):
        self._processor.wait_for_processing()

    def shutdown_processing(self):
        self._processor.shutdown()

    # Scenario creation/registry
    def create_scenario(
        self,
        tag: str,
        dataset_key: str = "Master data",
        algo_name: str = "",
        algo_params=None,
    ) -> Scenario:
        if self._registry.has_tag(tag):
            self.log(f"Scenario with tag '{tag}' already exists. Skipping creation.")
            raise ValueError(f"A scenario with tag '{tag}' already exists.")

        scenario = self._factory.create(
            tag=tag,
            dataset_key=dataset_key,
            algo_name=algo_name,
            algo_params=algo_params,
        )
        self._registry.add(scenario)

        if self._processor.auto_run_scenarios:
            self._processor.enqueue(scenario)
        return scenario

    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        return self._registry.get_by_id(scenario_id)

    def get_by_tag(self, tag: str) -> Optional[Scenario]:
        return self._registry.get_by_tag(tag)

    def delete_scenario(self, scenario_id: str) -> bool:
        return self._registry.delete(scenario_id)

    def list_scenarios(self) -> List[Scenario]:
        return self._registry.list()

    def list_ids(self):
        return self._registry.list_ids()

    def toggle_autocreate(
        self, value: bool = None, default_algo_name: str = ""
    ) -> None:
        if value is None:
            self._auto_create_scenario = not self._auto_create_scenario
            self._default_algo_name = (
                default_algo_name if self._auto_create_scenario else None
            )
        else:
            self._auto_create_scenario = value
            self._default_algo_name = (
                default_algo_name if self._auto_create_scenario else None
            )
        self.log(f"Auto-create scenarios set to {self._auto_create_scenario}")

    def add_datasource_from_json(self, json_string):
        # Create data source from JSON
        datasource = self._dm.data_object_type.from_json(json_string)

        # Add data source to datamanager
        self._dm.add_data_source(datasource)

        # create scenario if auto-create is enabled
        if self._auto_create_scenario:
            self.auto_create_scenarios([datasource.name])

    def etl_data(self, files, dataset_name: str) -> None:
        # Process the files
        self._dm.etl_data(files, dataset_name)

        # create scenario if auto-create is enabled
        if self._auto_create_scenario:
            self.auto_create_scenarios([dataset_name])

    def auto_create_scenarios(self, keys: List[str] = None):
        for key in keys:
            self.create_scenario(
                tag=f"{key} [auto]",
                dataset_key=key,
                algo_name=self._default_algo_name,
                algo_params=self._default_param_values,
            )

    def get_data_as_json(self, key: str) -> str:
        return self._dm.get_data(key).to_json()

    def store_data_as_json(self, set_name):
        if isinstance(self._dm, StatefulDataManager):
            self._dm.store_data_source_as_json(set_name)
        else:
            raise AttributeError(
                "Stateless data manager does not support internal serialization."
            )

    def debug_load_data(self, dataset_name: str) -> None:
        if isinstance(self._dm, StatefulDataManager):
            self._dm.load_data_from_dir("data")
        elif isinstance(self._dm, StatelessDataManager):
            raise NotImplementedError(
                "Todo: implement loading for stateless data manager."
            )
        else:
            raise Exception("Data manager not initialized.")

    def debug_create_and_run_scenario(
        self,
        scenario_tag: str,
        dataset_key: str,
        algo_name: str,
        algo_params: Dict[str, any],
    ) -> Scenario:
        """
        Creates and runs a scenario for debugging purposes. The method uses a factory to create a
        scenario instance, registers it, enqueues it for processing, and waits for the processing to
        complete. Returns the fully processed scenario.

        Parameters:
            scenario_tag (str): A unique identifier for the scenario being created and run.
            dataset_key (str): The key for the dataset to be used in the scenario.
            algo_name (str): The name of the algorithm to be applied in the scenario.
            algo_params (Dict): Additional parameters for the algorithm.

        Returns:
            Scenario: The fully processed scenario created and executed within this method.
        """
        scenario = self._factory.create(
            tag=scenario_tag,
            dataset_key=dataset_key,
            algo_name=algo_name,
            algo_params=algo_params,
        )
        self._registry.add(scenario)
        self._processor.enqueue(scenario)
        self.wait_for_processing()
        return scenario

    def debug_etl_data(self, dataset_name: str) -> None:
        """
        Debugging utility to run ETL on a directory as if loaded on startup.
        """
        # Retrieve files from directory
        if isinstance(self._dm, StatefulDataManager):
            self._dm.load_data_from_dir(dataset_name)
        else:
            raise AttributeError(
                "Stateless data manager does not support internal ETL."
            )

    def debug_load_serialized_data(self, file_name: str):
        """
        Debugging utility to upload a file as if loaded on startup.
        """
        if isinstance(self._dm, StatefulDataManager):
            self._dm.load_data_from_file(file_name)
        else:
            raise AttributeError(
                "Stateless data manager does not support internal deserialization."
            )

    def debug_import_data(self, directory: str) -> None:
        """
        Debugging utility to import data from a directory.
        """
        raise NotImplementedError("todo: write import data method")

    def debug_upload_data(self, file_name: str) -> None:
        """
        Debugging utility to upload data from a file.
        """
        raise NotImplementedError("todo: write upload data method")
