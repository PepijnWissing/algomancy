"""SQL-backed ScenarioRepository implementation.

Persists scenario definitions, run history, and KPI measurements to a
SQLAlchemy-compatible database (SQLite or Postgres).

**Lazy startup.** ``startup()`` loads only *metadata* — one lightweight
:class:`ScenarioRecord` per scenario (definition, latest-run metadata, and
persisted KPI values) — with no dataset fetch and no result payload read. Full
:class:`Scenario` objects are materialised lazily, per id, only when a detail /
run / reset path calls :meth:`get_by_id`, and are held in a bounded LRU cache
(``hydrated_cache_size``; ``None`` = unbounded, the framework default). An
actively-running scenario is *pinned* (kept resident, counted outside the LRU
limit) from enqueue until its run is persisted. Failed hydrations are left
uncached so later requests can retry.

Scenario results that implement :class:`SqlResultLayout` are stored in shared
per-sub-table SQL tables (``algomancy_result__<sub>``) keyed by session and
scenario discriminator columns — the table count is bounded by the result
shape, not by the number of scenarios. Results that do not implement the
protocol fall back to a JSON blob on ``algomancy_scenario_runs.result_blob``.

The repository reconstructs ``Scenario`` objects on demand by matching stored
``algorithm_name`` and ``kpi_names`` against the in-process template
dictionaries. If a referenced template no longer exists (or its dataset is
gone), hydration returns ``None`` and a warning is logged rather than silently
dropping the metadata record.
"""

from __future__ import annotations

import json
import re
import threading
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Type

import pandas as pd
import sqlalchemy as sa
from algomancy_utils.logger import Logger

from ..algorithmfactory import AlgorithmFactory
from ..basealgorithm import ALGORITHM
from ..keyperformanceindicator import BASE_KPI
from ..kpifactory import KpiFactory
from ..result import BaseScenarioResult
from ..scenario import Scenario, ScenarioStatus
from .models import (
    RESULT_TABLE_PREFIX,
    SCENARIO_COL,
    SESSION_COL,
    kpi_measurements_table,
    metadata as _scenario_metadata,
    scenario_runs_table,
    scenarios_table,
)
from .protocols import SqlResultLayout
from ..records import ScenarioRecord, build_kpi_dicts


