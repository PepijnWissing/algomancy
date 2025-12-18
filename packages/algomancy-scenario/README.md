### algomancy-scenario

Scenario modeling utilities for Algomancy: define algorithms and parameters, run scenarios against data, and compute KPIs.

#### Features
- `Scenario` lifecycle with statuses (`CREATED`, `QUEUED`, `PROCESSING`, `COMPLETE`, `FAILED`)
- `BaseAlgorithm` and parameter classes to define pluggable algorithms
- KPI framework (`BaseKPI`) to compute metrics from algorithm results
- Works with `algomancy-data` data sources and can be orchestrated from the GUI

#### Installation
```
pip install -e packages/algomancy-scenario
```

Requires Python >= 3.14.

#### Quick start
Define a simple algorithm and KPI, then run a `Scenario`:

```python
from algomancy_scenario import (
    Scenario, ScenarioStatus,
    BaseAlgorithm, BaseAlgorithmParameters, BaseKPI,
)
from algomancy_data import DataSource, DataClassification


# Minimal parameters type
class ExampleParams(BaseAlgorithmParameters):
    def serialize(self) -> dict:
        return {"hello": "world"}


# Minimal algorithm
class ExampleAlgorithm(BaseAlgorithm):
    def __init__(self):
        super().__init__(name="Example", params=ExampleParams())

    @staticmethod
    def initialize_parameters() -> ExampleParams:  # used by GUI tooling
        return ExampleParams()

    def run(self, data: DataSource) -> dict:
        # do something with data and return a result dictionary
        self.set_progress(100)
        return {"count_tables": len(data.list_tables())}


# Minimal KPI
class CountTablesKPI(BaseKPI):
    def __init__(self):
        super().__init__(name="Tables", improvement_direction=None)

    def compute_and_check(self, result: dict):
        self.value = result["count_tables"]


# Prepare data
ds = DataSource(ds_type=DataClassification.MASTER_DATA, name="warehouse")

# Build and run scenario
scenario = Scenario(
    tag="demo",
    input_data=ds,
    kpis={"tables": CountTablesKPI()},
    algorithm=ExampleAlgorithm(),
)

scenario.process()
assert scenario.status == ScenarioStatus.COMPLETE
print("Tables KPI:", scenario.kpis["tables"].value)
```

#### Related docs and examples
- Example app demonstrates scenario wiring: `example/pages/ScenarioPageContent.py`
- Algorithm/KPI examples: `example/templates/algorithm/` and `example/templates/kpi/`
