from .DelayKPITemplate import DelayKPI
from .ErrorKPITemplate import ErrorKPI
from .ThroughputKPITemplate import ThroughputKPI
from .UtilizationKPITemplate import UtilizationKPI
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
    "DelayKPI",
    "ErrorKPI",
    "ThroughputKPI",
    "UtilizationKPI",
    "WarehouseTravelKPI",
    "WarehouseZoneBalanceKPI",
    "WarehouseReslotCostKPI",
    "kpi_templates",
]

kpi_templates = {
    "Travel Distance": WarehouseTravelKPI,
    "Zone Balance": WarehouseZoneBalanceKPI,
    "Reslot Cost": WarehouseReslotCostKPI,
}