def _safe_segment(s: str) -> str:
    """Collapse anything that is not alphanumeric or underscore into ``_``."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)


def _result_table_name(sub_table: str) -> str:
    """Shared physical table name for a given result sub-table name."""
    return f"{RESULT_TABLE_PREFIX}{_safe_segment(sub_table)}"


class SqlScenarioRepository:
    """ScenarioRepository backed by a SQL database.

    Args:
        engine: A SQLAlchemy ``Engine`` for the target database.
        session_id: Logical session name that scopes all reads/writes.
        algorithms: Algorithm class registry (same as ``CoreConfig.algorithms``).
        kpis: KPI class registry (same as ``CoreConfig.kpis``).
        data_manager: DataManager used to load ``input_data`` when hydrating
            scenarios from the database.
        hydrated_cache_size: Maximum number of fully hydrated (non-pinned)
            ``Scenario`` objects to keep resident. ``None`` (the default) keeps
            an unbounded cache — behaviour-compatible with eager backends.
        eager_startup: When ``True``, hydrate every scenario at ``startup()``
            instead of lazily on first access — reproducing the pre-0.10 "all
            scenarios ready in memory" behaviour. Only meaningful with an
            unbounded cache; with a bounded cache only the last
            ``hydrated_cache_size`` warmed scenarios stay resident.
        logger: Optional logger instance.
    """

    def __init__(
        self,
        engine: sa.Engine,
        session_id: str,
        algorithms: Dict[str, Type[ALGORITHM]],
        kpis: Dict[str, Type[BASE_KPI]],
        data_manager,
        hydrated_cache_size: int | None = None,
        eager_startup: bool = False,
        logger: Logger | None = None,
    ) -> None:
        self._engine = engine
        self._session_id = session_id
        self._algo_factory = AlgorithmFactory(algorithms, logger)
        self._kpi_factory = KpiFactory(kpis)
        self._data_manager = data_manager
        self._cache_size = hydrated_cache_size
        self._eager_startup = eager_startup
        self._logger = logger
        # Metadata index (populated at startup, kept in sync on every mutation).
        self._records: Dict[str, ScenarioRecord] = {}
        self._tag_index: Dict[str, str] = {}  # tag → id
        # Bounded LRU of fully hydrated scenarios + pins for active runs.
        self._hydrated: "OrderedDict[str, Scenario]" = OrderedDict()
        self._pinned: set[str] = set()
        # Synchronisation: a coarse RLock for the shared dicts, plus a per-id
        # lock so concurrent requests for the same scenario hydrate it once.
        self._lock = threading.RLock()
        self._key_locks: Dict[str, threading.Lock] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def startup(self) -> None:
        """Initialise DB schema and load scenario *metadata* into memory.

        Loads one :class:`ScenarioRecord` per scenario — definition, latest-run
        metadata, and persisted KPI values — with no dataset fetch and no result
        payload read. Full scenarios hydrate lazily on first access.
        """
        _scenario_metadata.create_all(self._engine, checkfirst=True)
        self._migrate_add_data_parameter_values_column()
        with self._engine.connect() as conn:
            rows = conn.execute(
                scenarios_table.select().where(
                    scenarios_table.c.session_id == self._session_id
                )
            ).fetchall()

        scenario_ids = [row.id for row in rows]
        latest_runs = self._load_latest_runs(scenario_ids)
        run_ids = [r.run_id for r in latest_runs.values()]
        kpi_values = self._load_kpi_values(run_ids)

        with self._lock:
            for row in rows:
                latest = latest_runs.get(row.id)
                values = kpi_values.get(latest.run_id, {}) if latest else {}
                record = self._build_record(row, latest, values)
                self._records[record.id] = record
                self._tag_index[record.tag] = record.id
        self._log(
            f"SqlScenarioRepository startup for session '{self._session_id}': "
            f"loaded metadata for {len(self._records)} scenarios."
        )

        if self._eager_startup:
            # Opt-in legacy behaviour: fully hydrate every scenario now rather
            # than lazily. list() warms them all through get_by_id.
            hydrated = len(self.list())
            self._log(
                f"SqlScenarioRepository eager startup for session "
                f"'{self._session_id}': hydrated {hydrated} scenarios."
            )

    # ------------------------------------------------------------------
    # ScenarioRepository protocol
    # ------------------------------------------------------------------

    def add(self, scenario: Scenario) -> None:
        # serialize() already returns a JSON string; store it directly
        params_json = "{}"
        if hasattr(scenario._algorithm, "params"):
            params_json = scenario._algorithm.params.serialize()
        data_params_json: Optional[str] = None
        if scenario.data_params is not None and scenario.data_params.has_inputs():
            data_params_json = scenario.data_params.serialize()
        kpi_names = list(scenario.kpis.keys())
        created_at = datetime.now()
        with self._engine.begin() as conn:
            conn.execute(
                scenarios_table.insert().values(
                    id=scenario.id,
                    tag=scenario.tag,
                    session_id=self._session_id,
                    input_data_key=scenario.input_data_key,
                    algorithm_name=scenario._algorithm.name,
                    parameter_values=params_json,
                    data_parameter_values=data_params_json,
                    kpi_names=json.dumps(kpi_names),
                    status=str(scenario.status),
                    created_at=created_at,
                )
            )
        record = ScenarioRecord.from_scenario(scenario)
        record.created_at = created_at
        with self._lock:
            self._records[scenario.id] = record
            self._tag_index[scenario.tag] = scenario.id
            # Cache the live instance so autorun/enqueue processes and polls the
            # same object; eviction leaves it (it was just accessed → newest).
            self._hydrated[scenario.id] = scenario
            self._hydrated.move_to_end(scenario.id)
            self._evict_if_needed()
        self._log(f"Registered scenario '{scenario.tag}'.")

    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        with self._lock:
            scenario = self._hydrated.get(scenario_id)
            if scenario is not None:
                self._hydrated.move_to_end(scenario_id)
                return scenario
            record = self._records.get(scenario_id)
        if record is None:
            return None

        # Serialise hydration of the same id across threads.
        key_lock = self._get_key_lock(scenario_id)
        with key_lock:
            with self._lock:
                scenario = self._hydrated.get(scenario_id)
                if scenario is not None:
                    self._hydrated.move_to_end(scenario_id)
                    return scenario
                record = self._records.get(scenario_id)
            if record is None:
                return None
            scenario = self._rehydrate_by_id(record)
            if scenario is None:
                # Leave uncached so a later request can retry (e.g. once the
                # dataset is added back to the DataManager).
                return None
            with self._lock:
                self._hydrated[scenario_id] = scenario
                self._hydrated.move_to_end(scenario_id)
                self._evict_if_needed()
            return scenario

    def get_by_tag(self, tag: str) -> Optional[Scenario]:
        with self._lock:
            scenario_id = self._tag_index.get(tag)
        return self.get_by_id(scenario_id) if scenario_id else None

    def delete(self, scenario_id: str) -> bool:
        with self._lock:
            record = self._records.get(scenario_id)
            if record is None:
                return False
            tag = record.tag
        sub_tables = self._collect_sub_tables(scenario_id)
        existing_tables = set(sa.inspect(self._engine).get_table_names())
        with self._engine.begin() as conn:
            # Cascade in DB (FK ON DELETE CASCADE) handles scenario_runs and
            # kpi_measurements rows. If the DB doesn't enforce FK constraints
            # (SQLite default), clean up manually.
            conn.execute(
                sa.text(
                    "DELETE FROM algomancy_kpi_measurements WHERE run_id IN "
                    "(SELECT run_id FROM algomancy_scenario_runs WHERE scenario_id = :sid)"
                ),
                {"sid": scenario_id},
            )
            conn.execute(
                scenario_runs_table.delete().where(
                    scenario_runs_table.c.scenario_id == scenario_id
                )
            )
            conn.execute(
                scenarios_table.delete().where(scenarios_table.c.id == scenario_id)
            )
            self._delete_result_rows(conn, scenario_id, sub_tables, existing_tables)
        with self._lock:
            self._records.pop(scenario_id, None)
            if self._tag_index.get(tag) == scenario_id:
                del self._tag_index[tag]
            self._hydrated.pop(scenario_id, None)
            self._pinned.discard(scenario_id)
            self._key_locks.pop(scenario_id, None)
        self._log(f"Deleted scenario '{tag}'.")
        return True

    def refresh(self, scenario_id: str) -> bool:
        """Drop persisted run state for ``scenario_id``, keeping the scenario row.

        Deletes every ``algomancy_scenario_runs`` row for the scenario and every
        ``algomancy_kpi_measurements`` row hanging off those runs, removes any
        per-result rows in the shared ``algomancy_result__<sub>`` tables, and
        rewrites ``algomancy_scenarios.status`` to ``'created'``. The in-memory
        record is reset to its uncomputed state. Returns ``False`` if the
        scenario isn't in this session's index.
        """
        with self._lock:
            record = self._records.get(scenario_id)
            if record is None:
                return False
            tag = record.tag
        sub_tables = self._collect_sub_tables(scenario_id)
        existing_tables = set(sa.inspect(self._engine).get_table_names())
        with self._engine.begin() as conn:
            conn.execute(
                sa.text(
                    "DELETE FROM algomancy_kpi_measurements WHERE run_id IN "
                    "(SELECT run_id FROM algomancy_scenario_runs WHERE scenario_id = :sid)"
                ),
                {"sid": scenario_id},
            )
            conn.execute(
                scenario_runs_table.delete().where(
                    scenario_runs_table.c.scenario_id == scenario_id
                )
            )
            conn.execute(
                scenarios_table.update()
                .where(scenarios_table.c.id == scenario_id)
                .values(status=str(ScenarioStatus.CREATED))
            )
            self._delete_result_rows(conn, scenario_id, sub_tables, existing_tables)
        with self._lock:
            rec = self._records.get(scenario_id)
            if rec is not None:
                rec.status = ScenarioStatus.CREATED
                rec.result_available = False
                rec.run_started_at = None
                rec.run_finished_at = None
                rec.progress = 0.0
                rec.kpis = build_kpi_dicts(self._kpi_factory, list(rec.kpis.keys()))
        # The hydrated instance (if any) was already refresh()'d in memory by the
        # manager before this call, so it stays consistent in the cache.
        self._log(f"Refreshed scenario '{tag}'.")
        return True

    def list(self) -> List[Scenario]:
        """Eagerly hydrate every scenario and return the full objects.

        This is the GUI-compatibility path (``ScenarioManager.list_scenarios``).
        Under the default unbounded cache it is the same total work as the old
        eager startup, just deferred; under a bounded cache the objects are all
        constructed (and returned) even though not all stay resident. The API
        uses :meth:`list_records` instead to avoid hydration entirely.
        """
        with self._lock:
            ids = list(self._records.keys())
        result: List[Scenario] = []
        for scenario_id in ids:
            scenario = self.get_by_id(scenario_id)
            if scenario is not None:
                result.append(scenario)
        return result

    def list_ids(self) -> List[str]:
        with self._lock:
            return list(self._records.keys())

    def list_tags(self) -> List[str]:
        with self._lock:
            return list(self._tag_index.keys())

    def has_tag(self, tag: str) -> bool:
        with self._lock:
            return tag in self._tag_index

    def used_datasets(self) -> List[str]:
        with self._lock:
            return [r.input_data_key for r in self._records.values()]

    # ------------------------------------------------------------------
    # Metadata-only views (no hydration)
    # ------------------------------------------------------------------

    def list_records(self) -> List[ScenarioRecord]:
        with self._lock:
            return list(self._records.values())

    def get_record(self, scenario_id: str) -> Optional[ScenarioRecord]:
        with self._lock:
            return self._records.get(scenario_id)

    def status_of(self, scenario_id: str) -> Optional[Tuple[ScenarioStatus, float]]:
        """Return ``(status, progress)`` without hydrating.

        Prefers the live hydrated/pinned instance (accurate mid-run progress),
        falling back to the metadata record.
        """
        with self._lock:
            scenario = self._hydrated.get(scenario_id)
            if scenario is not None:
                return scenario.status, float(scenario.progress or 0.0)
            record = self._records.get(scenario_id)
            if record is None:
                return None
            return record.status, float(record.progress or 0.0)

    # ------------------------------------------------------------------
    # Hydration-cache pinning
    # ------------------------------------------------------------------

    def pin(self, scenario_id: str) -> None:
        """Keep ``scenario_id`` resident (outside the LRU limit) until unpinned."""
        with self._lock:
            self._pinned.add(scenario_id)

    def unpin(self, scenario_id: str) -> None:
        with self._lock:
            self._pinned.discard(scenario_id)
            self._evict_if_needed()

    # ------------------------------------------------------------------
    # Post-run persistence (called by ScenarioManager after processing)
    # ------------------------------------------------------------------

    def persist_run(self, scenario: Scenario) -> None:
        """Persist the outcome of a completed (or failed) scenario run.

        Inserts a row in ``algomancy_scenario_runs`` and one row per KPI in
        ``algomancy_kpi_measurements``, updates the scenario's status in
        ``algomancy_scenarios``, refreshes the in-memory metadata record, and
        unpins the scenario from the hydration cache.
        """
        run_id = str(uuid.uuid4())
        result_blob: Optional[str] = None
        error_text: Optional[str] = None
        sub_tables: List[str] = []

        # Drop any previous run's per-result rows for this scenario before
        # writing the new ones. Sub-tables that the new shape no longer uses
        # would otherwise leave stale rows behind.
        previous_sub_tables = self._collect_sub_tables(scenario.id)

        if scenario.status == ScenarioStatus.COMPLETE:
            if scenario.result is not None:
                try:
                    result_blob, sub_tables = self._persist_result_payload(
                        scenario.result, scenario.id, previous_sub_tables
                    )
                except (TypeError, ValueError) as exc:
                    self._log(
                        f"Could not serialise result for scenario '{scenario.tag}': {exc}"
                    )
        elif scenario.status == ScenarioStatus.FAILED:
            if isinstance(scenario.result, dict) and "error" in scenario.result:
                error_text = scenario.result["error"]

        now = datetime.now()
        with self._engine.begin() as conn:
            # Clear previous run rows for this scenario so per-result rows in
            # the shared tables remain in sync with run history.
            conn.execute(
                sa.text(
                    "DELETE FROM algomancy_kpi_measurements WHERE run_id IN "
                    "(SELECT run_id FROM algomancy_scenario_runs WHERE scenario_id = :sid)"
                ),
                {"sid": scenario.id},
            )
            conn.execute(
                scenario_runs_table.delete().where(
                    scenario_runs_table.c.scenario_id == scenario.id
                )
            )
            conn.execute(
                scenario_runs_table.insert().values(
                    run_id=run_id,
                    scenario_id=scenario.id,
                    started_at=now,
                    finished_at=now,
                    status=str(scenario.status),
                    result_blob=result_blob,
                    error=error_text,
                    result_sub_tables=json.dumps(sub_tables) if sub_tables else None,
                )
            )
            # Persist KPI measurements
            for kpi_name, kpi in scenario.kpis.items():
                threshold = None
                if kpi._threshold is not None:
                    threshold = kpi._threshold.value
                direction = str(kpi.better_when) if kpi.better_when else None
                conn.execute(
                    kpi_measurements_table.insert().values(
                        id=str(uuid.uuid4()),
                        run_id=run_id,
                        kpi_name=kpi_name,
                        value=kpi.value,
                        threshold=threshold,
                        direction=direction,
                        computed_at=now,
                    )
                )
            # Update scenario status
            conn.execute(
                scenarios_table.update()
                .where(scenarios_table.c.id == scenario.id)
                .values(status=str(scenario.status))
            )

        # Refresh metadata from the just-persisted run and release the pin.
        with self._lock:
            record = self._records.get(scenario.id)
            if record is not None:
                record.status = scenario.status
                record.run_started_at = now
                record.run_finished_at = now
                record.result_available = (
                    scenario.status == ScenarioStatus.COMPLETE
                    and scenario.result is not None
                )
                if scenario.status == ScenarioStatus.COMPLETE:
                    record.progress = 100.0
                record.kpis = {
                    k: v.to_dict() if hasattr(v, "to_dict") else v
                    for k, v in scenario.kpis.items()
                }
            self._pinned.discard(scenario.id)
            self._evict_if_needed()

    # ------------------------------------------------------------------
    # Internal helpers — hydration cache
    # ------------------------------------------------------------------

    def _get_key_lock(self, scenario_id: str) -> threading.Lock:
        with self._lock:
            lock = self._key_locks.get(scenario_id)
            if lock is None:
                lock = threading.Lock()
                self._key_locks[scenario_id] = lock
            return lock

    def _evict_if_needed(self) -> None:
        """Evict oldest non-pinned hydrated scenarios beyond the cache bound.

        Must be called while holding ``self._lock``. Pinned scenarios are never
        evicted and do not count toward the limit.
        """
        if self._cache_size is None:
            return
        while True:
            non_pinned = [k for k in self._hydrated if k not in self._pinned]
            if len(non_pinned) <= self._cache_size:
                return
            # Evict the oldest (front of the OrderedDict) non-pinned entry.
            for key in list(self._hydrated.keys()):
                if key not in self._pinned:
                    del self._hydrated[key]
                    break
            else:
                return

    # ------------------------------------------------------------------
    # Internal helpers — metadata loading
    # ------------------------------------------------------------------

    def _load_latest_runs(self, scenario_ids: List[str]) -> Dict[str, sa.Row]:
        """Return ``{scenario_id: latest_run_row}`` for the given scenarios."""
        if not scenario_ids:
            return {}
        with self._engine.connect() as conn:
            rows = conn.execute(
                scenario_runs_table.select().where(
                    scenario_runs_table.c.scenario_id.in_(scenario_ids)
                )
            ).fetchall()
        latest: Dict[str, sa.Row] = {}
        for row in rows:
            current = latest.get(row.scenario_id)
            if current is None or self._run_sort_key(row) > self._run_sort_key(current):
                latest[row.scenario_id] = row
        return latest

    @staticmethod
    def _run_sort_key(row) -> tuple:
        """Order runs by finished_at then started_at, tolerating NULLs."""
        finished = getattr(row, "finished_at", None) or datetime.min
        started = getattr(row, "started_at", None) or datetime.min
        return (finished, started)

    def _load_kpi_values(
        self, run_ids: List[str]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """Return ``{run_id: {kpi_name: value}}`` for the given runs."""
        if not run_ids:
            return {}
        with self._engine.connect() as conn:
            rows = conn.execute(
                kpi_measurements_table.select().where(
                    kpi_measurements_table.c.run_id.in_(run_ids)
                )
            ).fetchall()
        out: Dict[str, Dict[str, Optional[float]]] = {}
        for row in rows:
            out.setdefault(row.run_id, {})[row.kpi_name] = row.value
        return out

    def _build_record(
        self,
        row,
        latest_run: Optional[sa.Row],
        kpi_values: Dict[str, Optional[float]],
    ) -> ScenarioRecord:
        algo_params = self._parse_params(row.parameter_values)
        data_params = self._parse_params(getattr(row, "data_parameter_values", None))
        kpi_names = self._parse_kpi_names(row.kpi_names)
        status = ScenarioStatus(row.status)
        result_available = (
            status == ScenarioStatus.COMPLETE
            and latest_run is not None
            and latest_run.status == str(ScenarioStatus.COMPLETE)
        )
        return ScenarioRecord(
            id=row.id,
            tag=row.tag,
            input_data_key=row.input_data_key,
            algorithm_name=row.algorithm_name,
            algorithm_parameters=algo_params,
            data_parameters=data_params,
            status=status,
            progress=100.0 if status == ScenarioStatus.COMPLETE else 0.0,
            created_at=getattr(row, "created_at", None),
            run_started_at=getattr(latest_run, "started_at", None)
            if latest_run
            else None,
            run_finished_at=getattr(latest_run, "finished_at", None)
            if latest_run
            else None,
            result_available=result_available,
            kpis=build_kpi_dicts(self._kpi_factory, kpi_names, kpi_values),
        )

    @staticmethod
    def _parse_params(raw: Optional[str]) -> dict:
        """Parse a stored parameter blob to its inner ``{name: value}`` dict.

        ``serialize()`` stores ``{"name": ..., "parameters": {...}}``; return
        the inner ``parameters`` dict. Tolerates a bare dict or invalid JSON.
        """
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict) and "parameters" in parsed:
            inner = parsed["parameters"]
            return inner if isinstance(inner, dict) else {}
        return parsed if isinstance(parsed, dict) else {}

    def _parse_kpi_names(self, raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return list(self._kpi_factory.available_kpis)
        return [str(v) for v in value] if isinstance(value, list) else []

    # ------------------------------------------------------------------
    # Internal helpers — hydration
    # ------------------------------------------------------------------

    def _rehydrate_by_id(self, record: ScenarioRecord) -> Optional[Scenario]:
        """Reconstruct a full Scenario from its metadata record.

        Returns ``None`` (leaving the caller to skip caching) if the algorithm
        template is no longer registered, the algorithm cannot be rebuilt, or
        the input dataset is missing from the DataManager. Restores persisted
        KPI values and the latest run result for COMPLETE scenarios.
        """
        algo_name = record.algorithm_name
        if algo_name not in self._algo_factory.available_algorithms:
            self._log(
                f"Cannot hydrate scenario '{record.tag}': algorithm template "
                f"'{algo_name}' is no longer registered."
            )
            return None
        try:
            algorithm = self._algo_factory.create(
                algo_name, dict(record.algorithm_parameters)
            )
        except Exception as exc:
            self._log(
                f"Cannot hydrate scenario '{record.tag}': could not reconstruct "
                f"algorithm: {exc}"
            )
            return None

        kpis = self._kpi_factory.create(list(record.kpis.keys()))
        input_data = self._data_manager.get_data(record.input_data_key)
        if input_data is None:
            self._log(
                f"Cannot hydrate scenario '{record.tag}': dataset "
                f"'{record.input_data_key}' not found in DataManager."
            )
            return None

        data_params = input_data.initialize_data_parameters()
        if record.data_parameters:
            try:
                data_params.set_values(dict(record.data_parameters))
            except Exception:
                self._log(
                    f"Scenario '{record.tag}': stored data parameters could not be "
                    "applied; falling back to defaults."
                )

        scenario = Scenario(
            tag=record.tag,
            input_data=input_data,
            kpis=kpis,
            algorithm=algorithm,
            provided_id=record.id,
            data_params=data_params,
        )
        scenario.status = record.status

        if scenario.status == ScenarioStatus.COMPLETE:
            latest_result = self._load_latest_result(record.id, algorithm)
            if latest_result is not None:
                scenario.result = latest_result
            # Restore persisted KPI values (thresholds come from the templates).
            for key, kpi in kpis.items():
                persisted = record.kpis.get(key, {}).get("value")
                if persisted is not None:
                    kpi.value = persisted

        return scenario

    def _persist_result_payload(
        self, result, scenario_id: str, previous_sub_tables: List[str]
    ) -> tuple[Optional[str], List[str]]:
        """Persist a scenario result.

        Returns a ``(result_blob, sub_tables)`` tuple: ``result_blob`` is the
        JSON string to store on ``algomancy_scenario_runs.result_blob`` (or
        ``None`` for the per-table path) and ``sub_tables`` is the list of
        sub-table names this run wrote to the shared
        ``algomancy_result__<sub>`` tables (empty for the JSON path).

        Dispatch mirrors :class:`DatabaseDataManager._persist_datasource`: if
        the result implements :class:`SqlResultLayout`, each DataFrame is
        appended to a shared per-sub-table SQL table and the catalogue blob is
        ``None``. Otherwise the result is serialised via
        :meth:`BaseScenarioResult.to_json` and stored as a JSON string. A bare
        ``dict`` is serialised directly via :func:`json.dumps` to preserve
        backward compatibility with code paths that stashed raw dicts as
        ``Scenario.result`` (e.g. failure payloads).
        """
        if isinstance(result, SqlResultLayout):
            sql_tables = result.to_sql_tables()
            sub_table_names = list(sql_tables.keys())
            stale = set(previous_sub_tables) - set(sub_table_names)
            existing_tables = set(sa.inspect(self._engine).get_table_names())
            with self._engine.begin() as conn:
                self._delete_result_rows(
                    conn,
                    scenario_id,
                    list(stale) + sub_table_names,
                    existing_tables,
                )
                for sub_table, df in sql_tables.items():
                    self._append_to_shared_result_table(
                        conn, sub_table, scenario_id, df
                    )
            return None, sub_table_names
        if isinstance(result, BaseScenarioResult):
            return result.to_json(), []
        return json.dumps(result, default=str), []

    def _load_latest_result(
        self, scenario_id: str, algorithm: ALGORITHM
    ) -> Optional[BaseScenarioResult]:
        """Reconstruct the typed result of the most recent completed run, or None.

        Dispatch mirrors :class:`DatabaseDataManager._load_datasource_from_db`:
        if ``result_blob`` is present, use ``algorithm.result_class.from_json``;
        otherwise instantiate via ``result_class`` and load rows from the
        shared ``algomancy_result__<sub>`` tables via
        :class:`SqlResultLayout`.
        """
        with self._engine.connect() as conn:
            row = conn.execute(
                scenario_runs_table.select()
                .where(scenario_runs_table.c.scenario_id == scenario_id)
                .where(scenario_runs_table.c.status == str(ScenarioStatus.COMPLETE))
                .order_by(scenario_runs_table.c.finished_at.desc())
                .limit(1)
            ).fetchone()
        if row is None:
            return None
        result_cls = getattr(algorithm, "result_class", None)
        if result_cls is None:
            return None
        if row.result_blob is not None:
            try:
                return result_cls.from_json(row.result_blob)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                self._log(
                    f"Could not deserialise result for scenario '{scenario_id}': {exc}"
                )
                return None
        # SQL-table path: instantiate empty and load sub-tables
        try:
            inst = result_cls(data_id=scenario_id)
        except TypeError as exc:
            self._log(
                f"Could not instantiate result_class {result_cls.__name__} "
                f"with data_id only for scenario '{scenario_id}': {exc}. "
                "Override result_class to a type whose constructor accepts "
                "data_id alone, or persist via the JSON fallback."
            )
            return None
        if not isinstance(inst, SqlResultLayout):
            raise TypeError(
                f"Scenario '{scenario_id}' was persisted as per-table SQL but "
                f"result_class {result_cls.__name__} does not implement "
                "SqlResultLayout. Either restore the original result_class or "
                "delete and re-run the scenario."
            )
        sub_tables = _decode_sub_tables(getattr(row, "result_sub_tables", None)) or []
        inspector = sa.inspect(self._engine)
        existing = set(inspector.get_table_names())
        tables: Dict[str, pd.DataFrame] = {}
        for sub in sub_tables:
            table_name = _result_table_name(sub)
            if table_name not in existing:
                continue
            with self._engine.connect() as conn:
                df = pd.read_sql(
                    sa.text(
                        f'SELECT * FROM "{table_name}" '
                        f'WHERE "{SESSION_COL}" = :sid AND "{SCENARIO_COL}" = :scid'
                    ),
                    conn,
                    params={"sid": self._session_id, "scid": scenario_id},
                )
            tables[sub] = df.drop(columns=[SESSION_COL, SCENARIO_COL], errors="ignore")
        inst.from_sql_tables(tables)
        return inst

    def _collect_sub_tables(self, scenario_id: str) -> List[str]:
        """Return the union of result sub-table names recorded for any run."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                sa.text(
                    "SELECT result_sub_tables FROM algomancy_scenario_runs "
                    "WHERE scenario_id = :sid"
                ),
                {"sid": scenario_id},
            ).fetchall()
        names: List[str] = []
        seen = set()
        for row in rows:
            decoded = _decode_sub_tables(row[0]) or []
            for sub in decoded:
                if sub not in seen:
                    seen.add(sub)
                    names.append(sub)
        return names

    def _delete_result_rows(
        self,
        conn: sa.Connection,
        scenario_id: str,
        sub_tables: List[str],
        existing_tables: Optional[set[str]] = None,
    ) -> None:
        """Remove every row this (session, scenario) wrote to the shared tables.

        ``existing_tables`` should be pre-computed OUTSIDE the surrounding
        transaction when this is called inside ``engine.begin()``. Using
        ``sa.inspect`` inside the transaction borrows a connection and ROLLBACKs
        on release with SingletonThreadPool sqlite (default for
        ``sqlite:///:memory:``), undoing the pending DML.
        """
        if existing_tables is None:
            existing_tables = set(sa.inspect(self._engine).get_table_names())
        for sub in sub_tables:
            table_name = _result_table_name(sub)
            if table_name not in existing_tables:
                continue
            conn.execute(
                sa.text(
                    f'DELETE FROM "{table_name}" '
                    f'WHERE "{SESSION_COL}" = :sid AND "{SCENARIO_COL}" = :scid'
                ),
                {"sid": self._session_id, "scid": scenario_id},
            )

    def _append_to_shared_result_table(
        self,
        conn: sa.Connection,
        sub_table: str,
        scenario_id: str,
        df: pd.DataFrame,
    ) -> None:
        """Append ``df`` to the shared physical result table for ``sub_table``.

        Prepends the (session_id, scenario_id) discriminator columns. The
        physical table is created on first write with column types inferred
        by pandas — subsequent writes share that schema.
        """
        if SESSION_COL in df.columns or SCENARIO_COL in df.columns:
            raise ValueError(
                f"DataFrame for result sub-table '{sub_table}' must not contain "
                f"reserved columns {SESSION_COL!r} / {SCENARIO_COL!r}."
            )
        out = df.copy()
        out.insert(0, SCENARIO_COL, scenario_id)
        out.insert(0, SESSION_COL, self._session_id)
        out.to_sql(
            _result_table_name(sub_table),
            conn,
            if_exists="append",
            index=False,
        )

    def _log(self, msg: str) -> None:
        if self._logger:
            self._logger.log(msg)

    def _migrate_add_data_parameter_values_column(self) -> None:
        """Add ``data_parameter_values`` to an older schema's scenarios table.

        ``create_all(checkfirst=True)`` skips existing tables entirely, so it
        never adds new columns to a table that pre-dates this migration. We
        ALTER in the column once, idempotently, so older SQLite/Postgres
        databases keep loading.
        """
        inspector = sa.inspect(self._engine)
        if not inspector.has_table(scenarios_table.name):
            return
        existing_columns = {
            col["name"] for col in inspector.get_columns(scenarios_table.name)
        }
        if "data_parameter_values" in existing_columns:
            return
        with self._engine.begin() as conn:
            conn.execute(
                sa.text(
                    f"ALTER TABLE {scenarios_table.name} "
                    "ADD COLUMN data_parameter_values TEXT"
                )
            )


def _decode_sub_tables(raw: Optional[str]) -> Optional[List[str]]:
    if raw is None:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if isinstance(value, list):
        return [str(v) for v in value]
    return None
