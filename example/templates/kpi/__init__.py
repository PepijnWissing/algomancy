from .DelayKPITemplate import DelayKPI
from .ErrorKPITemplate import ErrorKPI
from .ThroughputKPITemplate import ThroughputKPI
from .UtilizationKPITemplate import UtilizationKPI

kpi_templates = {
    "Delay": DelayKPI,
    "Error": ErrorKPI,
    "Throughput": ThroughputKPI,
    "Utilization": UtilizationKPI,
}
