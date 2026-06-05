import json

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

    Implements :class:`algomancy_scenario.persistence.SqlResultLayout` so the
    two DataFrames land in real SQL tables when persisted to the database
    backend; the allocation/depot scalars are merged in via ``to_json`` /
    ``from_json`` as a small JSON sidecar table.
    """

    _META_SUBTABLE = "_meta"

    def __init__(
        self,
        data_id: str,
        allocation: dict[str, str] | None = None,
        sku_data: pd.DataFrame | None = None,
        layout_data: pd.DataFrame | None = None,
        depot_x: float = 0.0,
        depot_y: float = 0.0,
    ) -> None:
        super().__init__(data_id)
        self.allocation = allocation or {}
        self.sku_data = sku_data if sku_data is not None else pd.DataFrame()
        self.layout_data = layout_data if layout_data is not None else pd.DataFrame()
        self.depot_x = depot_x
        self.depot_y = depot_y

    def to_dict(self) -> dict:
        base = super().to_dict()
        base["allocation"] = self.allocation
        base["depot_x"] = self.depot_x
        base["depot_y"] = self.depot_y
        return base

    def to_json(self) -> str:
        return json.dumps(
            {
                "data_id": self.data_id,
                "completed_at": self.completed_at.isoformat(),
                "allocation": self.allocation,
                "depot_x": self.depot_x,
                "depot_y": self.depot_y,
                "sku_data": self.sku_data.to_dict(orient="records"),
                "layout_data": self.layout_data.to_dict(orient="records"),
            }
        )

    @classmethod
    def from_json(cls, json_string: str) -> "WarehouseAllocationResult":
        from datetime import datetime

        payload = json.loads(json_string)
        inst = cls(
            data_id=payload["data_id"],
            allocation=payload.get("allocation", {}),
            sku_data=pd.DataFrame(payload.get("sku_data", [])),
            layout_data=pd.DataFrame(payload.get("layout_data", [])),
            depot_x=payload.get("depot_x", 0.0),
            depot_y=payload.get("depot_y", 0.0),
        )
        completed_at = payload.get("completed_at")
        if completed_at:
            inst.completed_at = datetime.fromisoformat(completed_at)
        return inst

    def to_sql_tables(self) -> dict[str, pd.DataFrame]:
        meta = pd.DataFrame(
            [
                {
                    "data_id": self.data_id,
                    "completed_at": self.completed_at.isoformat(),
                    "depot_x": self.depot_x,
                    "depot_y": self.depot_y,
                    "allocation": json.dumps(self.allocation),
                }
            ]
        )
        return {
            "sku": self.sku_data,
            "layout": self.layout_data,
            self._META_SUBTABLE: meta,
        }

    def from_sql_tables(self, tables: dict[str, pd.DataFrame]) -> None:
        from datetime import datetime

        self.sku_data = tables.get("sku", pd.DataFrame())
        self.layout_data = tables.get("layout", pd.DataFrame())
        meta_df = tables.get(self._META_SUBTABLE)
        if meta_df is not None and not meta_df.empty:
            row = meta_df.iloc[0]
            self.data_id = str(row["data_id"])
            self.depot_x = float(row["depot_x"])
            self.depot_y = float(row["depot_y"])
            allocation_raw = row.get("allocation")
            if isinstance(allocation_raw, str) and allocation_raw:
                self.allocation = json.loads(allocation_raw)
            completed_at = row.get("completed_at")
            if isinstance(completed_at, str) and completed_at:
                self.completed_at = datetime.fromisoformat(completed_at)
