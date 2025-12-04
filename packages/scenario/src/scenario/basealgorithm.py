from abc import ABC, abstractmethod
from typing import TypeVar

from data_processing import BASE_DATA_BOUND
from .result import BASE_RESULT_BOUND
from .basealgorithmparameters import BASE_PARAMS_BOUND


class BaseAlgorithm(ABC):
    def __init__(self, name: str, params: BASE_PARAMS_BOUND):
        self._name: str = name
        self.description = str(params.serialize())
        self._params: BASE_PARAMS_BOUND = params
        self._progress: float = 0

    def __str__(self):
        return f"{self.name} [{self._progress:.0f}%]: {self.description}"

    @property
    def params(self):
        return self._params

    @property
    def get_progress(self) -> float:
        return self._progress

    @property
    def name(self) -> str:
        return self._name

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
            @staticmethod
            def initialize_parameters() -> ExampleAlgorithmParams:
                return ExampleAlgorithmParams()

        Raises:
            NotImplementedError: If the method is not overridden.

        Returns:
            BASE_PARAMS_BOUND: The initialized set of parameters, derived
                               from the BaseAlgorithmParameters class.
        """
        raise NotImplementedError("Abstract method")

    @abstractmethod
    def run(self, data: BASE_DATA_BOUND) -> BASE_RESULT_BOUND:
        raise NotImplementedError("Abstract method")


ALGORITHM: TypeVar = TypeVar("ALGORITHM", bound=BaseAlgorithm)
