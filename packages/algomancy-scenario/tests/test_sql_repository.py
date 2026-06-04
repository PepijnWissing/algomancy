"""Tests for SqlScenarioRepository — scenario persistence via SQLite.

The test suite runs the same contracts as ScenarioRegistry (in-memory) but
against a SqlScenarioRepository backed by an in-memory SQLite database.
"""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy", reason="requires algomancy-scenario[database]")

import importlib.util
import pathlib

import pytest
import pandas as pd
import sqlalchemy as sa

from algomancy_data import DataSource, DataClassification
from algomancy_data.database.database_manager import DatabaseDataManager
from algomancy_scenario.persistence.sql_repository import SqlScenarioRepository
from algomancy_scenario.persistence.models import metadata as scenario_meta
from algomancy_data.database.models import metadata as data_meta
from algomancy_scenario import (
    Scenario,
    ScenarioStatus,
)

# Load shared test fixtures from conftest.py in the same directory
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
# Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def engine():
    return sa.create_engine("sqlite:///:memory:")


@pytest.fixture
def dm(engine):
    """Minimal DatabaseDataManager with one in-memory DataSource pre-loaded."""
    data_meta.create_all(engine, checkfirst=True)
    manager = DatabaseDataManager(
        etl_factory=ExampleETLFactory,
        schemas=example_schemas,
        engine=engine,
        session_id="test_session",
        data_object_type=DataSource,
    )
    manager.startup()

    # Inject a simple DataSource so scenarios have something to reference
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
        algorithms=algorithms,
        kpis=kpis,
        data_manager=dm,
    )
    r.startup()
    return r


def _make_scenario(dm, tag: str = "my_scenario") -> Scenario:
    """Helper: create a minimal Scenario without going through ScenarioFactory."""
    algo = SlowAlgorithm(SlowAlgorithmParams())
    kpis = {"Delay": DelayKPI()}
    input_data = dm.get_data("test_data")
    return Scenario(tag=tag, input_data=input_data, kpis=kpis, algorithm=algo)


# ------------------------------------------------------------------ #
# Tests
# ------------------------------------------------------------------ #


class TestSqlScenarioRepositoryCRUD:
    def test_add_and_get_by_id(self, repo, dm):
        s = _make_scenario(dm)
        repo.add(s)
        loaded = repo.get_by_id(s.id)
        assert loaded is s  # in-memory cache returns same object

    def test_add_and_get_by_tag(self, repo, dm):
        s = _make_scenario(dm, tag="unique_tag")
        repo.add(s)
        loaded = repo.get_by_tag("unique_tag")
        assert loaded is not None
        assert loaded.id == s.id

    def test_has_tag(self, repo, dm):
        s = _make_scenario(dm, tag="tagged")
        assert not repo.has_tag("tagged")
        repo.add(s)
        assert repo.has_tag("tagged")

    def test_delete(self, repo, dm):
        s = _make_scenario(dm, tag="to_delete")
        repo.add(s)
        deleted = repo.delete(s.id)
        assert deleted is True
        assert repo.get_by_id(s.id) is None
        assert not repo.has_tag("to_delete")

    def test_delete_nonexistent_returns_false(self, repo):
        assert repo.delete("nonexistent-id") is False

    def test_list(self, repo, dm):
        s1 = _make_scenario(dm, "s1")
        s2 = _make_scenario(dm, "s2")
        repo.add(s1)
        repo.add(s2)
        ids = repo.list_ids()
        assert s1.id in ids
        assert s2.id in ids

    def test_used_datasets(self, repo, dm):
        s = _make_scenario(dm)
        repo.add(s)
        assert "test_data" in repo.used_datasets()


class TestSqlScenarioRepositoryPersistence:
    def test_rehydration_after_restart(self, engine, dm):
        """Scenarios added in one repo instance should appear after a cold startup."""
        repo1 = SqlScenarioRepository(
            engine=engine,
            session_id="test_session",
            algorithms=algorithms,
            kpis=kpis,
            data_manager=dm,
        )
        repo1.startup()
        s = _make_scenario(dm, tag="persisted_scenario")
        repo1.add(s)

        # "Restart": create a fresh repo pointing at the same engine
        repo2 = SqlScenarioRepository(
            engine=engine,
            session_id="test_session",
            algorithms=algorithms,
            kpis=kpis,
            data_manager=dm,
        )
        repo2.startup()

        loaded = repo2.get_by_tag("persisted_scenario")
        assert loaded is not None
        assert loaded.id == s.id
        assert loaded.tag == "persisted_scenario"

    def test_persist_run_updates_status(self, engine, dm):
        """persist_run should write a run row and update scenario status in DB."""
        repo = SqlScenarioRepository(
            engine=engine,
            session_id="test_session",
            algorithms=algorithms,
            kpis=kpis,
            data_manager=dm,
        )
        repo.startup()

        s = _make_scenario(dm, tag="run_scenario")
        repo.add(s)

        # Simulate a completed run
        s.status = ScenarioStatus.COMPLETE
        s.result = {"data_id": "test_data"}
        s.kpis["Delay"].value = 500.0
        repo.persist_run(s)

        # Reload from DB and verify status is preserved
        repo2 = SqlScenarioRepository(
            engine=engine,
            session_id="test_session",
            algorithms=algorithms,
            kpis=kpis,
            data_manager=dm,
        )
        repo2.startup()
        loaded = repo2.get_by_tag("run_scenario")
        assert loaded.status == ScenarioStatus.COMPLETE

    def test_session_isolation(self, engine):
        """Repositories for different sessions must not see each other's scenarios."""
        data_meta.create_all(engine, checkfirst=True)
        scenario_meta.create_all(engine, checkfirst=True)

        for sid in ("session_x", "session_y"):
            dm_local = DatabaseDataManager(
                etl_factory=ExampleETLFactory,
                schemas=example_schemas,
                engine=engine,
                session_id=sid,
                data_object_type=DataSource,
            )
            dm_local.startup()
            ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="ds")
            ds.add_table("t", pd.DataFrame({"id": [sid]}))
            dm_local.add_data_source(ds)

            repo_local = SqlScenarioRepository(
                engine=engine,
                session_id=sid,
                algorithms=algorithms,
                kpis=kpis,
                data_manager=dm_local,
            )
            repo_local.startup()
            s = Scenario(
                tag=f"scenario_{sid}",
                input_data=dm_local.get_data("ds"),
                kpis={"Delay": DelayKPI()},
                algorithm=SlowAlgorithm(SlowAlgorithmParams()),
            )
            repo_local.add(s)

        # repo for session_x should not see session_y's scenario
        dm_x = DatabaseDataManager(
            etl_factory=ExampleETLFactory,
            schemas=example_schemas,
            engine=engine,
            session_id="session_x",
            data_object_type=DataSource,
        )
        dm_x.startup()
        rx = SqlScenarioRepository(
            engine=engine,
            session_id="session_x",
            algorithms=algorithms,
            kpis=kpis,
            data_manager=dm_x,
        )
        rx.startup()
        assert rx.has_tag("scenario_session_x")
        assert not rx.has_tag("scenario_session_y")
