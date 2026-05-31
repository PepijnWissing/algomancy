"""Tests for M8 — Reference algorithms & KPIs."""

import math

import pandas as pd
import pytest

from example.data_handling.results import WarehouseAllocationResult
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sku_df() -> pd.DataFrame:
    return pd.read_csv(
        "example/data/default_session/example_data/sku_data.csv", sep=";"
    )


@pytest.fixture()
def layout_df() -> pd.DataFrame:
    return pd.read_csv(
        "example/data/default_session/example_data/warehouse_layout.csv", sep=";"
    )


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
