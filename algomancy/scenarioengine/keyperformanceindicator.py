from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import Dict, List, TypeVar

from algomancy.scenarioengine.result import BASE_RESULT_BOUND
from algomancy.scenarioengine.unit import BaseMeasurement, Measurement, Unit


class ImprovementDirection(StrEnum):
    HIGHER = auto()
    LOWER = auto()
    AT_LEAST = auto()
    AT_MOST = auto()


class KpiError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class BaseKPI(ABC):
    def __init__(
            self,
            name: str,
            better_when: ImprovementDirection,
            base_measurement: BaseMeasurement,
            threshold: float | None = None,
    ) -> None:
        self._name = name
        self._better_when = better_when
        self._measurement = Measurement(base_measurement)
        self._threshold = Measurement(base_measurement, threshold) if threshold else None

    def __str__(self):
        self.pretty()

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

    @property
    def is_binary_kpi(self) -> bool:
        return self._better_when in [ImprovementDirection.AT_MOST, ImprovementDirection.AT_LEAST]

    @property
    def success(self) -> bool:
        # Check the validity of the call
        if not self.is_binary_kpi:
            raise ValueError(f"KPI success is not defined for {self.name}")
        if self._threshold is None:
            raise ValueError(f"KPI threshold is not defined for {self.name}")

        # Compare with threshold and return
        if self._better_when == ImprovementDirection.AT_MOST:
            return self._measurement.value <= self._threshold.value
        return self._measurement.value >= self._threshold.value

    @value.setter
    def value(self, value: float):
        self._measurement.value = value

    def get_threshold_str(self, unit: Unit | None = None) -> str:
        if unit:
            return self._threshold.scale_to_unit(unit).to_string()
        else:
            return self._threshold.pretty()

    def pretty(self, unit: Unit | None = None) -> str:
        if self.is_binary_kpi:
            return "✓" if self.success else "✗"
        return self.details(unit)

    def get_pretty_unit(self) -> Unit:
        return self._measurement.scale().unit

    def details(self, unit: Unit | None = None) -> str | None:
        if unit:
            return self._measurement.scale_to_unit(unit).to_string()
        else:
            return self._measurement.pretty()

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
            "value": self.value,
            "threshold": self._threshold,
        }


BASE_KPI = TypeVar("BASE_KPI", bound=BaseKPI)

