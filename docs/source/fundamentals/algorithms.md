(fundamentals-algorithm-ref)=
# Algorithms and Parameters

Algorithms are the core logic of the framework, transforming a `DataSource` into a `ScenarioResult`. To ensure flexibility and ease of use, the framework uses a class-based approach for algorithms and a type-safe system for their parameters.

## BaseAlgorithm

Every algorithm in the framework must subclass `BaseAlgorithm`. This class provides the structure for execution, parameter management, and progress tracking.

### Key Components of an Algorithm:
1.  **`run(data)`**: The main method where the logic resides. It takes a `DataSource` and returns a `ScenarioResult`.
2.  **`initialize_parameters()`**: A static method that returns a default instance of the algorithm's parameter set. This is used by the GUI to generate the input form.
3.  **`set_progress(value)`**: A method to report the execution status (0-100%) back to the framework.

Example of a basic algorithm:

:::{dropdown} {octicon}`eye` Example
:color: success
```{code-block} python
:caption: A basic algorithm
:linenos: 

from time import sleep
from algomancy_scenario import BaseAlgorithm, ScenarioResult
from algomancy_data import BaseDataSource

class MyAlgorithm(BaseAlgorithm):
    def __init__(self, params: "MyParams"):
        super().__init__("My Custom Algorithm", params)

    @staticmethod
    def initialize_parameters():
        return MyParams()

    def run(self, data: BaseDataSource) -> ScenarioResult:
        duration = self.params.duration
        for i in range(duration):
            # Report progress to the GUI
            self.set_progress(100 * (i + 1) / duration)
            sleep(1)
        
        return ScenarioResult(data_id=data.id)
```
:::
## Parameters: `BaseParameterSet`

Algorithms are often driven by user-defined inputs. The `BaseParameterSet` class allows you to define these inputs in a 
type-safe way that the framework can automatically render in the GUI with an appropriate input component. Each `Algorithm` 
instance creates its own parameter set instance, which is passed to the algorithm during initialization. 

### Defining Parameters
You define a parameter set by subclassing `BaseParameterSet` and adding the parameters in the `__init__` method. 

```{important}
After construction, the parameter set is _locked_ and no more parameters can be added. In other words: the
`self.add_parameters` method must be be called in the `__init__` method. Note that the values of parameters 
can still be accessed and modified. 
```

:::{dropdown} {octicon}`eye` Example
:color: success
```{code-block} python
:caption: A custom ParameterSet
:linenos: 
from algomancy_utils import (BaseParameterSet, 
                             IntegerParameter, 
                             FloatParameter)

class MyParams(BaseParameterSet):
    def __init__(self):
        super().__init__(name="My Algorithm Parameters")
        
        self.add_parameters([
            IntegerParameter(name="duration", default=10, minvalue=1, maxvalue=60),
            FloatParameter(name="threshold", default=0.5, minvalue=0.0, maxvalue=1.0)
        ])

    @property
    def duration(self) -> int:
        return self["duration"]

    def validate(self):
        # Add cross-parameter validation here
        pass
```
:::

### Supported Parameter Types

| Parameter Type        | Description                                      | Example                                      |
| --------------------- | ------------------------------------------------ | -------------------------------------------- |
| `IntegerParameter`    | Whole numbers with bounds.                       | `IntegerParameter(name="count", default=1)`  |
| `FloatParameter`      | Decimal numbers with bounds.                     | `FloatParameter(name="rate", default=0.5)`  |
| `BooleanParameter`    | True/False toggle.                               | `BooleanParameter(name="verbose")`           |
| `StringParameter`     | Plain text input.                                | `StringParameter(name="label")`              |
| `EnumParameter`       | Single selection from a list.                    | `EnumParameter(name="mode", choices=["A"])` |
| `MultiEnumParameter`  | Multiple selections from a list.                 | `MultiEnumParameter(name="tags", ...)`       |
| `TimeParameter`       | A specific point in time.                        | `TimeParameter(name="start_time")`           |
| `IntervalParameter`   | A time range (start and end).                    | `IntervalParameter(name="window")`           |

### Data Parameters

Alongside its own parameter set, an algorithm receives a second
`BaseParameterSet` that the *data source* declared via
{ref}`initialize_data_parameters <data-parameters-ref>`. Read it from
`self.data_params` inside `run()` to subset, filter, or slice the input data
before the main loop. The framework persists the supplied values per
scenario and pushes them onto the algorithm before `run()`; nothing is
applied automatically.

```{code-block} python
:caption: Algorithm reading a data-parameter knob
:linenos:
def run(self, data: BaseDataSource) -> ScenarioResult:
    sku = data.tables["sku_data"].copy()
    if self.data_params.contains("category_filter"):
        selected = self.data_params["category_filter"]
        if selected:
            sku = sku[sku["category"].isin(selected)]
    # ...rest of the algorithm
```

Algorithms that don't care about data parameters simply ignore the
attribute — it defaults to `EmptyParameters()`, so the `.contains(...)`
guard is always safe.


## KPIs

**Key Performance Indicators (KPIs)** are used to evaluate the output of an algorithm. 
Like algorithms, they follow a class-based pattern by subclassing `BaseKPI`. 

### Implementing a KPI
Each KPI must implement the `compute(result)` method, which extracts a numeric value from the `ScenarioResult`. 

:::{dropdown} {octicon}`eye` Example
:color: success
Two things to note:
- The `__init__` method is used to define how the KPI is displayed and compared  
- The `compute` method must be implemented, and is used to extract the metric from the result

```{code-block} python
:caption: Example KPI implementation
:linenos:
from algomancy_scenario import BaseKPI, ImprovementDirection
from algomancy_utils import QUANTITIES, BaseMeasurement

class TotalCostKPI(BaseKPI):
    def __init__(self):
        # Define how the KPI should be displayed and compared
        super().__init__(
            name="Total Cost",
            better_when=ImprovementDirection.LOWER,
            base_measurement=BaseMeasurement(QUANTITIES["money"]["$"])
        )

    def compute(self, result: ScenarioResult) -> float:
        # Extract the metric from the result
        return sum([trip.cost for trip in result.trips])
```
:::
### Threshold KPIs
KPIs can also include a `threshold`. If the computed value meets the threshold (based on `better_when`), the KPI is marked as a "success" (e.g., with a checkmark in the GUI).

For more details, see the [API reference](kpi-ref).
