(kpi-ref)=
# KPI
## Overview
Key Performance Indicator (KPI) framework for scenario evaluation.

This module defines the foundational classes and enums used to define, compute,
and present KPIs within the Algomancy framework. It integrates with the
`algomancy_utils.unit` system to provide smart, unit-aware formatting for
performance metrics.

### Core concepts:
- **BaseKPI**: An abstract base class for all KPIs. It handles the metadata
  (name, improvement direction), unit scaling, and threshold comparisons.
- **ImprovementDirection**: An enum defining what "better" means for a given
  metric (e.g., HIGHER is better for throughput, LOWER is better for latency).
- **Binary vs. Continuous KPIs**: KPIs can be simple numeric trackers (continuous)
  or they can have a threshold (binary), where they are either "successful"
  or "failed" based on whether they met the threshold.

### Why this exists:
Scenario results often contain raw data that needs to be distilled into
meaningful metrics. This module provides a consistent way to define these
metrics, automatically handle their units, and determine if they meet
predefined success criteria, making it easy to generate summary reports.

### Quick start:
1. Define a concrete KPI class by inheriting from `BaseKPI` and implementing
   the `compute` method.
2. Instantiate the KPI with a name, improvement direction, and base unit.
3. Call `compute_and_check(result)` to populate the KPI value from scenario results.
4. Use `pretty()` to get a human-readable string of the result.

:::{dropdown} {octicon}`eye` Example
:color: success
TODO Explain example

```{code-block} python
:caption: A basic KPI implementation
:linenos:

from algomancy_scenario import BaseKPI, ImprovementDirection
from algomancy_utils import QUANTITIES, BaseMeasurement

class DurationKPI(BaseKPI):
    def compute(self, result):
        # Logic to extract duration from result
        return 1250.5

time = QUANTITIES["time"]
# Expect duraction of at least 1000 seconds
kpi = DurationKPI(
    "System Duration",
    ImprovementDirection.AT_LEAST,
    BaseMeasurement(time["s"]),
    threshold=1000.0
)

kpi.compute_and_check(some_result_object)
print(kpi.pretty())
print(kpi.details())
```
```
✓
1.25 ks
```

Note that the KPI class is normally passed to the [app configuration](configuration-ref) and a separate instance of the KPI 
is constructed every Scenario. Typical use of the `DurationKPI` class would therefore be:

```{code-block} python
:caption: Using KPIs in the AppConfiguration
:linenos: 
config = AppConfiguration(
    ...
    kpi_templates = [DurationKPI, ...],
    ...
)
```
:::

## Reference
```{eval-rst}
.. automodule:: algomancy_scenario.keyperformanceindicator
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource
```