from .warehouse_kpis import (
    WarehouseTravelKPI,
    WarehouseZoneBalanceKPI,
    WarehouseReslotCostKPI,
)

__all__ = [
    "WarehouseTravelKPI",
    "WarehouseZoneBalanceKPI",
    "WarehouseReslotCostKPI",
]

kpi_templates = {
    "Travel Distance": WarehouseTravelKPI,
    "Zone Balance": WarehouseZoneBalanceKPI,
    "Reslot Cost": WarehouseReslotCostKPI,
}
