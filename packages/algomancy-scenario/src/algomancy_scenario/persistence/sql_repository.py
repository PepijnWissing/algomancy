"""SQL-backed ScenarioRepository implementation.

Persists scenario definitions, run history, and KPI measurements to a
SQLAlchemy-compatible database (SQLite or Postgres). All scenarios for a
session are loaded into memory at ``startup()`` and kept in sync with the DB on
every mutation.

The repository reconstructs ``Scenario`` objects on load by matching stored
``algorithm_name`` and ``kpi_names`` against the in-process template
dictionaries. If a referenced template no longer exists, the scenario is
skipped and a warning is logged rather than silently dropped.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Type

import sqlalchemy as sa
from algomancy_utils.logger import Logger

from ..algorithmfactory import AlgorithmFactory
from ..basealgorithm import ALGORITHM
from ..keyperformanceindicator import BASE_KPI
from ..kpifactory import KpiFactory
from ..scenario import Scenario, ScenarioStatus
from .models import (
    metadata as _scenario_metadata,
    scenarios_table,
    scenario_runs_table,
    kpi_measurements_table,
)


class SqlScenarioRepository:
    """ScenarioRepository backed by a SQL database.

    Args:
        engine: A SQLAlchemy ``Engine`` for the target database.
        session_id: Logical session name that scopes all reads/writes.
        algorithms: Algorithm class registry (same as ``CoreConfig.algorithms``).
        kpis: KPI class registry (same as ``CoreConfig.kpis``).
        data_manager: DataManager used to load ``input_data`` when rehydrating
            scenarios from the database.
        logger: Optional logger instance.
    """

    def __init__(
        self,
        engine: sa.Engine,
        session_id: str,
        algorithms: Dict[str, Type[ALGORITHM]],
        kpis: Dict[str, Type[BASE_KPI]],
        data_manager,
        logger: Logger | None = None,
    ) -> None:
        self._engine = engine
        self._session_id = session_id
        self._algo_factory = AlgorithmFactory(algorithms, logger)
        self._kpi_factory = KpiFactory(kpis)
        self._data_manager = data_manager
        self._logger = logger
        # In-memory cache (populated at startup, kept in sync)
        self._scenarios: Dict[str, Scenario] = {}
        self._tag_index: Dict[str, str] = {}  # tag → id

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def startup(self) -> None:
        """Initialise DB schema and load all persisted scenarios into memory."""
        _scenario_metadata.create_all(self._engine, checkfirst=True)
        self._migrate_add_data_parameter_values_column()
        with self._engine.connect() as conn:
            rows = conn.execute(
                scenarios_table.select().where(
                    scenarios_table.c.session_id == self._session_id
                )
            ).fetchall()
        for row in rows:
            scenario = self._rehydrate(row)
            if scenario is not None:
                self._scenarios[scenario.id] = scenario
                self._tag_index[scenario.tag] = scenario.id
        self._log(
            f"SqlScenarioRepository startup for session '{self._session_id}': "
            f"loaded {len(self._scenarios)} scenarios."
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
                    created_at=datetime.now(),
                )
            )
        self._scenarios[scenario.id] = scenario
        self._tag_index[scenario.tag] = scenario.id
        self._log(f"Registered scenario '{scenario.tag}'.")

    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        return self._scenarios.get(scenario_id)

    def get_by_tag(self, tag: str) -> Optional[Scenario]:
        scenario_id = self._tag_index.get(tag)
        return self.get_by_id(scenario_id) if scenario_id else None

    def delete(self, scenario_id: str) -> bool:
        if scenario_id not in self._scenarios:
            return False
        tag = self._scenarios[scenario_id].tag
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
        del self._scenarios[scenario_id]
        if tag in self._tag_index:
            del self._tag_index[tag]
        self._log(f"Deleted scenario '{tag}'.")
        return True

    def list(self) -> List[Scenario]:
        return list(self._scenarios.values())

    def list_ids(self) -> List[str]:
        return list(self._scenarios.keys())

    def list_tags(self) -> List[str]:
        return list(self._tag_index.keys())

    def has_tag(self, tag: str) -> bool:
        return tag in self._tag_index

    def used_datasets(self) -> List[str]:
        return [s.input_data_key for s in self._scenarios.values()]

    # ------------------------------------------------------------------
    # Post-run persistence (called by ScenarioManager after processing)
    # ------------------------------------------------------------------

    def persist_run(self, scenario: Scenario) -> None:
        """Persist the outcome of a completed (or failed) scenario run.

        Inserts a row in ``algomancy_scenario_runs`` and one row per KPI in
        ``algomancy_kpi_measurements``, then updates the scenario's status in
        ``algomancy_scenarios``.
        """
        run_id = str(uuid.uuid4())
        result_blob: Optional[str] = None
        error_text: Optional[str] = None

        if scenario.status == ScenarioStatus.COMPLETE:
            if scenario.result is not None:
                try:
                    raw = (
                        scenario.result.to_dict()
                        if hasattr(scenario.result, "to_dict")
                        else scenario.result
                    )
                    result_blob = json.dumps(raw)
                except (TypeError, ValueError) as exc:
                    self._log(
                        f"Could not serialise result for scenario '{scenario.tag}': {exc}"
                    )
        elif scenario.status == ScenarioStatus.FAILED:
            if isinstance(scenario.result, dict) and "error" in scenario.result:
                error_text = scenario.result["error"]

        now = datetime.now()
        with self._engine.begin() as conn:
            conn.execute(
                scenario_runs_table.insert().values(
                    run_id=run_id,
                    scenario_id=scenario.id,
                    started_at=now,
                    finished_at=now,
                    status=str(scenario.status),
                    result_blob=result_blob,
                    error=error_text,
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rehydrate(self, row) -> Optional[Scenario]:
        """Reconstruct a Scenario from a DB row. Returns None on failure."""
        algo_name = row.algorithm_name
        if algo_name not in self._algo_factory.available_algorithms:
            self._log(
                f"Skipping scenario '{row.tag}': algorithm template '{algo_name}' "
                "is no longer registered."
            )
            return None

        try:
            params_raw = (
                json.loads(row.parameter_values) if row.parameter_values else {}
            )
            # serialize() stores {"name": ..., "parameters": {...}}; AlgorithmFactory.create
            # expects the inner "parameters" dict directly.
            if isinstance(params_raw, dict) and "parameters" in params_raw:
                params_dict = params_raw["parameters"]
            else:
                params_dict = params_raw if isinstance(params_raw, dict) else {}
        except json.JSONDecodeError:
            params_dict = {}

        try:
            kpi_names = json.loads(row.kpi_names) if row.kpi_names else []
        except json.JSONDecodeError:
            kpi_names = list(self._kpi_factory.available_kpis)

        try:
            algorithm = self._algo_factory.create(algo_name, params_dict)
        except Exception as exc:
            self._log(
                f"Skipping scenario '{row.tag}': could not reconstruct algorithm: {exc}"
            )
            return None

        kpis = self._kpi_factory.create(kpi_names)
        input_data = self._data_manager.get_data(row.input_data_key)

        if input_data is None:
            self._log(
                f"Skipping scenario '{row.tag}': dataset '{row.input_data_key}' "
                "not found in DataManager."
            )
            return None

        data_params = input_data.initialize_data_parameters()
        raw_data_params = getattr(row, "data_parameter_values", None)
        if raw_data_params:
            try:
                parsed = json.loads(raw_data_params)
                if isinstance(parsed, dict) and "parameters" in parsed:
                    data_params.set_values(parsed["parameters"])
                elif isinstance(parsed, dict):
                    data_params.set_values(parsed)
            except json.JSONDecodeError:
                self._log(
                    f"Scenario '{row.tag}': data_parameter_values is not valid JSON; "
                    "falling back to defaults."
                )

        scenario = Scenario(
            tag=row.tag,
            input_data=input_data,
            kpis=kpis,
            algorithm=algorithm,
            provided_id=row.id,
            data_params=data_params,
        )
        scenario.status = ScenarioStatus(row.status)

        # Restore the latest run result for completed scenarios
        if scenario.status == ScenarioStatus.COMPLETE:
            latest_result = self._load_latest_result(row.id)
            if latest_result is not None:
                scenario.result = latest_result

        return scenario

    def _load_latest_result(self, scenario_id: str):
        """Return the parsed result blob from the most recent run, or None."""
        with self._engine.connect() as conn:
            row = conn.execute(
                scenario_runs_table.select()
                .where(scenario_runs_table.c.scenario_id == scenario_id)
                .where(scenario_runs_table.c.status == str(ScenarioStatus.COMPLETE))
                .order_by(scenario_runs_table.c.finished_at.desc())
                .limit(1)
            ).fetchone()
        if row is None or row.result_blob is None:
            return None
        try:
            return json.loads(row.result_blob)
        except json.JSONDecodeError:
            return None

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
