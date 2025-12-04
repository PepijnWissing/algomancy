from dataclasses import dataclass
from typing import Callable, TypeVar, Generic

from algomancy.scenarioengine.algorithmparameters import AlgorithmParameters
from algomancy.dataengine import BASE_DATA_BOUND
from algomancy.scenarioengine.progresstracker import ProgressTracker
from algomancy.scenarioengine.result import BASE_RESULT_BOUND

ALGORITHM_PARAMETER = TypeVar("ALGORITHM_PARAMETER", bound=AlgorithmParameters)


@dataclass
class AlgorithmTemplate(Generic[ALGORITHM_PARAMETER]):
    name: str
    param_type: type(ALGORITHM_PARAMETER)
    main_method_template: Callable[
        [BASE_DATA_BOUND, ALGORITHM_PARAMETER, Callable[[float], None]],
        BASE_RESULT_BOUND,
    ]


class Algorithm:
    def __init__(
        self,
        template: AlgorithmTemplate,
        params: AlgorithmParameters,
    ) -> None:
        self._description = str(params.serialize())
        self._template = template
        self._params = params
        self._progress_tracker = ProgressTracker()

        # Bind parameters positionally to be independent of the parameter name used in algorithm functions
        def _bound_main(data: BASE_DATA_BOUND):
            return template.main_method_template(
                data,
                params,
                self._progress_tracker.set_progress,
            )

        self._main_method = _bound_main

    def __str__(self):
        return self._description

    @property
    def name(self):
        return self._template.name

    @property
    def params(self):
        return self._params

    @property
    def description(self):
        return self._description

    @property
    def get_progress(self) -> float:
        return self._progress_tracker.get_progress()

    def run(self, data: BASE_DATA_BOUND) -> BASE_RESULT_BOUND:
        return self._main_method(data)

    def to_dict(self):
        return {
            "name": self._template.name,
            "parameters": self._params.serialize(),
        }
