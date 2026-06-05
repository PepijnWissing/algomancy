"""Tests for the DataParameters construct (issue #19, milestone #23).

DataParameters are declared on concrete ``BaseDataSource`` subclasses, populated
per scenario, persisted alongside the algorithm params, and pushed onto the
algorithm via ``BaseAlgorithm.set_data_params`` before ``run()``. The framework
does NOT apply them to data automatically — the algorithm reads
``self.data_params`` and decides what to do.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pandas as pd
import pytest

pytest.importorskip("sqlalchemy", reason="requires algomancy-scenario[database]")

import sqlalchemy as sa

from algomancy_data import DataClassification, DataSource
from algomancy_data.database.database_manager import DatabaseDataManager
from algomancy_data.database.models import metadata as data_meta
from algomancy_scenario import (
    BaseAlgorithm,
    BaseParameterSet,
    IntegerParameter,
    Scenario,
    ScenarioStatus,
    StringParameter,
)
from algomancy_scenario.persistence.models import metadata as scenario_meta
from algomancy_scenario.persistence.sql_repository import SqlScenarioRepository
from algomancy_scenario.result import ScenarioResult
from algomancy_utils.baseparameterset import EmptyParameters, ParameterError

# Load shared fixtures from the conftest in the same directory.
_CONFTEST = pathlib.Path(__file__).resolve().parent / "conftest.py"
_spec = importlib.util.spec_from_file_location("_dp_test_shared", _CONFTEST)
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)

ExampleETLFactory = _shared.ExampleETLFactory
example_schemas = _shared.example_schemas
kpis = _shared.kpis
DelayKPI = _shared.DelayKPI


# --------------------------------------------------------------------------- #
# Test fixtures: a DataSource subclass that DOES declare data parameters
# --------------------------------------------------------------------------- #


class FilteredDataParameters(BaseParameterSet):
    def __init__(self) -> None:
        super().__init__(name="Filtered")
        self.add_parameters(
            [
                IntegerParameter(name="row_limit", minvalue=1, default=10),
                StringParameter(name="label", default="default-label"),
            ]
        )

    def validate(self) -> None:
        pass


class FilteredDataSource(DataSource):
    def initialize_data_parameters(self) -> BaseParameterSet:
        return FilteredDataParameters()


class _RecordingAlgorithm(BaseAlgorithm):
    """Algorithm that captures the data_params it sees in ``run`` for assertions."""

    def __init__(self, params: BaseParameterSet) -> None:
        super().__init__("Recording", params)
        self.observed_data_params: BaseParameterSet | None = None

    @staticmethod
    def initialize_parameters() -> BaseParameterSet:
        return EmptyParameters()

    def run(self, data) -> ScenarioResult:
        self.observed_data_params = self.data_params
        self.set_progress(100)
        return ScenarioResult(data_id=data.id)


# --------------------------------------------------------------------------- #
# BaseDataSource default behaviour
# --------------------------------------------------------------------------- #


class TestDefaultDataParameters:
    def test_plain_data_source_returns_empty_parameters(self):
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="plain")
        params = ds.initialize_data_parameters()
        assert isinstance(params, EmptyParameters)
        assert not params.has_inputs()

    def test_subclass_can_declare_parameters(self):
        ds = FilteredDataSource(ds_type=DataClassification.MASTER_DATA, name="filtered")
        params = ds.initialize_data_parameters()
        assert params.has_inputs()
        assert params.contains("row_limit")
        assert params.contains("label")


# --------------------------------------------------------------------------- #
# BaseAlgorithm storage / setter
# --------------------------------------------------------------------------- #


class TestBaseAlgorithmDataParams:
    def test_default_data_params_are_empty(self):
        algo = _RecordingAlgorithm(EmptyParameters())
        assert isinstance(algo.data_params, EmptyParameters)

    def test_set_data_params_replaces_attribute(self):
        algo = _RecordingAlgorithm(EmptyParameters())
        new_params = FilteredDataParameters()
        algo.set_data_params(new_params)
        assert algo.data_params is new_params

    def test_set_data_params_none_falls_back_to_empty(self):
        algo = _RecordingAlgorithm(EmptyParameters())
        algo.set_data_params(FilteredDataParameters())
        algo.set_data_params(None)
        assert isinstance(algo.data_params, EmptyParameters)


# --------------------------------------------------------------------------- #
# Scenario.process pushes data_params onto the algorithm BEFORE run()
# --------------------------------------------------------------------------- #


class TestScenarioPushesDataParams:
    def test_process_pushes_data_params_before_run(self):
        ds = FilteredDataSource(ds_type=DataClassification.MASTER_DATA, name="ds")
        ds.add_table("t", pd.DataFrame({"id": ["a"]}))
        data_params = FilteredDataParameters()
        data_params.set_validated_values({"row_limit": 7, "label": "hello"})

        algo = _RecordingAlgorithm(EmptyParameters())
        scenario = Scenario(
            tag="t",
            input_data=ds,
            kpis={"Delay": DelayKPI()},
            algorithm=algo,
            data_params=data_params,
        )
        scenario.process()

        assert scenario.status == ScenarioStatus.COMPLETE
        assert algo.observed_data_params is data_params
        assert algo.observed_data_params["row_limit"] == 7
        assert algo.observed_data_params["label"] == "hello"

    def test_scenario_defaults_to_empty_when_omitted(self):
        ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="plain")
        ds.add_table("t", pd.DataFrame({"id": ["a"]}))
        algo = _RecordingAlgorithm(EmptyParameters())
        scenario = Scenario(
            tag="t",
            input_data=ds,
            kpis={"Delay": DelayKPI()},
            algorithm=algo,
        )
        scenario.process()

        assert scenario.status == ScenarioStatus.COMPLETE
        assert isinstance(algo.observed_data_params, EmptyParameters)


# --------------------------------------------------------------------------- #
# ScenarioFactory + ScenarioManager: validation and tuple shape
# --------------------------------------------------------------------------- #


@pytest.fixture
def engine():
    return sa.create_engine("sqlite:///:memory:")


@pytest.fixture
def dm_with_filtered_source(engine):
    data_meta.create_all(engine, checkfirst=True)
    manager = DatabaseDataManager(
        etl_factory=ExampleETLFactory,
        schemas=example_schemas,
        engine=engine,
        session_id="dp_session",
        data_object_type=FilteredDataSource,
    )
    manager.startup()
    ds = FilteredDataSource(ds_type=DataClassification.MASTER_DATA, name="ds")
    ds.add_table("item", pd.DataFrame({"id": ["a", "b"], "value": [1, 2]}))
    manager.add_data_source(ds)
    return manager


class TestScenarioFactoryDataParams:
    def test_get_associated_parameters_returns_tuple(self, dm_with_filtered_source):
        from algomancy_scenario.scenariofactory import ScenarioFactory

        algos = {"Recording": _RecordingAlgorithm}
        factory = ScenarioFactory(
            kpis=kpis, algorithms=algos, data_manager=dm_with_filtered_source
        )
        algo_params, data_params = factory.get_associated_parameters("Recording", "ds")
        assert isinstance(algo_params, BaseParameterSet)
        assert isinstance(data_params, FilteredDataParameters)

    def test_get_associated_parameters_without_dataset_returns_empty_data(
        self, dm_with_filtered_source
    ):
        from algomancy_scenario.scenariofactory import ScenarioFactory

        algos = {"Recording": _RecordingAlgorithm}
        factory = ScenarioFactory(
            kpis=kpis, algorithms=algos, data_manager=dm_with_filtered_source
        )
        _, data_params = factory.get_associated_parameters("Recording")
        assert isinstance(data_params, EmptyParameters)

    def test_create_validates_supplied_data_params(self, dm_with_filtered_source):
        from algomancy_scenario.scenariofactory import ScenarioFactory

        algos = {"Recording": _RecordingAlgorithm}
        factory = ScenarioFactory(
            kpis=kpis, algorithms=algos, data_manager=dm_with_filtered_source
        )
        # row_limit has minvalue=1, so 0 is invalid.
        with pytest.raises(ParameterError):
            factory.create(
                tag="bad",
                dataset_key="ds",
                algo_name="Recording",
                algo_params={},
                data_params={"row_limit": 0},
            )

    def test_create_applies_supplied_data_params(self, dm_with_filtered_source):
        from algomancy_scenario.scenariofactory import ScenarioFactory

        algos = {"Recording": _RecordingAlgorithm}
        factory = ScenarioFactory(
            kpis=kpis, algorithms=algos, data_manager=dm_with_filtered_source
        )
        scenario = factory.create(
            tag="ok",
            dataset_key="ds",
            algo_name="Recording",
            algo_params={},
            data_params={"row_limit": 5, "label": "x"},
        )
        assert scenario.data_params["row_limit"] == 5
        assert scenario.data_params["label"] == "x"


# --------------------------------------------------------------------------- #
# Persistence: round-trip through SqlScenarioRepository
# --------------------------------------------------------------------------- #


@pytest.fixture
def repo_factory(engine, dm_with_filtered_source):
    """Return a callable that builds fresh SqlScenarioRepository instances."""
    scenario_meta.create_all(engine, checkfirst=True)
    algos = {"Recording": _RecordingAlgorithm}

    def _make():
        r = SqlScenarioRepository(
            engine=engine,
            session_id="dp_session",
            algorithms=algos,
            kpis=kpis,
            data_manager=dm_with_filtered_source,
        )
        r.startup()
        return r

    return _make


def _make_scenario_with_data_params(dm, *, data_params=None, tag="dp_scenario"):
    algo = _RecordingAlgorithm(EmptyParameters())
    return Scenario(
        tag=tag,
        input_data=dm.get_data("ds"),
        kpis={"Delay": DelayKPI()},
        algorithm=algo,
        data_params=data_params,
    )


class TestPersistenceRoundTrip:
    def test_round_trip_with_populated_data_params(
        self, repo_factory, dm_with_filtered_source
    ):
        data_params = FilteredDataParameters()
        data_params.set_validated_values({"row_limit": 42, "label": "persisted"})

        repo = repo_factory()
        scenario = _make_scenario_with_data_params(
            dm_with_filtered_source, data_params=data_params
        )
        repo.add(scenario)

        # Cold reload from same DB.
        repo2 = repo_factory()
        loaded = repo2.get_by_tag("dp_scenario")
        assert loaded is not None
        assert isinstance(loaded.data_params, FilteredDataParameters)
        assert loaded.data_params["row_limit"] == 42
        assert loaded.data_params["label"] == "persisted"

    def test_round_trip_without_data_params_back_compat(
        self, repo_factory, dm_with_filtered_source
    ):
        repo = repo_factory()
        scenario = _make_scenario_with_data_params(
            dm_with_filtered_source, data_params=None, tag="legacy"
        )
        repo.add(scenario)

        repo2 = repo_factory()
        loaded = repo2.get_by_tag("legacy")
        assert loaded is not None
        # Defaults reconstruct from the data source's declaration (filtered).
        assert isinstance(loaded.data_params, FilteredDataParameters)
        assert loaded.data_params["row_limit"] == 10  # default

    def test_migration_adds_column_to_old_schema(self, engine):
        """SqlScenarioRepository.startup() ALTERs in the new column."""
        # Build the old-shape table by hand (no ``data_parameter_values``).
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "CREATE TABLE algomancy_scenarios ("
                    "id TEXT PRIMARY KEY, "
                    "tag TEXT NOT NULL, "
                    "session_id TEXT NOT NULL, "
                    "input_data_key TEXT NOT NULL, "
                    "algorithm_name TEXT NOT NULL, "
                    "parameter_values TEXT, "
                    "kpi_names TEXT, "
                    "status TEXT NOT NULL, "
                    "created_at TIMESTAMP)"
                )
            )
        data_meta.create_all(engine, checkfirst=True)
        dm = DatabaseDataManager(
            etl_factory=ExampleETLFactory,
            schemas=example_schemas,
            engine=engine,
            session_id="dp_session",
            data_object_type=DataSource,
        )
        dm.startup()

        repo = SqlScenarioRepository(
            engine=engine,
            session_id="dp_session",
            algorithms={"Recording": _RecordingAlgorithm},
            kpis=kpis,
            data_manager=dm,
        )
        repo.startup()

        inspector = sa.inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("algomancy_scenarios")}
        assert "data_parameter_values" in cols
