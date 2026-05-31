from .DelayKPITemplate import DelayKPI
from .ErrorKPITemplate import ErrorKPI
from .ThroughputKPITemplate import ThroughputKPI
from .UtilizationKPITemplate import UtilizationKPI
from .warehouse_kpis import (
    WarehouseTravelKPI,
    WarehouseZoneBalanceKPI,
    WarehouseReslotCostKPI,
)

kpi_templates = {
    "Delay": DelayKPI,
    "Error": ErrorKPI,
    "Throughput": ThroughputKPI,
    "Utilization": UtilizationKPI,
    "Travel Distance": WarehouseTravelKPI,
    "Zone Balance": WarehouseZoneBalanceKPI,
    "Reslot Cost": WarehouseReslotCostKPI,
}
