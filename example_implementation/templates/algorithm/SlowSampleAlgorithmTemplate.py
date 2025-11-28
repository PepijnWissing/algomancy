from time import sleep
from typing import Callable

from algomancy.dataengine import DataSource
from algomancy.scenarioengine import ScenarioResult, AlgorithmTemplate
from algomancy.scenarioengine.algorithmparameters import (
    AlgorithmParameters,
    IntegerParameter,
)


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

        return int(duration_parameter.value)

    def validate(self):
        pass


def slow_sample_algorithm(
    data: DataSource,
    parameters: SlowSampleAlgorithmParams,
    set_progress: Callable[[float], None],
) -> ScenarioResult:
    for i in range(parameters.duration):
        set_progress(100 * i / parameters.duration)
        sleep(1)
    set_progress(1)
    return ScenarioResult(data_id=data.id)  # placeholder


# Explicitly specify the generic type parameter
slow_sample_algorithm_template = AlgorithmTemplate(
    name="Slow",
    param_type=SlowSampleAlgorithmParams,
    main_method_template=slow_sample_algorithm,
)
