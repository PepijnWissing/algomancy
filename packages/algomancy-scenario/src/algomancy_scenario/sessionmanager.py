import json
import os
import re
import shutil
import uuid
from typing import Dict, List, Optional, TypeVar, Type

from algomancy_utils.logger import Logger, MessageStatus
from algomancy_data import ETLFactory, Schema, BASEDATASOURCE

from .basealgorithm import BaseAlgorithm
from .keyperformanceindicator import BaseKPI
from .scenariomanager import ScenarioManager
from .core_configuration import CoreConfig
from algomancy_utils.baseparameterset import BaseParameterSet


SESSION_META_FILENAME = "meta.json"


def _safe_table_segment(s: str) -> str:
    """Mirror of ``algomancy_data.database.database_manager._safe_segment``.

    Re-declared here to avoid creating a hard import dependency just for a
    string transformation. Must produce identical output: anything that
    isn't alphanumeric or underscore collapses to ``_``.
    """
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)


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


def _validate_display_name(name: str) -> None:
    """Reject display names that would be ambiguous or hostile.

    Display names are user-facing strings and may contain spaces, punctuation,
    Unicode — but they must not be empty or pure-whitespace.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Session display name must be a non-empty string.")


def _validate_directory_segment(name: str) -> None:
    """Reject directory segments that would escape the data folder.

    Used for the slugified storage directory name; never accepts user input
    directly.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("Session directory segment must be a non-empty string.")
    if any(sep in name for sep in ("/", "\\", "\x00")):
        raise ValueError(
            f"Session directory segment {name!r} must not contain path separators."
        )
    if name in (".", "..") or name.startswith(".."):
        raise ValueError(
            f"Session directory segment {name!r} must not refer to a parent directory."
        )
    if len(name) >= 2 and name[1] == ":":
        raise ValueError(
            f"Session directory segment {name!r} must not contain a drive prefix."
        )


def _slugify_for_directory(display_name: str) -> str:
    """Produce a safe filesystem directory segment from a display name.

    Keeps ASCII letters, digits, dash, underscore and dot. Everything else
    collapses to underscore. Empty results fall back to ``"session"``.
    """
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", display_name).strip("._-")
    return slug or "session"


def _new_session_uuid() -> str:
    return str(uuid.uuid4())


