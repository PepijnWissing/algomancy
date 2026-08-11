"""Tests for lazy manager startup and bounded hydration in SqlScenarioRepository.

Covers:
* metadata-only startup (no dataset / result reads until first ``get_by_id``);
* lazy hydration + bounded LRU eviction with pinning;
* persisted-KPI-value restore on hydration (the previously-missing path);
* failed hydration left uncached so a later request can retry.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

pytest.importorskip("sqlalchemy", reason="requires algomancy-scenario[database]")

import pandas as pd
import sqlalchemy as sa

from algomancy_data import DataSource, DataClassification
from algomancy_data.database.database_manager import DatabaseDataManager
from algomancy_data.database.models import metadata as data_meta
from algomancy_scenario import Scenario, ScenarioStatus, ScenarioResult
from algomancy_scenario.persistence.models import metadata as scenario_meta
from algomancy_scenario.persistence.sql_repository import SqlScenarioRepository
from algomancy_utils.unit import Measurement

_CONFTEST = pathlib.Path(__file__).resolve().parent / "conftest.py"
_spec = importlib.util.spec_from_file_location("_scenario_test_shared", _CONFTEST)
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)

ExampleETLFactory = _shared.ExampleETLFactory
example_schemas = _shared.example_schemas
algorithms = _shared.algorithms
kpis = _shared.kpis
SlowAlgorithm = _shared.SlowAlgorithm
SlowAlgorithmParams = _shared.SlowAlgorithmParams
DelayKPI = _shared.DelayKPI


# ------------------------------------------------------------------ #
# Fixtures / helpers
# ------------------------------------------------------------------ #


@pytest.fixture
def engine():
    # A file-independent shared in-memory DB so multiple connections/managers
    # created in one test see the same schema and rows.
    return sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=sa.pool.StaticPool,
    )


def _make_dm(engine, session_id="test_session", cache_size=None):
    data_meta.create_all(engine, checkfirst=True)
    scenario_meta.create_all(engine, checkfirst=True)
    dm = DatabaseDataManager(
        etl_factory=ExampleETLFactory,
        schemas=example_schemas,
        engine=engine,
        session_id=session_id,
        data_object_type=DataSource,
        datasource_cache_size=cache_size,
    )
    dm.startup()
    return dm


def _add_dataset(dm, name="test_data"):
    ds = DataSource(ds_type=DataClassification.MASTER_DATA, name=name)
    ds.add_table("item", pd.DataFrame({"id": ["a", "b"], "value": [1, 2]}))
    dm.add_data_source(ds)


def _make_repo(
    engine, dm, session_id="test_session", cache_size=None, eager_startup=False
):
    repo = SqlScenarioRepository(
        engine=engine,
        session_id=session_id,
        algorithms=algorithms,
        kpis=kpis,
        data_manager=dm,
        hydrated_cache_size=cache_size,
        eager_startup=eager_startup,
    )
    repo.startup()
    return repo


def _make_scenario(dm, tag, dataset="test_data") -> Scenario:
    return Scenario(
        tag=tag,
        input_data=dm.get_data(dataset),
        kpis={"Delay": DelayKPI()},
        algorithm=SlowAlgorithm(SlowAlgorithmParams()),
    )


def _persist_completed(repo, dm, tag, delay_value=500.0) -> str:
    """Add a scenario, mark it COMPLETE with a KPI value, and persist the run."""
    s = _make_scenario(dm, tag)
    repo.add(s)
    s.status = ScenarioStatus.COMPLETE
    s.result = ScenarioResult(data_id=dm.get_data("test_data").id)
    s.kpis["Delay"].value = delay_value
    repo.persist_run(s)
    return s.id


# ------------------------------------------------------------------ #
# Metadata-only startup
# ------------------------------------------------------------------ #


def test_startup_loads_metadata_only(engine):
    dm = _make_dm(engine)
    _add_dataset(dm)
    repo = _make_repo(engine, dm)
    _persist_completed(repo, dm, "done")

    # Fresh managers over the same DB — simulate a cold restart.
    dm2 = _make_dm(engine)
    repo2 = _make_repo(engine, dm2)

    # Metadata is present…
    assert len(repo2.list_records()) == 1
    assert repo2.has_tag("done")
    # …but nothing is hydrated and no dataset was materialised.
    assert len(repo2._hydrated) == 0
    assert len(dm2._data) == 0

    # First access hydrates lazily and pulls the dataset in.
    scenario = repo2.get_by_id(repo2.list_ids()[0])
    assert scenario is not None
    assert len(repo2._hydrated) == 1
    assert "test_data" in dm2._data


def test_persisted_kpi_values_restored_on_hydration(engine):
    dm = _make_dm(engine)
    _add_dataset(dm)
    repo = _make_repo(engine, dm)
    sid = _persist_completed(repo, dm, "with_kpi", delay_value=777.0)

    dm2 = _make_dm(engine)
    repo2 = _make_repo(engine, dm2)

    # Metadata record already carries the persisted value.
    record = repo2.get_record(sid)
    assert record.kpis["Delay"]["value"] == 777.0
    assert record.result_available is True

    # A freshly-created KPI would read the uncomputed sentinel; the hydrated
    # scenario must instead expose the restored value.
    assert DelayKPI().value == Measurement.INITIAL_VALUE
    scenario = repo2.get_by_id(sid)
    assert scenario.status == ScenarioStatus.COMPLETE
    assert scenario.kpis["Delay"].value == 777.0


def test_eager_startup_hydrates_everything(engine):
    dm = _make_dm(engine)
    _add_dataset(dm)
    repo = _make_repo(engine, dm)
    _persist_completed(repo, dm, "a")
    _persist_completed(repo, dm, "b")

    # Cold restart with eager_startup=True → all scenarios hydrated at startup,
    # reproducing the pre-0.10 "everything in memory" behaviour.
    dm2 = _make_dm(engine)
    repo2 = _make_repo(engine, dm2, eager_startup=True)

    assert len(repo2._hydrated) == 2
    assert len(dm2._data) == 1  # the shared dataset was materialised
    # KPI values are already restored on the resident objects.
    for scenario in repo2._hydrated.values():
        assert scenario.kpis["Delay"].value == 500.0


# ------------------------------------------------------------------ #
# Bounded LRU + pinning
# ------------------------------------------------------------------ #


def test_lru_eviction_bounds_cache(engine):
    dm = _make_dm(engine, cache_size=2)
    _add_dataset(dm)
    repo = _make_repo(engine, dm, cache_size=2)

    ids = [_persist_completed(repo, dm, f"s{i}") for i in range(4)]

    # add() caches the live instance; with a bound of 2 the oldest non-pinned
    # entries are evicted, so at most 2 stay resident.
    assert len(repo._hydrated) <= 2

    # Accessing an evicted scenario rehydrates it without exceeding the bound.
    for sid in ids:
        assert repo.get_by_id(sid) is not None
        assert len(repo._hydrated) <= 2


def test_pinned_scenario_survives_eviction(engine):
    dm = _make_dm(engine, cache_size=1)
    _add_dataset(dm)
    repo = _make_repo(engine, dm, cache_size=1)

    pinned_id = _persist_completed(repo, dm, "pinned")
    repo.pin(pinned_id)

    # Fill the cache with more scenarios than the bound allows.
    for i in range(3):
        _persist_completed(repo, dm, f"other{i}")

    # The pinned scenario is kept resident, outside the size limit.
    assert pinned_id in repo._hydrated

    repo.unpin(pinned_id)
    # After unpinning it becomes evictable again.
    for i in range(3):
        repo.get_by_id(repo.list_ids()[i])
    assert len([k for k in repo._hydrated if k not in repo._pinned]) <= 1


# ------------------------------------------------------------------ #
# Failed hydration
# ------------------------------------------------------------------ #


def test_failed_hydration_is_not_cached_and_retries(engine):
    dm = _make_dm(engine)
    _add_dataset(dm)
    repo = _make_repo(engine, dm)
    sid = _persist_completed(repo, dm, "orphan")

    # Drop the dataset and evict the live instance so hydration must reload it.
    dm.delete_data("test_data")
    repo._hydrated.clear()

    # Dataset gone → hydration fails, returns None, and is NOT cached.
    assert repo.get_by_id(sid) is None
    assert sid not in repo._hydrated

    # Restore the dataset → a later request succeeds (retry works).
    _add_dataset(dm)
    scenario = repo.get_by_id(sid)
    assert scenario is not None
    assert sid in repo._hydrated
