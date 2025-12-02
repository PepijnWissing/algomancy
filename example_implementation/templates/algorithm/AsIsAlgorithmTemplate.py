from time import sleep
from typing import Callable

from algomancy.dataengine import DataSource
from algomancy.scenarioengine import (
    AlgorithmTemplate,
    ScenarioResult,
)
from algomancy.scenarioengine.basealgorithmparameters import BaseAlgorithmParameters


class AsIsAlgorithmParams(BaseAlgorithmParameters):
    def __init__(self, name: str = "As is") -> None:
        super().__init__(name=name)

    def validate(self):
        pass


def as_is_algorithm(
    data: DataSource,
    parameters: AsIsAlgorithmParams,
    set_progress: Callable[[float], None],
) -> ScenarioResult:
    sleep(0.5)

    set_progress(1)
    return ScenarioResult(data_id=data.id)  # placeholder


as_is_algorithm_template = AlgorithmTemplate(
    name="As is",
    param_type=AsIsAlgorithmParams,
    main_method_template=as_is_algorithm,
)
