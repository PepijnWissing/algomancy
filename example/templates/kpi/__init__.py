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

# RaisingKPI is kept importable for direct unit tests of the framework's
# KPI-failure handling, but NOT registered here: every registered KPI is
# attached to every scenario via KpiFactory.create_all(), so registering a
# KPI that always raises would mark every scenario "failed" end-to-end.
kpi_templates = {
    "NaN KPI": NaNKPI,
    "Inf KPI": InfKPI,
    "Negative KPI": NegativeKPI,
    "Zero-at-threshold KPI": ZeroAtThresholdKPI,
    "Travel Distance": WarehouseTravelKPI,
    "Zone Balance": WarehouseZoneBalanceKPI,
    "Reslot Cost": WarehouseReslotCostKPI,
}
