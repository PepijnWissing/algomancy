from dataclasses import dataclass
from typing import Callable, TypeVar, Generic

from algomancy.scenarioengine.algorithmparameters import AlgorithmParameters
from algomancy.dataengine.datasource import DataSource
from algomancy.scenarioengine.progresstracker import ProgressTracker
from algomancy.scenarioengine.result import ScenarioResult

P = TypeVar('P', bound=AlgorithmParameters)


@dataclass
class AlgorithmTemplate(Generic[P]):
    name: str
    param_type: type(P)
    main_method_template: Callable[[DataSource, P, Callable[[float], None]], ScenarioResult]


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
        def _bound_main(data: DataSource):
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

    def run(self, data: DataSource) -> ScenarioResult:
        return self._main_method(data)

    def to_dict(self):
        return {
            "name": self._template.name,
            "parameters": self._params.serialize(),
        }
