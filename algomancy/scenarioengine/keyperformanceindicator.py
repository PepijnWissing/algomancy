from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar

from algomancy.scenarioengine.enumtypes import ImprovementDirection
from algomancy.scenarioengine.result import BASE_RESULT_BOUND
from algomancy.scenarioengine.unit import BaseMeasurement, Measurement


class KpiError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


# todo KpiType: at least value / at most value

class BaseKPI(ABC):
    def __init__(
            self,
            name: str,
            better_when: ImprovementDirection,
            base_measurement: BaseMeasurement,
    ) -> None:
        self._name = name
        self._better_when = better_when
        self._measurement = Measurement(base_measurement)

    @property
    def measurement(self) -> Measurement:
        return self._measurement

    @property
    def name(self) -> str:
        return self._name

    @property
    def better_when(self) -> ImprovementDirection:
        return self._better_when

    @property
    def value(self) -> float | None:
        return self._measurement.value

    @value.setter
    def value(self, value: float):
        self._measurement.value = value

    def __str__(self):
        self._measurement.pretty()

    @abstractmethod
    def compute(self, result: BASE_RESULT_BOUND) -> float:
        raise NotImplementedError("Abstract method")

    def compute_and_check(self, result: BASE_RESULT_BOUND) -> None:
        """
        Computes a key performance indicator (KPI) value using the provided result data
        and a callback function.

        This method attempts to compute the KPI by invoking a specified callback with
        the result data. If an exception occurs during computation, it logs an error
        message indicating the KPI name and raises a KpiError to indicate failure.

        :param result: The result data of the type required for KPI computation.
        :type result: Derived from BaseScenarioResult
        :raises KpiError: If an error occurs during the KPI computation.
        """
        try:
            value = self.compute(result)
            if not isinstance(value, (int, float)):
                raise KpiError("KPI callback must return a numeric value.")
            self.value = value
        except Exception as e:
            print(f"Error computing KPI {self.name}: {e}")
            raise KpiError(f"Error computing KPI {self.name}")

    def to_dict(self):
        return {
            "name": self.name,
            "better_when": self.better_when.name,
            "basis": self._measurement.base_measurement,
            "value": self.value
        }


BASE_KPI = TypeVar("BASE_KPI", bound=BaseKPI)

