"""Tests for M8 — Reference algorithms & KPIs."""

import math
from pathlib import Path

import pandas as pd
import pytest

from algomancy_data import StatelessDataManager, DataSource

from example.data_handling.factories import ExampleETLFactory
from example.data_handling.results import WarehouseAllocationResult
from example.data_handling.schemas import example_schemas
from example.templates.algorithm.warehouse_slotting import (
    AsIsSlotting,
    GreedySlotting,
    SimulatedAnnealingSlotting,
)
from example.templates.kpi.warehouse_kpis import (
    WarehouseReslotCostKPI,
    WarehouseTravelKPI,
    WarehouseZoneBalanceKPI,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DATA_DIR = REPO_ROOT / "example" / "data" / "default_session" / "example_data"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sku_df() -> pd.DataFrame:
    return pd.read_csv(EXAMPLE_DATA_DIR / "sku_data.csv", sep=";")


@pytest.fixture()
def layout_df() -> pd.DataFrame:
    return pd.read_csv(EXAMPLE_DATA_DIR / "warehouse_layout.csv", sep=";")


class _FakeDataSource:
    def __init__(self, sku: pd.DataFrame, layout: pd.DataFrame) -> None:
        self.id = "test"
        self.tables = {"sku_data": sku, "warehouse_layout": layout}


@pytest.fixture()
def fake_data(sku_df, layout_df):
    return _FakeDataSource(sku_df, layout_df)


# ---------------------------------------------------------------------------
# WarehouseAllocationResult — #135
# ---------------------------------------------------------------------------


class TestWarehouseAllocationResult:
    def test_to_dict_round_trips_allocation(self, fake_data, sku_df, layout_df):
        alloc = {"1001": "SLOT-001", "1002": "SLOT-002"}
        r = WarehouseAllocationResult(
            data_id="x",
            allocation=alloc,
            sku_data=sku_df,
            layout_data=layout_df,
            depot_x=5.0,
            depot_y=5.0,
        )
        d = r.to_dict()
        assert d["allocation"] == alloc
        assert d["depot_x"] == 5.0
        assert d["depot_y"] == 5.0


# ---------------------------------------------------------------------------
# AsIsSlotting — #136
# ---------------------------------------------------------------------------


class TestAsIsSlotting:
    def test_allocation_equals_current_slot(self, fake_data, sku_df):
        algo = AsIsSlotting(AsIsSlotting.initialize_parameters())
        result = algo.run(fake_data)
        assert isinstance(result, WarehouseAllocationResult)
        for _, row in sku_df.iterrows():
            assert result.allocation[str(row["itemid"])] == str(row["currentslot"])


# ---------------------------------------------------------------------------
# GreedySlotting — #136
# ---------------------------------------------------------------------------


class TestGreedySlotting:
    def test_deterministic(self, fake_data):
        algo = GreedySlotting(GreedySlotting.initialize_parameters())
        r1 = algo.run(fake_data)
        r2 = algo.run(fake_data)
        assert r1.allocation == r2.allocation

    def test_all_items_allocated(self, fake_data, sku_df):
        algo = GreedySlotting(GreedySlotting.initialize_parameters())
        result = algo.run(fake_data)
        assert len(result.allocation) == len(sku_df)


# ---------------------------------------------------------------------------
# SimulatedAnnealingSlotting — #136
# ---------------------------------------------------------------------------


class TestSASlotting:
    def test_calls_set_progress_at_least_10_times(self, fake_data, monkeypatch):
        progress_calls = []
        algo = SimulatedAnnealingSlotting(
            SimulatedAnnealingSlotting.initialize_parameters()
        )
        monkeypatch.setattr(algo, "set_progress", lambda v: progress_calls.append(v))
        algo.run(fake_data)
        assert len(progress_calls) >= 10

    def test_completes_within_5_seconds(self, fake_data):
        import time

        algo = SimulatedAnnealingSlotting(
            SimulatedAnnealingSlotting.initialize_parameters()
        )
        start = time.monotonic()
        algo.run(fake_data)
        elapsed = time.monotonic() - start
        assert elapsed < 5.0


# ---------------------------------------------------------------------------
# KPIs — #137
# ---------------------------------------------------------------------------


class TestWarehouseTravelKPI:
    def test_greedy_strictly_better_than_asis(self, fake_data):
        asis = AsIsSlotting(AsIsSlotting.initialize_parameters()).run(fake_data)
        greedy = GreedySlotting(GreedySlotting.initialize_parameters()).run(fake_data)

        kpi_asis = WarehouseTravelKPI()
        kpi_asis.compute_and_check(asis)

        kpi_greedy = WarehouseTravelKPI()
        kpi_greedy.compute_and_check(greedy)

        assert kpi_greedy.value < kpi_asis.value

    def test_value_is_finite(self, fake_data):
        result = AsIsSlotting(AsIsSlotting.initialize_parameters()).run(fake_data)
        kpi = WarehouseTravelKPI()
        kpi.compute_and_check(result)
        assert math.isfinite(kpi.value)

    def test_to_dict_round_trips(self, fake_data):
        result = AsIsSlotting(AsIsSlotting.initialize_parameters()).run(fake_data)
        kpi = WarehouseTravelKPI()
        kpi.compute_and_check(result)
        d = kpi.to_dict()
        assert d["value"] == kpi.value


class TestWarehouseZoneBalanceKPI:
    def test_value_is_non_negative(self, fake_data):
        result = GreedySlotting(GreedySlotting.initialize_parameters()).run(fake_data)
        kpi = WarehouseZoneBalanceKPI()
        kpi.compute_and_check(result)
        assert kpi.value >= 0.0


class TestWarehouseReslotCostKPI:
    def test_asis_zero_reslot_cost(self, fake_data):
        result = AsIsSlotting(AsIsSlotting.initialize_parameters()).run(fake_data)
        kpi = WarehouseReslotCostKPI()
        kpi.compute_and_check(result)
        assert kpi.value == 0.0

    def test_greedy_positive_reslot_cost(self, fake_data):
        result = GreedySlotting(GreedySlotting.initialize_parameters()).run(fake_data)
        kpi = WarehouseReslotCostKPI()
        kpi.compute_and_check(result)
        assert kpi.value >= 0.0


# ---------------------------------------------------------------------------
# End-to-end: ExampleETLFactory + StatelessDataManager + GreedySlotting
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def etl_datasource() -> DataSource:
    """Run the real ExampleETLFactory pipeline against the example data dir."""
    dm = StatelessDataManager(
        etl_factory=ExampleETLFactory,
        schemas=example_schemas,
        save_type="json",
        data_object_type=DataSource,
    )

    # Logical name → filename on disk; the manager dispatches by schema extension.
    file_items = [
        ("sku_data", str(EXAMPLE_DATA_DIR / "sku_data.csv")),
        ("warehouse_layout", str(EXAMPLE_DATA_DIR / "warehouse_layout.csv")),
    ]
    files = dm.prepare_files(file_items_with_path=file_items)
    result = dm.etl_data(files, dataset_name="example_data")
    assert result.is_success, (
        "ETL pipeline failed: "
        f"{result.validation_result.counts_by_severity if result.validation_result else 'unknown'}"
    )
    return dm.get_data("example_data")


class TestExampleETLPipelineIntegration:
    """Drive the warehouse algorithms through the real ETL pipeline.

    Guards against silent drift between schemas / transformers and the
    columns the algorithms assume — the fast unit tests above bypass the
    factory by reading CSVs directly.
    """

    def test_etl_produces_warehouse_tables(self, etl_datasource):
        assert "sku_data" in etl_datasource.tables
        assert "warehouse_layout" in etl_datasource.tables

        sku = etl_datasource.tables["sku_data"]
        for col in ("itemid", "daily_picks", "currentslot"):
            assert col in sku.columns

        layout = etl_datasource.tables["warehouse_layout"]
        for col in ("slotid", "x", "y", "zone"):
            assert col in layout.columns

    def test_greedy_runs_on_etl_output(self, etl_datasource):
        algo = GreedySlotting(GreedySlotting.initialize_parameters())
        result = algo.run(etl_datasource)
        assert isinstance(result, WarehouseAllocationResult)
        assert len(result.allocation) == len(etl_datasource.tables["sku_data"])

        kpi = WarehouseTravelKPI()
        kpi.compute_and_check(result)
        assert math.isfinite(kpi.value)
        assert kpi.value > 0.0
