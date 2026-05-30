import os
from typing import Dict, List, Optional, TypeVar, Type

from algomancy_utils.logger import Logger, MessageStatus
from algomancy_data import ETLFactory, Schema, BASEDATASOURCE

from .basealgorithm import BaseAlgorithm
from .keyperformanceindicator import BaseKPI
from .scenariomanager import ScenarioManager
from .core_configuration import CoreConfig
from algomancy_utils.baseparameterset import BaseParameterSet


def _unwrap_core_config(cfg) -> CoreConfig:
    """Accept either a CoreConfig (or subclass) or an AppConfig-style wrapper exposing `.core`."""
    if isinstance(cfg, CoreConfig):
        return cfg
    core = getattr(cfg, "core", None)
    if isinstance(core, CoreConfig):
        return core
    raise TypeError(
        "Configuration must be a CoreConfig (or subclass) or expose a `.core` "
        f"attribute of type CoreConfig; got {type(cfg).__name__}"
    )


def _validate_session_name(name: str) -> None:
    """Reject session names that would escape the data folder or break path joining.

    Sessions become subdirectories of ``data_path`` when persistent state is enabled,
    so the name must be a single safe directory segment.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("Session name must be a non-empty string.")
    if any(sep in name for sep in ("/", "\\", "\x00")):
        raise ValueError(f"Session name {name!r} must not contain path separators.")
    if name in (".", "..") or name.startswith(".."):
        raise ValueError(f"Session name {name!r} must not refer to a parent directory.")
    # Drive prefix on Windows ("C:") or relative-drive references.
    if len(name) >= 2 and name[1] == ":":
        raise ValueError(f"Session name {name!r} must not contain a drive prefix.")


class SessionManager:
    """
    Container for multiple ScenarioManagers, one per session.

    Used when ``CoreConfig.use_sessions`` is True. When persistent state is enabled,
    sessions are discovered as subdirectories of ``data_path``; otherwise a single
    default ``"main"`` session is created.

    When ``persistence_backend="database"``, sessions are stored in a
    ``algomancy_sessions`` DB table rather than as filesystem directories.
    """

    E = TypeVar("E", bound=ETLFactory)

    @classmethod
    def from_config(cls, cfg) -> "SessionManager":
        core = _unwrap_core_config(cfg)
        return cls(
            etl_factory=core.etl_factory,
            kpi_templates=core.kpi_templates,
            algo_templates=core.algo_templates,
            schemas=core.schemas,
            data_object_type=core.data_object_type,
            data_folder=core.data_path,
            has_persistent_state=core.has_persistent_state,
            save_type=core.save_type,
            auto_create=core.autocreate,
            default_algo_name=core.default_algo,
            default_param_values=core.default_algo_params_values,
            autorun=core.autorun,
            discover_sessions=core.use_sessions,
            persistence_backend=core.persistence_backend,
            database_url=core.database_url,
        )

    def __init__(
        self,
        etl_factory: type[E],
        kpi_templates: Dict[str, Type[BaseKPI]],
        algo_templates: Dict[str, Type[BaseAlgorithm]],
        schemas: List[Schema],
        data_object_type: type[BASEDATASOURCE],
        data_folder: str = None,
        logger: Logger = None,
        scenario_save_location: str = "scenarios.json",
        has_persistent_state: bool = False,
        save_type: str = "json",
        auto_create: bool = False,
        default_algo_name: str = None,
        default_param_values: Dict[str, any] = None,
        autorun: bool = False,
        discover_sessions: bool = True,
        persistence_backend: str = "none",
        database_url: str | None = None,
    ) -> None:
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
        self._discover_sessions = discover_sessions
        self._persistence_backend = persistence_backend
        self._database_url = database_url

        assert save_type in ["json"], "Save type must be parquet or json."
        self._save_type = save_type

        # Build shared DB engine when using the database backend
        self._db_engine = None
        if self._persistence_backend == "database":
            self._db_engine = self._build_engine(database_url)
            self._init_db_schema()

        self._sessions: Dict[str, ScenarioManager] = {}
        self._create_default_scenario_managers()
        self._start_session_name = list(self._sessions.keys())[0]

        self.log("SessionManager initialized.")

    # ------------------------------------------------------------------
    # Database engine helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_engine(database_url: str):
        try:
            import sqlalchemy as sa
        except ImportError as exc:
            raise ImportError(
                "SQLAlchemy is required for persistence_backend='database'. "
                "Install it with: pip install algomancy-scenario[database]"
            ) from exc
        return sa.create_engine(database_url)

    def _init_db_schema(self) -> None:
        """Create all fixed framework tables if they don't exist yet."""
        from algomancy_data.database.models import metadata as data_meta
        from .persistence.models import metadata as scenario_meta

        data_meta.create_all(self._db_engine, checkfirst=True)
        scenario_meta.create_all(self._db_engine, checkfirst=True)

    # ------------------------------------------------------------------
    # Session discovery / construction
    # ------------------------------------------------------------------

    def _create_default_scenario_managers(self) -> None:
        if self._persistence_backend == "database":
            for session_name in self._determine_sessions_from_db():
                self._create_default_scenario_manager(session_name)
        elif self._has_persistent_state:
            assert self._data_folder, (
                "Data folder must be specified if a persistent state is used."
            )
            if self._discover_sessions:
                sessions = self._determine_sessions_from_folder(self._data_folder)
                for session_name, session_path in sessions.items():
                    self._create_default_scenario_manager(session_name, session_path)
        if len(self._sessions) == 0:
            self._create_default_scenario_manager("main")

    def _determine_sessions_from_db(self) -> List[str]:
        from .persistence.models import sessions_table

        with self._db_engine.connect() as conn:
            rows = conn.execute(sessions_table.select()).fetchall()
        return [row.name for row in rows]

    def _persist_session_to_db(self, name: str) -> None:
        from datetime import datetime
        from .persistence.models import sessions_table

        with self._db_engine.begin() as conn:
            conn.execute(
                sessions_table.insert().values(name=name, created_at=datetime.now())
            )

    def log(self, message: str, status: MessageStatus = MessageStatus.INFO) -> None:
        if self.logger:
            self.logger.log(message, status)

    @staticmethod
    def _determine_sessions_from_folder(data_folder) -> Dict[str, str]:
        return {f.name: f.path for f in os.scandir(data_folder) if f.is_dir()}

    def get_scenario_manager(self, session_id: str) -> ScenarioManager:
        if session_id not in self._sessions:
            self.log(f"Session '{session_id}' not found.")
            raise KeyError(f"Session '{session_id}' not found.")
        return self._sessions[session_id]

    def has_session(self, session_id: str) -> bool:
        return session_id in self._sessions

    def _create_folder(self, name: str) -> str:
        _validate_session_name(name)
        session_folder = os.path.join(self._data_folder, name)
        os.makedirs(session_folder, exist_ok=True)
        return session_folder

    def _create_default_scenario_manager(
        self, name: str, session_path: Optional[str] = None
    ) -> None:
        if self._persistence_backend == "database":
            self._sessions[name] = self._build_db_scenario_manager(name)
            return

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

    def _build_db_scenario_manager(self, session_id: str) -> ScenarioManager:
        from algomancy_data.database.database_manager import DatabaseDataManager
        from .persistence.sql_repository import SqlScenarioRepository

        dm = DatabaseDataManager(
            etl_factory=self._etl_factory,
            schemas=self._schemas,
            engine=self._db_engine,
            session_id=session_id,
            data_object_type=self._data_object_type,
            logger=self.logger,
        )
        repo = SqlScenarioRepository(
            engine=self._db_engine,
            session_id=session_id,
            algo_templates=self._algo_templates,
            kpi_templates=self._kpi_templates,
            data_manager=dm,
            logger=self.logger,
        )
        return ScenarioManager(
            etl_factory=self._etl_factory,
            kpi_templates=self._kpi_templates,
            algo_templates=self._algo_templates,
            schemas=self._schemas,
            data_object_type=self._data_object_type,
            data_folder=None,
            logger=self.logger,
            has_persistent_state=False,
            save_type=self._save_type,
            autocreate=self._auto_create_scenario,
            default_algo_name=self._default_algo_name,
            default_param_values=self._default_param_values,
            autorun=self._autorun,
            data_manager=dm,
            scenario_repository=repo,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
        _validate_session_name(session_name)
        if session_name in self._sessions:
            raise ValueError(f"Session '{session_name}' already exists.")
        if self._persistence_backend == "database":
            self._persist_session_to_db(session_name)
        self._create_default_scenario_manager(session_name)

    def copy_session(self, session_name: str, new_session_name: str):
        _validate_session_name(new_session_name)
        if new_session_name in self._sessions:
            raise ValueError(f"Session '{new_session_name}' already exists.")
        if self._persistence_backend == "database":
            self._persist_session_to_db(new_session_name)
        self._create_default_scenario_manager(new_session_name)
        src = self.get_scenario_manager(session_name)
        dst = self.get_scenario_manager(new_session_name)
        for data_key in src.get_data_keys():
            dst.set_data(data_key, src.get_data(data_key))
