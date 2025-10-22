from typing import Dict, List, Optional, TypeVar, Type

from tabulate import tabulate

from algomancy.dataengine.datamanager import (ETLFactory,
                           InputFileConfiguration,
                           StatefulDataManager,
                           StatelessDataManager,
                           DataSource)
from algomancy.dashboardlogger.logger import Logger,MessageStatus

from .algorithmtemplate import AlgorithmTemplate
from .keyperformanceindicator import KpiTemplate
from .scenario import Scenario
from .scenarioregistry import ScenarioRegistry
from .scenariofactory import ScenarioFactory
from .scenarioprocessor import ScenarioProcessor


class ScenarioManager:
    """
    Facade that coordinates data management, scenario creation/registry, and processing.
    """
    E = TypeVar("E", bound=ETLFactory)
    DOT = TypeVar("DOT", bound=DataSource)

    def __init__(
            self,
            etl_factory: type[E],
            kpi_templates: List[KpiTemplate],
            algo_templates: Dict[str, AlgorithmTemplate],
            input_configs: List[InputFileConfiguration],
            data_object_type: type[DOT],  # for extensions of datasource
            data_folder: str = None,
            logger: Logger = None,
            scenario_save_location: str = "scenarios.json",
            has_persistent_state: bool = False,
            save_type: str = "parquet",  # adjusts the format
    ) -> None:
        self.logger = logger if logger else Logger()
        self.scenario_save_location = scenario_save_location
        self._has_persistent_state = has_persistent_state

        assert save_type in ["parquet", "json"], "Save type must be parquet or json."
        self._save_type = save_type

        # Components
        if self._has_persistent_state:
            assert data_folder, "Data folder must be specified if data manager has state."
            self.dm = StatefulDataManager(etl_factory=etl_factory, input_configs=input_configs,
                                          data_folder=data_folder, save_type=save_type,
                                          data_object_type=data_object_type, logger=self.logger)
        else:
            self.dm = StatelessDataManager(etl_factory=etl_factory, input_configs=input_configs, save_type=save_type,
                                           logger=self.logger, data_object_type=data_object_type)

        self.registry = ScenarioRegistry(logger=self.logger)
        self.factory = ScenarioFactory(kpi_templates=kpi_templates, algo_templates=algo_templates,
                                       data_manager=self.dm, logger=self.logger)
        self.processor = ScenarioProcessor(logger=self.logger)

        # Keep inputs for accessors
        self._algo_templates = algo_templates
        self._input_configs = input_configs

        # Load initial data
        try:
            self.dm.startup()
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
        return self.factory.available_algorithms

    @property
    def auto_run_scenarios(self):
        return self.processor.auto_run_scenarios

    @property
    def currently_processing(self) -> Optional[Scenario]:
        return self.processor.currently_processing

    def get_algorithm_template(self, key) -> AlgorithmTemplate:
        return self._algo_templates.get(key)

    # Data operations (delegated)
    def get_data_keys(self) -> List[str]:
        return self.dm.get_data_keys()

    def get_data(self, data_key):
        return self.dm.get_data(data_key)

    def derive_data(self, derive_from_key: str, new_data_key: str) -> None:
        self.dm.derive_data(derive_from_key, new_data_key)

    def delete_data(self, data_key: str, prevent_masterdata_removal: bool = False) -> None:
        # prevent delete if used by scenarios
        assert data_key not in self.registry.used_datasets(), f"Cannot delete data used in scenarios."
        self.dm.delete_data(data_key, prevent_masterdata_removal)

    # def load_data_from_dir(self, directory: str, root: str = None) -> None:
    #     if isinstance(self.dm, StatefulDataManager):
    #         if self.logger:
    #             self.logger.warning(f"(DeprecatedWarning): ScenarioManager.load_data_from_dir is deprecated. "
    #                                 f"Use DataManager.load_data_from_dir instead.")
    #         self.dm.load_data_from_dir(directory, root)
    #     else:
    #         if self.logger:
    #             self.logger.warning(f"(DeprecatedWarning): ScenarioManager.load_data_from_dir is deprecated. "
    #                                 f"Use DataManager.load_data_from_dir instead.")
    #             self.logger.error(f"Load data from dir is not supported for stateless data manager. ")
    #         pass

    # def create_validator(self):
    #     return self.dm.create_validation_sequence()

    def store_data(self, dataset_name: str, data):
        if isinstance(self.dm, StatefulDataManager):
            self.dm.store_data(dataset_name, data)
        else:
            if self.logger:
                self.logger.error(f"Store data is not supported for stateless data manager. ")
            pass

    def toggle_autorun(self, value: bool = None) -> None:
        if value is None:
            self.processor.auto_run_scenarios = not self.processor.auto_run_scenarios
        else:
            self.processor.auto_run_scenarios = value
        self.log(f"Auto-run scenarios set to {self.processor.auto_run_scenarios}")

    # Processing operations (delegated)
    def process_scenario_async(self, scenario):
        self.processor.enqueue(scenario)

    def wait_for_processing(self):
        self.processor.wait_for_processing()

    def shutdown_processing(self):
        self.processor.shutdown()

    # Scenario creation/registry
    def create_scenario(self, tag: str, dataset_key: str = "Master data", algo_name: str = "",
                        algo_params=None) -> Scenario:
        if self.registry.has_tag(tag):
            self.log(f"Scenario with tag '{tag}' already exists. Skipping creation.")
            raise ValueError(f"A scenario with tag '{tag}' already exists.")

        scenario = self.factory.create(tag=tag, dataset_key=dataset_key, algo_name=algo_name, algo_params=algo_params)
        self.registry.add(scenario)

        if self.processor.auto_run_scenarios:
            self.processor.enqueue(scenario)
        return scenario

    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        return self.registry.get_by_id(scenario_id)

    def get_by_tag(self, tag: str) -> Optional[Scenario]:
        return self.registry.get_by_tag(tag)

    def delete_scenario(self, scenario_id: str) -> bool:
        return self.registry.delete(scenario_id)

    def list_scenarios(self) -> List[Scenario]:
        return self.registry.list()

    def list_ids(self):
        return self.registry.list_ids()

    def list_scenario_kpis(self, print_as_table=False) -> Dict[str, Dict[str, any]]:
        completed_scenarios = [s for s in self.registry.list() if s.is_completed()]
        first_scenario = completed_scenarios[0]
        assert first_scenario, "No scenarios completed yet"

        if print_as_table:
            headers = ["Scenario"] + [(f"{kpi.name} ({kpi.UOM})" if kpi.UOM else kpi.name) for kpi in
                                      first_scenario._kpis.values()]
            table = [[s.tag] + [kpi.value for kpi in s._kpis.values()] for s in completed_scenarios]
            print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
            print(table)
        return {s.tag: {"kpis": s._kpis} for s in completed_scenarios}

    def debug_load_data(self, dataset_name: str) -> None:
        if isinstance(self.dm, StatefulDataManager):
            self.dm.load_data_from_dir("data")
        elif isinstance(self.dm, StatelessDataManager):
            raise NotImplementedError("Todo: implement loading for stateless data manager.")

            # Process the files
            files = prepare_files_from_upload(sm, filenames, contents)

            # Load the data
            self.dm.etl_data(files, dataset_name)
        else:
            raise Exception("Data manager not initialized.")

    def debug_create_and_run_scenario(
            self, scenario_tag: str, dataset_key: str, algo_name: str, algo_params: Dict[str, any]
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
        scenario = self.factory.create(
            tag=scenario_tag,
            dataset_key=dataset_key,
            algo_name=algo_name,
            algo_params=algo_params
        )
        self.registry.add(scenario)
        self.processor.enqueue(scenario)
        self.wait_for_processing()
        return scenario

    def debug_etl_data(self, dataset_name: str) -> None:
        """
        Debugging utility to run ETL on a directory as if loaded on startup.
        """
        # Retrieve files from directory
        if isinstance(self.dm, StatefulDataManager):
            self.dm.load_data_from_dir(dataset_name)
        else:
            raise AttributeError("Stateless data manager does not support internal ETL.")

    def debug_load_serialized_data(self, file_name: str):
        """
        Debugging utility to upload a file as if loaded on startup.
        """
        if isinstance(self.dm, StatefulDataManager):
            self.dm.load_data_from_file(file_name)
        else:
            raise AttributeError("Stateless data manager does not support internal deserialization.")

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
