from time import sleep
from typing import Callable

from algomancy.dataengine import DataSource
from algomancy.scenarioengine import (
    AlgorithmTemplate,
    ScenarioResult,
)
from algomancy.scenarioengine.basealgorithmparameters import BaseAlgorithmParameters


class PlaceholderParams(BaseAlgorithmParameters):
    def __init__(self, name: str = "As is") -> None:
        super().__init__(name=name)

    def validate(self):
        pass


def placeholder_main_method(
    data: DataSource,
    parameters: PlaceholderParams,
    set_progress: Callable[[float], None],
) -> ScenarioResult:
    sleep(0.5)

    set_progress(1)
    return ScenarioResult(master_data_id=data.id)  # placeholder


placeholder_algorithm_template = AlgorithmTemplate(
    name="As is",
    param_type=PlaceholderParams,
    main_method_template=placeholder_main_method,
)
