(tutorial-kpi-ref)=
# KPIs
We define the KPIs for our instance. We are interested in the total costs of the tour for this tutorial. 
We store the KPI definition as a template in the directory src/templates/kpi/.

1. Create the file total_costs.py in the directory src/templates/kpi/.
First we need to define a TotalCostKPI, and determine its name, direction (what direction is considered better), 
and the unit of measurement of the KPI.
Secondly, we define the computation function, based on the ResultModel.
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
2. We also need to initialize the KPIs in an initialization script, __init__.py in the directory src/templates/kpi/.
The dict kpi_templates's key is the name of the KPI, whereas the value is the class of the KPI.
```python
from .total_costs import TotalCostsKPI

kpi_templates = {
    "Total_costs": TotalCostsKPI,
}
```
3. Add the kpi_templates dict to the main.py script in the AppConfiguration so that Algomancy knows about the KPIs.
Make sure to also import input_configs (PyCharm has built-in autocompletion for this)
```python
app_cfg = AppConfiguration(
        etl_factory=TSPETLFactory,
        kpi_templates=kpi_templates,
        algo_templates={'placeholder': PlaceholderAlgorithm},
        input_configs=input_configs,
        data_object_type=DataSource,
        autocreate=False, #this will be the default in next release
        autorun=False, #this will be the default in next release
        host=host,
        port=port,
        data_page="standard",#this will be the default in next release
    )
```