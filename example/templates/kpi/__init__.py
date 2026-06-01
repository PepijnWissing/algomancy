from .edge_kpis import InfKPI, NaNKPI, NegativeKPI, RaisingKPI, ZeroAtThresholdKPI
from .warehouse_kpis import (
    WarehouseTravelKPI,
    WarehouseZoneBalanceKPI,
    WarehouseReslotCostKPI,
)

# The Delay/Error/Throughput/Utilization classes are kept around as minimal
# BaseKPI examples but are intentionally NOT registered: they return random
# placeholder values, which would pollute the KPI table on real warehouse
# scenarios (ScenarioFactory attaches every registered KPI to every scenario).
__all__ = [
    "WarehouseTravelKPI",
    "WarehouseZoneBalanceKPI",
    "WarehouseReslotCostKPI",
    "NaNKPI",
    "InfKPI",
    "NegativeKPI",
    "ZeroAtThresholdKPI",
    "RaisingKPI",
]

kpi_templates = {
    "NaN KPI": NaNKPI,
    "Inf KPI": InfKPI,
    "Negative KPI": NegativeKPI,
    "Zero-at-threshold KPI": ZeroAtThresholdKPI,
    "Raising KPI": RaisingKPI,
    "Travel Distance": WarehouseTravelKPI,
    "Zone Balance": WarehouseZoneBalanceKPI,
    "Reslot Cost": WarehouseReslotCostKPI,
}
