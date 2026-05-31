import math
import random as _random

import pandas as pd

from algomancy_data import DataSource
from algomancy_scenario import (
    BaseAlgorithm,
    BaseParameterSet,
    BooleanParameter,
    FloatParameter,
    IntegerParameter,
)

from example.data_handling.results import WarehouseAllocationResult


# ---------------------------------------------------------------------------
# Shared parameter set
# ---------------------------------------------------------------------------


class SlottingParams(BaseParameterSet):
    """Parameters shared by all three slotting algorithms."""

    def __init__(self, name: str = "Slotting") -> None:
        super().__init__(name=name)
        self.add_parameters(
            [
                FloatParameter(name="depot_x", default=0.0),
                FloatParameter(name="depot_y", default=0.0),
                BooleanParameter(name="respect_zones", default=False),
            ]
        )

    @property
    def depot_x(self) -> float:
        return self._parameters["depot_x"].value

    @property
    def depot_y(self) -> float:
        return self._parameters["depot_y"].value

    @property
    def respect_zones(self) -> bool:
        return self._parameters["respect_zones"].value

    def validate(self):
        pass


class SASlottingParams(SlottingParams):
    """Extended parameters for SimulatedAnnealingSlotting."""

    def __init__(self, name: str = "SA Slotting") -> None:
        super().__init__(name=name)
        self.add_parameters(
            [
                IntegerParameter(name="iterations", default=2000, minvalue=1),
                FloatParameter(
                    name="start_temperature",
                    default=100.0,
                    minvalue=FloatParameter.EPSILON,
                ),
                FloatParameter(
                    name="cooling_rate", default=0.995, minvalue=FloatParameter.EPSILON
                ),
                IntegerParameter(name="seed", default=42),
            ]
        )

    @property
    def iterations(self) -> int:
        return self._parameters["iterations"].value

    @property
    def start_temperature(self) -> float:
        return self._parameters["start_temperature"].value

    @property
    def cooling_rate(self) -> float:
        return self._parameters["cooling_rate"].value

    @property
    def seed(self) -> int:
        return self._parameters["seed"].value


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _load_tables(data: DataSource) -> tuple[pd.DataFrame, pd.DataFrame]:
    sku = data.tables["sku_data"].copy()
    layout = data.tables["warehouse_layout"].copy()
    return sku, layout


def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _travel_cost(
    allocation: dict[str, str],
    sku: pd.DataFrame,
    layout: pd.DataFrame,
    depot_x: float,
    depot_y: float,
) -> float:
    slot_pos = layout.set_index("slotid")[["x", "y"]].to_dict("index")
    total = 0.0
    for _, row in sku.iterrows():
        slotid = allocation.get(str(row["itemid"]))
        if slotid is None or slotid not in slot_pos:
            continue
        pos = slot_pos[slotid]
        total += float(row["daily_picks"]) * _dist(pos["x"], pos["y"], depot_x, depot_y)
    return total


def _build_result(
    data: DataSource,
    allocation: dict[str, str],
    sku: pd.DataFrame,
    layout: pd.DataFrame,
    depot_x: float,
    depot_y: float,
) -> WarehouseAllocationResult:
    return WarehouseAllocationResult(
        data_id=data.id,
        allocation=allocation,
        sku_data=sku,
        layout_data=layout,
        depot_x=depot_x,
        depot_y=depot_y,
    )


# ---------------------------------------------------------------------------
# AsIsSlotting
# ---------------------------------------------------------------------------


class AsIsSlotting(BaseAlgorithm):
    """Baseline: returns the current slot assignment unchanged."""

    def __init__(self, params: SlottingParams) -> None:
        super().__init__("AsIs Slotting", params)

    @staticmethod
    def initialize_parameters() -> SlottingParams:
        return SlottingParams(name="AsIs Slotting")

    def run(self, data: DataSource) -> WarehouseAllocationResult:
        sku, layout = _load_tables(data)
        p: SlottingParams = self.params

        allocation = {
            str(row["itemid"]): str(row["currentslot"]) for _, row in sku.iterrows()
        }

        self.set_progress(100)
        return _build_result(data, allocation, sku, layout, p.depot_x, p.depot_y)


# ---------------------------------------------------------------------------
# GreedySlotting
# ---------------------------------------------------------------------------


