"""Tests for the dual-path ScenarioResult persistence in SqlScenarioRepository.

Mirrors :mod:`algomancy_data.database.database_manager`'s dual-path strategy:

* Results that implement :class:`SqlResultLayout` write each sub-table to a
  real SQL table; ``result_blob`` is NULL.
* Results that do not implement the protocol fall back to a JSON blob via the
  abstract ``to_json`` / ``from_json`` contract on
  :class:`BaseScenarioResult`.

Both paths must round-trip through a repository restart.
"""

from __future__ import annotations

import json
import importlib.util
import pathlib

import pytest

pytest.importorskip("sqlalchemy", reason="requires algomancy-scenario[database]")

import pandas as pd
import sqlalchemy as sa

from algomancy_data import DataSource, DataClassification
from algomancy_data.database.database_manager import DatabaseDataManager
from algomancy_data.database.models import metadata as data_meta
from algomancy_scenario import (
    BaseAlgorithm,
    Scenario,
    ScenarioResult,
    ScenarioStatus,
)
from algomancy_scenario.persistence.models import metadata as scenario_meta
from algomancy_scenario.persistence.sql_repository import (
    SqlScenarioRepository,
    _result_table_name,
    _result_table_prefix,
)

# Load shared fixtures from conftest
_CONFTEST = pathlib.Path(__file__).resolve().parent / "conftest.py"
_spec = importlib.util.spec_from_file_location("_scenario_test_shared", _CONFTEST)
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)

ExampleETLFactory = _shared.ExampleETLFactory
example_schemas = _shared.example_schemas
DelayKPI = _shared.DelayKPI
SlowAlgorithm = _shared.SlowAlgorithm
SlowAlgorithmParams = _shared.SlowAlgorithmParams


# ------------------------------------------------------------------ #
# Custom result implementations used by the tests
# ------------------------------------------------------------------ #


class TabularResult(ScenarioResult):
    """A result with two DataFrames + scalar metadata — picks the SQL-table path."""

    def __init__(
        self,
        data_id: str,
        rows: pd.DataFrame | None = None,
        summary: pd.DataFrame | None = None,
        note: str = "",
    ) -> None:
        super().__init__(data_id)
        self.rows = rows if rows is not None else pd.DataFrame()
        self.summary = summary if summary is not None else pd.DataFrame()
        self.note = note

    def to_dict(self) -> dict:
        return {"data_id": self.data_id, "note": self.note}

    def to_json(self) -> str:
        return json.dumps(
            {
                "data_id": self.data_id,
                "note": self.note,
                "rows": self.rows.to_dict(orient="records"),
                "summary": self.summary.to_dict(orient="records"),
            }
        )

    @classmethod
    def from_json(cls, json_string: str) -> "TabularResult":
        payload = json.loads(json_string)
        return cls(
            data_id=payload["data_id"],
            rows=pd.DataFrame(payload.get("rows", [])),
            summary=pd.DataFrame(payload.get("summary", [])),
            note=payload.get("note", ""),
        )

    def to_sql_tables(self) -> dict[str, pd.DataFrame]:
        meta = pd.DataFrame([{"data_id": self.data_id, "note": self.note}])
        return {"rows": self.rows, "summary": self.summary, "_meta": meta}

    def from_sql_tables(self, tables: dict[str, pd.DataFrame]) -> None:
        self.rows = tables.get("rows", pd.DataFrame())
        self.summary = tables.get("summary", pd.DataFrame())
        meta = tables.get("_meta")
        if meta is not None and not meta.empty:
            row = meta.iloc[0]
            self.data_id = str(row["data_id"])
            self.note = str(row["note"])


class JsonOnlyResult(ScenarioResult):
    """A result that only implements the JSON-blob path."""

    def __init__(self, data_id: str, payload: dict | None = None) -> None:
        super().__init__(data_id)
        self.payload = payload or {}

    def to_dict(self) -> dict:
        return {"data_id": self.data_id, "payload": self.payload}

    def to_json(self) -> str:
        return json.dumps({"data_id": self.data_id, "payload": self.payload})

    @classmethod
    def from_json(cls, json_string: str) -> "JsonOnlyResult":
        data = json.loads(json_string)
        return cls(data_id=data["data_id"], payload=data.get("payload", {}))


