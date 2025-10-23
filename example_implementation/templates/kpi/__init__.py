from .DelayKPITemplate import delay_template
from .ErrorKPITemplate import error_template
from .ThroughputKPITemplate import throughput_template
from .UtilizationKPITemplate import utilization_template

kpi_templates = [
    delay_template,
    error_template,
    throughput_template,
    utilization_template,
]
