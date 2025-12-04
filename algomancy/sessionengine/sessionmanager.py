import os
from typing import Dict, List, TypeVar

from algomancy.appconfiguration import AppConfiguration
from algomancy.dashboardlogger import Logger, MessageStatus
from algomancy.dataengine import ETLFactory, InputFileConfiguration, BASE_DATA_BOUND
from algomancy.scenarioengine import KpiTemplate, AlgorithmTemplate, ScenarioManager


class SessionManager:
    """ """

    E = TypeVar("E", bound=ETLFactory)

    @classmethod
    def from_config(cls, configuration: "AppConfiguration") -> "SessionManager":
        # Local import to avoid heavy top-level coupling
        from algomancy.appconfiguration import AppConfiguration  # type: ignore

        if not isinstance(configuration, AppConfiguration):
            raise TypeError("from_config expects an AppConfiguration instance")
        return cls(
            etl_factory=configuration.etl_factory,
            kpi_templates=configuration.kpi_templates,
            algo_templates=configuration.algo_templates,
            input_configs=configuration.input_configs,
            data_object_type=configuration.data_object_type,
            data_folder=configuration.data_path,
            has_persistent_state=configuration.has_persistent_state,
            save_type=configuration.save_type,
            autocreate=configuration.autocreate,
            default_algo_name=configuration.default_algo,
            default_param_values=configuration.default_algo_params_values,
            autorun=configuration.autorun,
        )

    def __init__(
        self,
        etl_factory: type[E],
        kpi_templates: List[KpiTemplate],
        algo_templates: Dict[str, AlgorithmTemplate],
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
        self._sessions = {}
        if self._has_persistent_state:
            assert (
                data_folder
            ), "Data folder must be specified if a persistent state is used."

            sessions = self.determine_sessions_from_folder(data_folder)
            for session_name, session_path in sessions.items():
                self._sessions[session_name] = ScenarioManager(
                    etl_factory=etl_factory,
                    kpi_templates=kpi_templates,
                    algo_templates=algo_templates,
                    input_configs=input_configs,
                    data_object_type=data_object_type,
                    data_folder=session_path,
                    logger=self.logger,
                    has_persistent_state=self._has_persistent_state,
                    save_type=self._save_type,
                    autocreate=self._auto_create_scenario,
                    default_algo_name=default_algo_name,
                    default_param_values=default_param_values,
                    autorun=autorun,
                )
        if len(self._sessions) == 0:
            self._sessions["main"] = self.create_default_scenario_manager(
                etl_factory,
                kpi_templates,
                algo_templates,
                input_configs,
                data_object_type,
                default_algo_name,
                default_param_values,
                autorun,
            )

        self._session_name = list(self._sessions.keys())[0]
        self._scenario_manager = self._sessions[self._session_name]

        self.log("SessionManager initialized.")

    def log(self, message: str, status: MessageStatus = MessageStatus.INFO) -> None:
        if self.logger:
            self.logger.log(message, status)

    @staticmethod
    def determine_sessions_from_folder(data_folder) -> Dict[str, str]:
        session_folders = {
            f.name: f.path for f in os.scandir(data_folder) if f.is_dir()
        }
        return session_folders

    def set_active_scenario_manager(self, session_name: str):
        self._session_name = session_name
        assert session_name in self._sessions, f"Session '{session_name}' not found."
        self.log(f"Active session set to '{session_name}'.")
        self._scenario_manager = self._sessions[session_name]

    def get_scenario_manager(self, session_id: str) -> ScenarioManager:
        self.log("Scenario id cannot be None when using persistent state.")
        if session_id in self._sessions:
            self.log(f"Scenario '{session_id}' not found.")
        assert session_id in self._sessions, f"Scenario '{session_id}' not found."
        return self._sessions[session_id]

    def create_default_scenario_manager(
        self,
        etl_factory,
        kpi_templates,
        algo_templates,
        input_configs,
        data_object_type,
        default_algo_name,
        default_param_values,
        autorun,
    ):
        return ScenarioManager(
            etl_factory=etl_factory,
            kpi_templates=kpi_templates,
            algo_templates=algo_templates,
            input_configs=input_configs,
            data_object_type=data_object_type,
            logger=self.logger,
            has_persistent_state=self._has_persistent_state,
            save_type=self._save_type,
            autocreate=self._auto_create_scenario,
            default_algo_name=default_algo_name,
            default_param_values=default_param_values,
            autorun=autorun,
        )

    @property
    def sessions_names(self) -> List[str]:
        return list(self._sessions.keys())

    @property
    def active_session_name(self) -> str:
        return self._session_name

    @property
    def active_scenario_manager(self) -> ScenarioManager:
        return self._scenario_manager
