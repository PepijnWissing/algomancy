# Templates

Parts of the framework are reliant on user-defined templates. 
Conceptually, the user defines a mold, which may be used internally to create an object of a certain type.
For example, an algorithm template may define a set of parameters, which are then used to create

## Contents
1. [Algorithm Templates](#algorithm-templates)
2. [KPI Templates](#kpi-templates)

## Algorithm Templates
[To content](0_introduction.md#)

Oftentimes, an Algorithm will be dependent on a few key parameters to define its exact behavior. 
To accommodate this, the framework provides a template mechanism.
Specifically, a set of parameters is defined, which may be set from the front-end when the end-user creates a new Scenario.
These parameters are passed to a 'factory' method, which creates the actual Algorithm.
This means that:
> An `Algorithm` has a rigid set of parameters, though many `Algorithms` may share the same `AlgorithmTemplate`.

Creating an AlgorithmTemplate consists effectively of two components:
1. A set of parameters
2. A main method

Indeed, the actual creation of the AlgorithmTemplate is simply a matter of combining these two components. Consider the following example:
```python
slow_sample_algorithm_template = AlgorithmTemplate(
    name="Slow",
    param_type=SlowSampleAlgorithmParams,
    main_method_template=slow_sample_algorithm,
)
```

### Algorithm Parameters
The `AlgorithmParameters` class is, in practice, a set of expected parameter definitions.
It contains the description of a collection of parameters that is (joinly) required to create an `Algorithm` from an `AlgorithmTemplate`
Typically, the user will create a custom parameter definition for each `AlgorithmTemplate`. This is defined by subclassing `AlgorithmParameters`.
Consider the following example:

```python
# Define the parameters for the algorithm
class SampleAlgorithmParams(AlgorithmParameters):
    def __init__(self, name: str = "Sample") -> None:
        super().__init__(name=name)

        self.add_parameters(
            [FloatParameter(name="start_time", minvalue=9.0, maxvalue=17.0)],
            [FloatParameter(name="end_time", minvalue=9.0, maxvalue=17.0)]
        )

    @property
    def start_time(self) -> float:
        return self._parameters["start_time"].value
    
    @property
    def end_time(self) -> float:
        return self._parameters["end_time"].value

    def validate(self):
        assert self.start_time < self.end_time, "Start time must be before end time"
```

At a bare minimum, the subclass must implement the `__init__` method, which defines the parameters. 

The `.validate()` should be used to check parameter values which validity arises from their interaction with each other (e.g., `start_time < end_time`).
Each parameter has individual validation methods, depending on the parameter type, to check e.g., max/min values.

It is recommended to add property definitions for easy access to the parameter values, as the type wrappers make the parameter values a bit unfortunate to reach. 
In the example below, we add a property definition for the `start_time` parameter. 
This allows us to access the parameter value as `parameters.start_time`.
If the property is not defined, the parameter value may be accessed (from outside the class) as `parameters.get_values()["duration"].start_time`.


Currently, the framework supports only single-value parameters. 
To make sure that each parameter may be input appropriately (e.g., a toggle switch for boolean parameters), the parameters are wrapped in specific classes, as outlined in the table below.    

| Parameter Type   | Description                                                                 | Example                                                         |
|------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------|
| IntegerParameter | Numeric parameter with integer values. <br>Has a minimum and maximum value. | `IntegerParameter(name="duration", minvalue=1, maxvalue=60)`    |
| FloatParameter   | Numeric parameter with float values. <br>Has a minimum and maximum value.   | `FloatParameter(name="threshold", minvalue=0.0, maxvalue=1.0)`  |
| BooleanParameter | Boolean parameter.                                                          | `BooleanParameter(name="enable_feature")`                       |
| StringParameter  | String parameter.                                                           | `StringParameter(name="username")`                              |
| EnumParameter    | String parameter with a set of predefined values.                           | `EnumParameter(name="color", options=["red", "green", "blue"])` |

Note that the class wrappers also allow for some natural validation of the parameter values. For example, the `IntegerParameter` class will ensure that the value is within the specified range.




### Main method
```python
# Define the main method of the algorithm
def slow_sample_algorithm(
        data: DataSource, parameters: SlowSampleAlgorithmParams, set_progress: Callable[[float], None],
) -> ScenarioResult:
    # fetch parameter
    duration = parameters.duration
    
    # do something and track progress
    for i in range(parameters.duration):
        set_progress(100 * i / parameters.duration)
        sleep(1)
    
    # return result
    set_progress(1)
    return ScenarioResult(master_data_id=data.id)  #-- placeholder
```

### Complete example
```python
from time import sleep
from typing import Callable

from algomancy.dataengine import DataSource
from algomancy.scenarioengine import ScenarioResult, AlgorithmTemplate
from algomancy.scenarioengine.algorithmparameters import *

# Define the parameters for the algorithm
class SlowSampleAlgorithmParams(AlgorithmParameters):
    def __init__(self, name: str = "Slow") -> None:
        super().__init__(name=name)

        self.add_parameters(
            [IntegerParameter(name="duration", minvalue=1, maxvalue=60)]
        )

    @property
    def duration(self) -> int:
        param_dct = self._parameters
        duration_parameter = param_dct["duration"]

        return duration_parameter.value

    def validate(self):
        pass

# Define the main method of the algorithm
def slow_sample_algorithm(
    data: DataSource,
    parameters: SlowSampleAlgorithmParams,
    set_progress: Callable[[float], None],
) -> ScenarioResult:
    for i in range(int(parameters.duration)):
        set_progress(100 * i / parameters.duration)
        sleep(1)
    set_progress(1)
    return ScenarioResult(master_data_id=data.id)  # placeholder


# Combine the elements into an algorithm template
slow_sample_algorithm_template = AlgorithmTemplate(
    name="Slow",
    param_type=SlowSampleAlgorithmParams,
    main_method_template=slow_sample_algorithm,
)

```

## KPI Templates
[To content](0_introduction.md#)
