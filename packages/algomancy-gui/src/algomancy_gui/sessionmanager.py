import os
from typing import Dict, List, TypeVar, Type

from algomancy_gui.appconfiguration import AppConfiguration
from algomancy_utils.logger import Logger, MessageStatus
from algomancy_data import ETLFactory, Schema, BASE_DATA_BOUND
from algomancy_scenario import (
    ScenarioManager,
    BaseKPI,
    BaseAlgorithm,
    BaseParameterSet,
)


class SessionManager:
    """
    Container for all the scenario managers.
    Can create a default scenario manager when a new session is created.
    """

    E = TypeVar("E", bound=ETLFactory)

    @classmethod
    def from_config(cls, configuration: "AppConfiguration") -> "SessionManager":
        # Local import to avoid heavy top-level coupling
        from algomancy_gui.appconfiguration import AppConfiguration  # type: ignore

        if not isinstance(configuration, AppConfiguration):
            raise TypeError("from_config expects an AppConfiguration instance")
        return cls(
            etl_factory=configuration.etl_factory,
            kpi_templates=configuration.kpi_templates,
            algo_templates=configuration.algo_templates,
            schemas=configuration.schemas,
            data_object_type=configuration.data_object_type,
            data_folder=configuration.data_path,
            has_persistent_state=configuration.has_persistent_state,
            save_type=configuration.save_type,
            auto_create=configuration.autocreate,
            default_algo_name=configuration.default_algo,
            default_param_values=configuration.default_algo_params_values,
            autorun=configuration.autorun,
        )

    def __init__(
        self,
        etl_factory: type[E],
        kpi_templates: Dict[str, Type[BaseKPI]],
        algo_templates: Dict[str, Type[BaseAlgorithm]],
        schemas: List[Schema],
        data_object_type: type[BASE_DATA_BOUND],  # for extensions of datasource
        data_folder: str = None,
        logger: Logger = None,
        scenario_save_location: str = "scenarios.json",
        has_persistent_state: bool = False,
        save_type: str = "json",  # adjusts the format
        auto_create: bool = False,
        default_algo_name: str = None,
        default_param_values: Dict[str, any] = None,
        autorun: bool = False,
    ) -> None:
        # Store general information
        self.logger = logger if logger else Logger()
        self._etl_factory = etl_factory
        self._kpi_templates = kpi_templates
        self._algo_templates = algo_templates
        self._schemas = schemas
        self._data_object_type = data_object_type
        self._autorun = autorun
        self._scenario_save_location = scenario_save_location
        self._data_folder = data_folder
        self._has_persistent_state = has_persistent_state
        self._auto_create_scenario = auto_create
        self._default_algo_name = default_algo_name
        self._default_param_values = default_param_values
        self._algo_templates = algo_templates

        assert save_type in ["json"], "Save type must be parquet or json."
        self._save_type = save_type

        # Create sessions
        self._sessions = {}
        self._create_default_scenario_managers()
        self._start_session_name = list(self._sessions.keys())[0]

        self.log("SessionManager initialized.")

    def _create_default_scenario_managers(self) -> None:
        if self._has_persistent_state:
            assert self._data_folder, (
                "Data folder must be specified if a persistent state is used."
            )

            sessions = self._determine_sessions_from_folder(self._data_folder)
            for session_name, session_path in sessions.items():
                self._create_default_scenario_manager(session_name, session_path)
        if len(self._sessions) == 0:
            self._create_default_scenario_manager("main")

    def log(self, message: str, status: MessageStatus = MessageStatus.INFO) -> None:
        if self.logger:
            self.logger.log(message, status)

    @staticmethod
    def _determine_sessions_from_folder(data_folder) -> Dict[str, str]:
        session_folders = {
            f.name: f.path for f in os.scandir(data_folder) if f.is_dir()
        }
        return session_folders

    def get_scenario_manager(self, session_id: str) -> ScenarioManager:
        if session_id not in self._sessions:
            self.log(f"Session '{session_id}' not found.")
        assert session_id in self._sessions, f"Scenario '{session_id}' not found."
        return self._sessions[session_id]

    def _create_folder(self, name: str) -> str:
        session_folder = self._data_folder + "/" + name
        os.makedirs(session_folder, exist_ok=True)
        return session_folder

    def _create_default_scenario_manager(
        self, name: str, session_path: str = None
    ) -> None:
        if not self._has_persistent_state:
            session_path = None
        elif self._has_persistent_state and session_path is None:
            session_path = self._create_folder(name)

        self._sessions[name] = ScenarioManager(
            etl_factory=self._etl_factory,
            kpi_templates=self._kpi_templates,
            algo_templates=self._algo_templates,
            schemas=self._schemas,
            data_object_type=self._data_object_type,
            data_folder=session_path,
            logger=self.logger,
            has_persistent_state=self._has_persistent_state,
            save_type=self._save_type,
            autocreate=self._auto_create_scenario,
            default_algo_name=self._default_algo_name,
            default_param_values=self._default_param_values,
            autorun=self._autorun,
        )

    @property
    def sessions_names(self) -> List[str]:
        return list(self._sessions.keys())

    @property
    def start_session_name(self) -> str:
        return self._start_session_name

    def get_algorithm_parameters(self, key) -> BaseParameterSet:
        template: Type[BaseAlgorithm] = self._algo_templates.get(key)
        if template is None:
            raise KeyError(f"Unable to find template {key} in the available templates.")
        return template.initialize_parameters()

    def create_new_session(self, session_name: str) -> None:
        self._create_default_scenario_manager(session_name)

    def copy_session(self, session_name: str, new_session_name: str):
        self._create_default_scenario_manager(new_session_name)

        for data_key in self.get_scenario_manager(session_name).get_data_keys():
            data = self.get_scenario_manager(session_name).get_data(data_key)
            self.get_scenario_manager(new_session_name).set_data(data_key, data)