class GreedySlotting(BaseAlgorithm):
    """Greedy: assign high-pick items to slots nearest the depot."""

    def __init__(self, params: SlottingParams) -> None:
        super().__init__("Greedy Slotting", params)

    @staticmethod
    def initialize_parameters() -> SlottingParams:
        return SlottingParams(name="Greedy Slotting")

    def run(self, data: DataSource) -> WarehouseAllocationResult:
        sku, layout = _load_tables(data)
        p: SlottingParams = self.params

        # Sort items by daily_picks descending (deterministic tiebreak on itemid)
        items = sku.sort_values(
            ["daily_picks", "itemid"], ascending=[False, True]
        ).reset_index(drop=True)

        # Build list of available slots sorted by distance to depot
        layout_sorted = layout.copy()
        layout_sorted["_dist"] = layout_sorted.apply(
            lambda r: _dist(r["x"], r["y"], p.depot_x, p.depot_y), axis=1
        )
        layout_sorted = layout_sorted.sort_values("_dist").reset_index(drop=True)

        allocation: dict[str, str] = {}

        if p.respect_zones:
            # Group slots by zone; for each item keep only same-zone slots
            item_zones = sku.set_index("itemid")["currentslot"].map(
                layout.set_index("slotid")["zone"]
            )
            slots_by_zone: dict[str, list[str]] = {}
            for _, row in layout_sorted.iterrows():
                slots_by_zone.setdefault(row["zone"], []).append(row["slotid"])

            zone_queues = {z: list(slots) for z, slots in slots_by_zone.items()}

            for _, row in items.iterrows():
                iid = str(row["itemid"])
                zone = item_zones.get(row["itemid"], None)
                if zone and zone in zone_queues and zone_queues[zone]:
                    allocation[iid] = zone_queues[zone].pop(0)
                else:
                    # fallback: keep current slot
                    allocation[iid] = str(row["currentslot"])
        else:
            available = list(layout_sorted["slotid"])
            for _, row in items.iterrows():
                iid = str(row["itemid"])
                if available:
                    allocation[iid] = available.pop(0)
                else:
                    allocation[iid] = str(row["currentslot"])

        self.set_progress(100)
        return _build_result(data, allocation, sku, layout, p.depot_x, p.depot_y)


# ---------------------------------------------------------------------------
# SimulatedAnnealingSlotting
# ---------------------------------------------------------------------------


class SimulatedAnnealingSlotting(BaseAlgorithm):
    """SA slotting: start from AsIs, improve by swapping item-slot pairs.

    Uses O(1) incremental delta-cost updates to stay well within the 5-second
    budget on the default warehouse data (150 items, 2000 iterations).
    """

    def __init__(self, params: SASlottingParams) -> None:
        super().__init__("SA Slotting", params)

    @staticmethod
    def initialize_parameters() -> SASlottingParams:
        return SASlottingParams()

    def run(self, data: DataSource) -> WarehouseAllocationResult:
        sku, layout = _load_tables(data)
        p: SASlottingParams = self.params
        rng = _random.Random(p.seed)

        # Precompute lookups for O(1) delta evaluation
        dist_map: dict[str, float] = {
            str(row["slotid"]): _dist(row["x"], row["y"], p.depot_x, p.depot_y)
            for _, row in layout.iterrows()
        }
        picks_map: dict[str, float] = {
            str(row["itemid"]): float(row["daily_picks"]) for _, row in sku.iterrows()
        }

        # Start from AsIs allocation
        allocation: dict[str, str] = {
            str(row["itemid"]): str(row["currentslot"]) for _, row in sku.iterrows()
        }
        item_ids = list(allocation.keys())

        current_cost = sum(
            picks_map[iid] * dist_map.get(sid, 0.0) for iid, sid in allocation.items()
        )
        temp = p.start_temperature
        progress_step = max(1, p.iterations // 100)

        for i in range(p.iterations):
            a, b = rng.sample(item_ids, 2)
            s_a, s_b = allocation[a], allocation[b]

            # Delta = change in cost if we swap a and b's slots
            delta = picks_map[a] * (
                dist_map.get(s_b, 0.0) - dist_map.get(s_a, 0.0)
            ) + picks_map[b] * (dist_map.get(s_a, 0.0) - dist_map.get(s_b, 0.0))

            if delta < 0 or (temp > 0 and rng.random() < math.exp(-delta / temp)):
                allocation[a], allocation[b] = s_b, s_a
                current_cost += delta

            temp *= p.cooling_rate

            if (i + 1) % progress_step == 0:
                self.set_progress(int(100 * (i + 1) / p.iterations))

        self.set_progress(100)
        return _build_result(data, allocation, sku, layout, p.depot_x, p.depot_y)
