from time import sleep
from typing import Callable

from algomancy.dataengine import DataSource
from algomancy.scenarioengine import (
    AlgorithmTemplate,
    ScenarioResult,
)
from algomancy.scenarioengine.algorithmparameters import (
    AlgorithmParameters,
    FloatParameter,
)


class RandomAlgorithmParameters(AlgorithmParameters):
    def __init__(
        self,
        name: str = "Random",
    ):
        super().__init__(name=name)
        self.add_parameters(
            [FloatParameter(name="variance", minvalue=FloatParameter.EPSILON)]
        )

    @property
    def variance(self) -> float:
        return self._parameters["variance"].value

    def validate(self):
        pass


def random_algorithm(
    data: DataSource,
    parameters: RandomAlgorithmParameters,
    set_progress: Callable[[float], None],
) -> ScenarioResult:
    # run the algorithm
    sleep(parameters.variance)

    # set to complete
    set_progress(1)
    return ScenarioResult(data_id=data.id)  # placeholder


random_algorithm_template = AlgorithmTemplate(
    name="Random",
    param_type=RandomAlgorithmParameters,
    main_method_template=random_algorithm,
)