class SessionManager:
    """
    Container for multiple ScenarioManagers, one per session.

    A SessionManager is always present in both GUI and API deployments. When
    persistent state is enabled, sessions are discovered as subdirectories of
    ``data_path`` (filesystem backend) or as rows of ``algomancy_sessions``
    (database backend). If no sessions exist yet, a single default session
    named ``"main"`` is created so the runtime always has somewhere to put
    scenarios.

    **Identity model.** Each session has a UUID ``id`` (stable, opaque) and a
    mutable ``display_name`` shown in UIs. Routes and the GUI dropdown value
    use the ``id``; only labels show the ``display_name``. For the filesystem
    backend the on-disk directory name is the slugified display name at
    creation time and never changes thereafter — renaming a session only
    updates ``meta.json``.
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
        self._display_names: Dict[str, str] = {}
        self._directory_names: Dict[str, str] = {}  # only used by filesystem backend
        self._create_default_scenario_managers()
        self._start_session_id = list(self._sessions.keys())[0]

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
            for row in self._load_sessions_from_db():
                self._register_db_session(row["id"], row["display_name"])
        elif self._has_persistent_state:
            assert self._data_folder, (
                "Data folder must be specified if a persistent state is used."
            )
            for session_id, display_name, dir_name in self._load_sessions_from_folder():
                self._register_filesystem_session(session_id, display_name, dir_name)
        if len(self._sessions) == 0:
            # Auto-create the "main" default so the runtime always has somewhere
            # to put scenarios. This is the single-tenant baseline.
            self.create_new_session("main")

    def _load_sessions_from_db(self) -> List[dict]:
        from .persistence.models import sessions_table

        with self._db_engine.connect() as conn:
            rows = conn.execute(sessions_table.select()).fetchall()
        return [{"id": row.id, "display_name": row.display_name} for row in rows]

    def _persist_session_to_db(self, session_id: str, display_name: str) -> None:
        from datetime import datetime
        from .persistence.models import sessions_table

        with self._db_engine.begin() as conn:
            conn.execute(
                sessions_table.insert().values(
                    id=session_id,
                    display_name=display_name,
                    created_at=datetime.now(),
                )
            )

    def _update_display_name_in_db(self, session_id: str, display_name: str) -> None:
        from .persistence.models import sessions_table

        with self._db_engine.begin() as conn:
            conn.execute(
                sessions_table.update()
                .where(sessions_table.c.id == session_id)
                .values(display_name=display_name)
            )

    def _load_sessions_from_folder(self) -> List[tuple[str, str, str]]:
        """Scan data_folder for session directories; return (id, display_name, dir_name).

        Each session directory has a ``meta.json`` carrying its UUID id and
        mutable display name. Directories without ``meta.json`` are
        backfilled on first read: a UUID is generated and the directory name
        becomes the initial display name. The meta file is written so
        subsequent runs are stable.
        """
        result: List[tuple[str, str, str]] = []
        for entry in os.scandir(self._data_folder):
            if not entry.is_dir():
                continue
            meta_path = os.path.join(entry.path, SESSION_META_FILENAME)
            meta = self._read_or_init_session_meta(meta_path, entry.name)
            result.append((meta["id"], meta["display_name"], entry.name))
        return result

    @staticmethod
    def _read_or_init_session_meta(meta_path: str, fallback_display_name: str) -> dict:
        if os.path.isfile(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            # Validate required fields; tolerate extra keys for forward compat.
            if "id" not in meta or "display_name" not in meta:
                raise ValueError(
                    f"Session meta at {meta_path} is missing required fields"
                )
            return meta
        meta = {"id": _new_session_uuid(), "display_name": fallback_display_name}
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        return meta

    def _write_session_meta(
        self, dir_name: str, session_id: str, display_name: str
    ) -> None:
        if not self._has_persistent_state or self._persistence_backend != "json":
            return
        meta_path = os.path.join(self._data_folder, dir_name, SESSION_META_FILENAME)
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"id": session_id, "display_name": display_name}, f, indent=2)

    def log(self, message: str, status: MessageStatus = MessageStatus.INFO) -> None:
        if self.logger:
            self.logger.log(message, status)

    def get_scenario_manager(self, session_id: str) -> ScenarioManager:
        """Look up a ScenarioManager by session UUID.

        Falls back to a ``display_name`` lookup so casual callers (smoke
        tests, single-tenant deployments using human-readable session names)
        can still address the manager without first translating the name to
        a UUID. Authoritative code paths should always pass the UUID.
        """
        if session_id in self._sessions:
            return self._sessions[session_id]
        resolved = self.resolve_id_by_display_name(session_id)
        if resolved is not None:
            return self._sessions[resolved]
        self.log(f"Session '{session_id}' not found.")
        raise KeyError(f"Session '{session_id}' not found.")

    def has_session(self, session_id: str) -> bool:
        return session_id in self._sessions

    # ------------------------------------------------------------------
    # Session registration helpers
    # ------------------------------------------------------------------

    def _register_filesystem_session(
        self, session_id: str, display_name: str, dir_name: str
    ) -> None:
        session_path = (
            os.path.join(self._data_folder, dir_name)
            if self._has_persistent_state
            else None
        )
        self._sessions[session_id] = ScenarioManager(
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
        self._display_names[session_id] = display_name
        self._directory_names[session_id] = dir_name

    def _register_db_session(self, session_id: str, display_name: str) -> None:
        self._sessions[session_id] = self._build_db_scenario_manager(session_id)
        self._display_names[session_id] = display_name

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
    def session_ids(self) -> List[str]:
        return list(self._sessions.keys())

    @property
    def start_session_id(self) -> str:
        return self._start_session_id

    def list_sessions(self) -> List[Dict[str, str]]:
        """Return the (id, display_name) for every session.

        The shape matches what the API and GUI need: an opaque identifier the
        URL/store carries, and a human label for display."""
        return [
            {"id": sid, "display_name": self._display_names.get(sid, sid)}
            for sid in self._sessions
        ]

    def get_display_name(self, session_id: str) -> str:
        if session_id not in self._sessions:
            raise KeyError(f"Session '{session_id}' not found.")
        return self._display_names.get(session_id, session_id)

    def get_algorithm_parameters(self, key) -> BaseParameterSet:
        template: Type[BaseAlgorithm] = self._algo_templates.get(key)
        if template is None:
            raise KeyError(f"Unable to find template {key} in the available templates.")
        return template.initialize_parameters()

    def _pick_unique_directory_name(self, base: str) -> str:
        """Find a free directory segment under data_folder based on ``base``."""
        candidate = base
        counter = 1
        existing = set(self._directory_names.values())
        while True:
            if candidate not in existing and not os.path.exists(
                os.path.join(self._data_folder, candidate)
            ):
                return candidate
            counter += 1
            candidate = f"{base}-{counter}"

    def create_new_session(self, display_name: str) -> str:
        """Create a session under ``display_name`` and return its UUID id."""
        _validate_display_name(display_name)
        if display_name in self._display_names.values():
            raise ValueError(f"Session '{display_name}' already exists.")
        session_id = _new_session_uuid()
        if self._persistence_backend == "database":
            self._persist_session_to_db(session_id, display_name)
            self._register_db_session(session_id, display_name)
            return session_id

        if self._has_persistent_state:
            slug = _slugify_for_directory(display_name)
            _validate_directory_segment(slug)
            dir_name = self._pick_unique_directory_name(slug)
            os.makedirs(os.path.join(self._data_folder, dir_name), exist_ok=True)
            self._write_session_meta(dir_name, session_id, display_name)
        else:
            dir_name = _slugify_for_directory(display_name)
        self._register_filesystem_session(session_id, display_name, dir_name)
        return session_id

    def copy_session(self, source_id: str, new_display_name: str) -> str:
        """Copy ``source_id``'s data into a new session and return its UUID."""
        if source_id not in self._sessions:
            raise KeyError(f"Session '{source_id}' not found.")
        new_id = self.create_new_session(new_display_name)
        src = self._sessions[source_id]
        dst = self._sessions[new_id]
        for data_key in src.get_data_keys():
            dst.set_data(data_key, src.get_data(data_key))
        return new_id

    def rename_session(self, session_id: str, new_display_name: str) -> None:
        """Change the display name of an existing session in-place."""
        if session_id not in self._sessions:
            raise KeyError(f"Session '{session_id}' not found.")
        _validate_display_name(new_display_name)
        if new_display_name == self._display_names.get(session_id):
            return
        if new_display_name in self._display_names.values():
            raise ValueError(f"Session '{new_display_name}' already exists.")
        self._display_names[session_id] = new_display_name
        if self._persistence_backend == "database":
            self._update_display_name_in_db(session_id, new_display_name)
        elif self._has_persistent_state:
            dir_name = self._directory_names[session_id]
            self._write_session_meta(dir_name, session_id, new_display_name)

    def delete_session(self, session_id: str) -> None:
        """Remove a session and all its scenarios, runs, KPIs, and data.

        Refuses to leave the SessionManager in an empty state: if the deleted
        session was the only one, a fresh default ``"main"`` session is
        created in its place so the runtime always has somewhere to put
        scenarios.

        Filesystem backend: the session directory is removed with
        ``shutil.rmtree``.

        Database backend: all rows scoped to this session in the framework
        tables (``algomancy_scenarios``, ``algomancy_scenario_runs``,
        ``algomancy_kpi_measurements``, ``algomancy_datasets``) are deleted
        — FK cascades chain runs and KPI measurements automatically — and
        every ``ds__{session_id}__*`` data table is dropped.
        """
        if session_id not in self._sessions:
            raise KeyError(f"Session '{session_id}' not found.")

        if self._persistence_backend == "database":
            self._cascade_delete_db_session(session_id)
        elif self._has_persistent_state and self._persistence_backend == "json":
            dir_name = self._directory_names.get(session_id)
            if dir_name is not None:
                session_path = os.path.join(self._data_folder, dir_name)
                if os.path.isdir(session_path):
                    shutil.rmtree(session_path)

        del self._sessions[session_id]
        self._display_names.pop(session_id, None)
        self._directory_names.pop(session_id, None)
        if self._start_session_id == session_id:
            self._start_session_id = next(iter(self._sessions), session_id)

        if not self._sessions:
            # Re-establish the default session so callers always have a
            # ScenarioManager to write into.
            new_default_id = self.create_new_session("main")
            self._start_session_id = new_default_id

        self.log(f"Session '{session_id}' deleted.")

    def _cascade_delete_db_session(self, session_id: str) -> None:
        import sqlalchemy as sa

        from .persistence.models import (
            scenarios_table,
            sessions_table,
        )

        with self._db_engine.begin() as conn:
            # Scenarios cascade-delete their runs + KPI measurements via FK.
            conn.execute(
                scenarios_table.delete().where(
                    scenarios_table.c.session_id == session_id
                )
            )
            conn.execute(
                sessions_table.delete().where(sessions_table.c.id == session_id)
            )
            # Drop dataset catalogue rows + dynamic ds__ tables.
            try:
                from algomancy_data.database.models import datasets_table

                conn.execute(
                    datasets_table.delete().where(
                        datasets_table.c.session_id == session_id
                    )
                )
            except ImportError:
                # intentional pass: the target table is already gone.
                pass
            inspector = sa.inspect(conn)
            prefix = f"ds__{_safe_table_segment(session_id)}__"
            for table_name in inspector.get_table_names():
                if table_name.startswith(prefix):
                    conn.execute(sa.text(f"DROP TABLE {table_name}"))

    def resolve_id_by_display_name(self, display_name: str) -> Optional[str]:
        """Look up a session by its (currently mutable) display name.

        Returns ``None`` when no match exists. Migration scripts, tests, and
        users who know a session only by its name use this to bridge to the
        new UUID identity.
        """
        for sid, name in self._display_names.items():
            if name == display_name:
                return sid
        return None
