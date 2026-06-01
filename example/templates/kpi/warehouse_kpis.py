import math

from algomancy_scenario import ImprovementDirection, BaseKPI
from algomancy_utils import QUANTITIES, BaseMeasurement

from example.data_handling.results import WarehouseAllocationResult


def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


class WarehouseTravelKPI(BaseKPI):
    """Total pick-weighted travel distance: sum(daily_picks_i * dist(slot_i, depot)).

    Lower is better.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Travel Distance",
            better_when=ImprovementDirection.LOWER,
            base_measurement=BaseMeasurement(
                QUANTITIES["length"]["m"], min_digits=1, max_digits=3, decimals=0
            ),
        )

    def compute(self, result: WarehouseAllocationResult) -> float:
        if not isinstance(result, WarehouseAllocationResult):
            return float("nan")
        layout = result.layout_data.set_index("slotid")[["x", "y"]].to_dict("index")
        total = 0.0
        for _, row in result.sku_data.iterrows():
            slotid = result.allocation.get(str(row["itemid"]))
            if slotid is None or slotid not in layout:
                continue
            pos = layout[slotid]
            total += float(row["daily_picks"]) * _dist(
                pos["x"], pos["y"], result.depot_x, result.depot_y
            )
        return total


class WarehouseZoneBalanceKPI(BaseKPI):
    """Std-dev of total daily picks across warehouse zones.

    Lower means picks are distributed evenly across zones.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Zone Balance",
            better_when=ImprovementDirection.LOWER,
            base_measurement=BaseMeasurement(
                QUANTITIES["count"][""], min_digits=1, max_digits=6, decimals=1
            ),
        )

    def compute(self, result: WarehouseAllocationResult) -> float:
        if not isinstance(result, WarehouseAllocationResult):
            return float("nan")
        zone_map = result.layout_data.set_index("slotid")["zone"].to_dict()
        picks_by_zone: dict[str, float] = {}

        for _, row in result.sku_data.iterrows():
            slotid = result.allocation.get(str(row["itemid"]))
            if slotid is None:
                continue
            zone = zone_map.get(slotid)
            if zone is None:
                continue
            picks_by_zone[zone] = picks_by_zone.get(zone, 0.0) + float(
                row["daily_picks"]
            )

        if not picks_by_zone:
            return 0.0

        values = list(picks_by_zone.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)


class WarehouseReslotCostKPI(BaseKPI):
    """Number of items that need to be moved from their current slot.

    Lower means fewer physical moves required.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Reslot Cost",
            better_when=ImprovementDirection.LOWER,
            base_measurement=BaseMeasurement(
                QUANTITIES["count"][""], min_digits=1, max_digits=6, decimals=0
            ),
        )

    def compute(self, result: WarehouseAllocationResult) -> float:
        if not isinstance(result, WarehouseAllocationResult):
            return float("nan")
        moves = 0
        for _, row in result.sku_data.iterrows():
            iid = str(row["itemid"])
            proposed = result.allocation.get(iid)
            current = str(row["currentslot"])
            if proposed is not None and proposed != current:
                moves += 1
        return float(moves)