class TabularAlgorithm(BaseAlgorithm):
    """Algorithm whose run() returns a TabularResult."""

    result_class = TabularResult

    def __init__(self, params: SlowAlgorithmParams) -> None:
        super().__init__(name="Tabular", params=params)

    @staticmethod
    def initialize_parameters() -> SlowAlgorithmParams:
        return SlowAlgorithmParams()

    def run(self, data) -> TabularResult:
        rows = pd.DataFrame({"item": ["a", "b"], "value": [1, 2]})
        summary = pd.DataFrame([{"total": 3, "count": 2}])
        return TabularResult(data_id=data.id, rows=rows, summary=summary, note="hello")


class JsonAlgorithm(BaseAlgorithm):
    """Algorithm whose run() returns a JsonOnlyResult."""

    result_class = JsonOnlyResult

    def __init__(self, params: SlowAlgorithmParams) -> None:
        super().__init__(name="Json", params=params)

    @staticmethod
    def initialize_parameters() -> SlowAlgorithmParams:
        return SlowAlgorithmParams()

    def run(self, data) -> JsonOnlyResult:
        return JsonOnlyResult(data_id=data.id, payload={"hello": "world"})


algorithms_local = {
    "Tabular": TabularAlgorithm,
    "Json": JsonAlgorithm,
    "Slow": SlowAlgorithm,
}
kpis_local = {"Delay": DelayKPI}


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def engine():
    return sa.create_engine("sqlite:///:memory:")


@pytest.fixture
def dm(engine):
    data_meta.create_all(engine, checkfirst=True)
    manager = DatabaseDataManager(
        etl_factory=ExampleETLFactory,
        schemas=example_schemas,
        engine=engine,
        session_id="test_session",
        data_object_type=DataSource,
    )
    manager.startup()
    ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="test_data")
    ds.add_table("item", pd.DataFrame({"id": ["a", "b"], "value": [1, 2]}))
    manager.add_data_source(ds)
    return manager


@pytest.fixture
def repo(engine, dm):
    scenario_meta.create_all(engine, checkfirst=True)
    r = SqlScenarioRepository(
        engine=engine,
        session_id="test_session",
        algorithms=algorithms_local,
        kpis=kpis_local,
        data_manager=dm,
    )
    r.startup()
    return r


def _make_scenario(dm, algorithm_cls, tag: str) -> Scenario:
    algo = algorithm_cls(SlowAlgorithmParams())
    kpis = {"Delay": DelayKPI()}
    return Scenario(
        tag=tag, input_data=dm.get_data("test_data"), kpis=kpis, algorithm=algo
    )


def _fresh_repo(engine, dm):
    r = SqlScenarioRepository(
        engine=engine,
        session_id="test_session",
        algorithms=algorithms_local,
        kpis=kpis_local,
        data_manager=dm,
    )
    r.startup()
    return r


# ------------------------------------------------------------------ #
# Tests — JSON-blob path
# ------------------------------------------------------------------ #


def test_json_blob_path_persists_and_rehydrates(engine, repo, dm):
    s = _make_scenario(dm, JsonAlgorithm, tag="json_run")
    repo.add(s)
    s.result = s._algorithm.run(s._input_data)
    s.status = ScenarioStatus.COMPLETE
    repo.persist_run(s)

    # Verify the row has a non-null result_blob and no result__ tables exist
    with engine.connect() as conn:
        row = conn.execute(
            sa.text(
                "SELECT result_blob FROM algomancy_scenario_runs "
                "WHERE scenario_id = :sid"
            ),
            {"sid": s.id},
        ).fetchone()
    assert row is not None
    assert row.result_blob is not None
    inspector = sa.inspect(engine)
    prefix = _result_table_prefix("test_session", s.id)
    assert not any(t.startswith(prefix) for t in inspector.get_table_names())

    # Rehydrate
    repo2 = _fresh_repo(engine, dm)
    loaded = repo2.get_by_tag("json_run")
    assert loaded is not None
    assert isinstance(loaded.result, JsonOnlyResult)
    assert loaded.result.payload == {"hello": "world"}


# ------------------------------------------------------------------ #
# Tests — SqlResultLayout path
# ------------------------------------------------------------------ #


