(tutorial-kpi-ref)=
# KPIs
We define the KPIs for our instance. We are interested in the total cost of the tour.

The quickstart generated a skeleton at `src/templates/kpi/tsp_kpi.py`. We will replace that skeleton with a `TotalCostsKPI` implementation.

1. Create `total_costs.py` in `src/templates/kpi/`.
   First define the name, direction (which direction is better), and unit of measurement.
   Then implement `compute` based on the `ResultModel`:

:::{dropdown} {octicon}`code` Code
:color: info

```python
from algomancy_scenario import BaseKPI, ImprovementDirection
from algomancy_utils import BaseMeasurement, QUANTITIES

from data_handling.result_model.result_model import ResultModel


class TotalCostsKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            "Total_costs",
            ImprovementDirection.HIGHER,
            BaseMeasurement(
                QUANTITIES["money"]["$"], min_digits=1, max_digits=3, decimals=2
            ),
        )

    def compute(self, result: ResultModel) -> float:
        total_costs = 0.0
        if result.tour is not None:
            for route in result.tour:
                total_costs += route.cost
        return total_costs
```
:::

2. Create `__init__.py` in `src/templates/kpi/` to export the KPI template dictionary.
   The dict key is the name that appears in the dashboard; the value is the class:

```python
from .total_costs import TotalCostsKPI

kpi_templates = {
    "Total_costs": TotalCostsKPI,
}
```

3. Update `main.py` to use `TotalCostsKPI`. The quickstart already added a `kpi_templates` argument to `AppConfiguration` — update the import and the dict:

```python
from src.templates.kpi import kpi_templates
```

```python
app_cfg = AppConfiguration(
    ...
    kpi_templates=kpi_templates,
    ...
)
```
