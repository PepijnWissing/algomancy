import pandas as pd

from algomancy_scenario import ScenarioResult


class WarehouseAllocationResult(ScenarioResult):
    """Scenario result that carries a full warehouse slot allocation.

    Attributes:
        allocation: Mapping from itemid to proposed slotid.
        sku_data: DataFrame with at least itemid, daily_picks, currentslot columns.
        layout_data: DataFrame with at least slotid, x, y, zone columns.
        depot_x: X coordinate of the depot (pick origin).
        depot_y: Y coordinate of the depot (pick origin).
    """

    def __init__(
        self,
        data_id: str,
        allocation: dict[str, str],
        sku_data: pd.DataFrame,
        layout_data: pd.DataFrame,
        depot_x: float,
        depot_y: float,
    ) -> None:
        super().__init__(data_id)
        self.allocation = allocation
        self.sku_data = sku_data
        self.layout_data = layout_data
        self.depot_x = depot_x
        self.depot_y = depot_y

    def to_dict(self) -> dict:
        base = super().to_dict()
        base["allocation"] = self.allocation
        base["depot_x"] = self.depot_x
        base["depot_y"] = self.depot_y
        return base
