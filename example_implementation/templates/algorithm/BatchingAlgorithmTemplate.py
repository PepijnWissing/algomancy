from time import sleep
from typing import Callable

from algomancy.dataengine import DataSource
from algomancy.scenarioengine import (
    AlgorithmTemplate,
    ScenarioResult,
)
from algomancy.scenarioengine.basealgorithmparameters import (
    BaseAlgorithmParameters,
    IntegerParameter,
    EnumParameter,
    BooleanParameter,
)

class BatchingAlgorithmParameters(BaseAlgorithmParameters):
    def __init__(
        self,
        name: str = "Batching",
    ):
        super().__init__(name=name)

        self.add_parameters(
            [
                IntegerParameter(name="batch_size", minvalue=1),
                EnumParameter(
                    name="search_direction", choices=["depth first", "breadth first"]
                ),
                BooleanParameter(name="use_cache"),
            ]
        )

    @property
    def batch_size(self) -> int:
        return self["batch_size"]

    @property
    def search_direction(self):
        return self["search_direction"]

    @property
    def use_cache(self):
        return self["use_cache"]

    def validate(self):
        pass


def batching_algorithm(
    data: DataSource,
    parameters: BatchingAlgorithmParameters,
    set_progress: Callable[[float], None],
) -> ScenarioResult:
    sleep(parameters.batch_size)
    set_progress(1)
    return ScenarioResult(data_id=data.id)  # placeholder


batching_algorithm_template = AlgorithmTemplate(
    name="Batching",
    param_type=BatchingAlgorithmParameters,
    main_method_template=batching_algorithm,
)
