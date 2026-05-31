from .DelayKPITemplate import DelayKPI
from .ErrorKPITemplate import ErrorKPI
from .ThroughputKPITemplate import ThroughputKPI
from .UtilizationKPITemplate import UtilizationKPI
from .edge_kpis import InfKPI, NaNKPI, NegativeKPI, RaisingKPI, ZeroAtThresholdKPI

kpi_templates = {
    "Delay": DelayKPI,
    "Error": ErrorKPI,
    "Throughput": ThroughputKPI,
    "Utilization": UtilizationKPI,
    "NaN KPI": NaNKPI,
    "Inf KPI": InfKPI,
    "Negative KPI": NegativeKPI,
    "Zero-at-threshold KPI": ZeroAtThresholdKPI,
    "Raising KPI": RaisingKPI,
}
