from abc import ABC, abstractmethod
from typing import Type, TypeVar

from algomancy_data import BASEDATASOURCE
from algomancy_utils import Logger
from .result import BASE_RESULT_BOUND, BaseScenarioResult, ScenarioResult
from algomancy_utils.baseparameterset import (
    BASE_PARAMS_BOUND,
    BaseParameterSet,
    EmptyParameters,
)


class BaseAlgorithm(ABC):
    # Class returned by ``run``. Override on subclasses whose ``run`` returns a
    # custom ``BaseScenarioResult`` subclass; the database repository uses this
    # to rehydrate persisted results into their original type.
    result_class: Type[BaseScenarioResult] = ScenarioResult

    def __init__(self, name: str, params: BASE_PARAMS_BOUND):
        self._name: str = name
        self.description = str(params.serialize())
        self._params: BASE_PARAMS_BOUND = params
        self._data_params: BaseParameterSet = EmptyParameters()
        self._progress: float = 0
        self._logger: Logger | None = None  # set by factory after initialization

    def __str__(self):
        return f"{self.name} [{self._progress:.0f}%]: {self.description}"

    @property
    def params(self):
        return self._params

    @property
    def data_params(self) -> BaseParameterSet:
        """The data parameters declared by the input data source for the current run.

        Defaults to ``EmptyParameters()``. The scenario calls
        ``set_data_params`` with the user-supplied values before ``run()``.
        """
        return self._data_params

    def set_data_params(self, data_params: BaseParameterSet) -> None:
        self._data_params = (
            data_params if data_params is not None else EmptyParameters()
        )

    @property
    def get_progress(self) -> float:
        return self._progress

    @property
    def name(self) -> str:
        return self._name

    def set_logger(self, logger: Logger) -> None:
        self._logger = logger

    def set_progress(self, progress: float):
        assert 0 <= progress <= 100, "progress must be between 0 and 100"
        self._progress = progress

    def is_complete(self):
        return self._progress == 100

    def to_dict(self):
        return {
            "name": self.name,
            "parameters": self._params.serialize(),
        }

    def healthcheck(self) -> bool:
        return True

    @staticmethod
    @abstractmethod
    def initialize_parameters() -> BASE_PARAMS_BOUND:
        """
        Initializes parameters for the derived Algorithm, which is necessary
        for the GUI logic. It should simply return a default object of the
        associated AlgorithmParameters class.

        Example:
            >>> @staticmethod
            >>> def initialize_parameters() -> ExampleAlgorithmParams:
            ...    return ExampleAlgorithmParams()

        Raises:
            NotImplementedError: If the method is not overridden.

        Returns:
            BASE_PARAMS_BOUND: The initialized set of parameters, derived
                               from the BaseAlgorithmParameters class.
        """
        raise NotImplementedError("Abstract method")

    @abstractmethod
    def run(self, data: BASEDATASOURCE) -> BASE_RESULT_BOUND:
        raise NotImplementedError("Abstract method")


ALGORITHM: TypeVar = TypeVar("ALGORITHM", bound=BaseAlgorithm)