def test_sql_layout_path_writes_subtables_and_clears_blob(engine, repo, dm):
    s = _make_scenario(dm, TabularAlgorithm, tag="tab_run")
    repo.add(s)
    s.result = s._algorithm.run(s._input_data)
    s.status = ScenarioStatus.COMPLETE
    repo.persist_run(s)

    # result_blob should be NULL
    with engine.connect() as conn:
        row = conn.execute(
            sa.text(
                "SELECT result_blob FROM algomancy_scenario_runs "
                "WHERE scenario_id = :sid"
            ),
            {"sid": s.id},
        ).fetchone()
    assert row is not None
    assert row.result_blob is None

    # Real sub-tables exist
    inspector = sa.inspect(engine)
    expected_tables = {
        _result_table_name("test_session", s.id, "rows"),
        _result_table_name("test_session", s.id, "summary"),
        _result_table_name("test_session", s.id, "_meta"),
    }
    actual = set(inspector.get_table_names())
    assert expected_tables.issubset(actual)


def test_sql_layout_path_roundtrips_typed_result(engine, repo, dm):
    s = _make_scenario(dm, TabularAlgorithm, tag="tab_roundtrip")
    repo.add(s)
    s.result = s._algorithm.run(s._input_data)
    s.status = ScenarioStatus.COMPLETE
    repo.persist_run(s)

    repo2 = _fresh_repo(engine, dm)
    loaded = repo2.get_by_tag("tab_roundtrip")
    assert loaded is not None
    assert isinstance(loaded.result, TabularResult)
    assert loaded.result.note == "hello"
    pd.testing.assert_frame_equal(
        loaded.result.rows.reset_index(drop=True),
        pd.DataFrame({"item": ["a", "b"], "value": [1, 2]}),
    )
    pd.testing.assert_frame_equal(
        loaded.result.summary.reset_index(drop=True),
        pd.DataFrame([{"total": 3, "count": 2}]),
    )


def test_delete_drops_result_subtables(engine, repo, dm):
    s = _make_scenario(dm, TabularAlgorithm, tag="tab_delete")
    repo.add(s)
    s.result = s._algorithm.run(s._input_data)
    s.status = ScenarioStatus.COMPLETE
    repo.persist_run(s)

    inspector = sa.inspect(engine)
    prefix = _result_table_prefix("test_session", s.id)
    assert any(t.startswith(prefix) for t in inspector.get_table_names())

    assert repo.delete(s.id) is True

    inspector = sa.inspect(engine)
    assert not any(t.startswith(prefix) for t in inspector.get_table_names())


def test_re_persist_drops_stale_subtables(engine, repo, dm):
    """A second persist_run should not leave behind sub-tables that the new
    result schema no longer produces."""
    s = _make_scenario(dm, TabularAlgorithm, tag="tab_repersist")
    repo.add(s)
    s.result = s._algorithm.run(s._input_data)
    s.status = ScenarioStatus.COMPLETE
    repo.persist_run(s)

    # Simulate a result with a different sub-table set
    s.result = TabularResult(
        data_id=s._input_data.id,
        rows=pd.DataFrame({"item": ["c"], "value": [9]}),
        summary=pd.DataFrame([{"total": 9, "count": 1}]),
        note="rev2",
    )
    repo.persist_run(s)

    inspector = sa.inspect(engine)
    prefix = _result_table_prefix("test_session", s.id)
    present = {t for t in inspector.get_table_names() if t.startswith(prefix)}
    # Only the three sub-tables defined by TabularResult, no leftovers
    expected = {
        _result_table_name("test_session", s.id, "rows"),
        _result_table_name("test_session", s.id, "summary"),
        _result_table_name("test_session", s.id, "_meta"),
    }
    assert present == expected


def test_dict_result_falls_back_to_json_dump(engine, repo, dm):
    """Legacy code paths that set scenario.result to a bare dict must still
    persist (json.dumps) — the contract added in this PR must not break this.
    """
    s = _make_scenario(dm, JsonAlgorithm, tag="dict_legacy")
    repo.add(s)
    s.status = ScenarioStatus.COMPLETE
    s.result = {"raw": "payload"}
    repo.persist_run(s)

    with engine.connect() as conn:
        row = conn.execute(
            sa.text(
                "SELECT result_blob FROM algomancy_scenario_runs "
                "WHERE scenario_id = :sid"
            ),
            {"sid": s.id},
        ).fetchone()
    assert row.result_blob is not None
    assert json.loads(row.result_blob) == {"raw": "payload"}
