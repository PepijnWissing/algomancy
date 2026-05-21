from abc import ABC, abstractmethod
from enum import StrEnum, auto
from typing import TypeVar

from .result import BASE_RESULT_BOUND
from algomancy_utils.unit import BaseMeasurement, Measurement, Unit

"""
Key Performance Indicator (KPI) framework for scenario evaluation.

This module defines the foundational classes and enums used to define, compute,
and present KPIs within the Algomancy framework. It integrates with the
`algomancy_utils.unit` system to provide smart, unit-aware formatting for
performance metrics.

Core concepts:
    - **BaseKPI**: An abstract base class for all KPIs. It handles the metadata
      (name, improvement direction), unit scaling, and threshold comparisons.
    - **ImprovementDirection**: An enum defining what "better" means for a given
      metric (e.g., HIGHER is better for throughput, LOWER is better for latency).
    - **Binary vs. Continuous KPIs**: KPIs can be simple numeric trackers (continuous)
      or they can have a threshold (binary), where they are either "successful"
      or "failed" based on whether they met the threshold.

Why this exists:
    Scenario results often contain raw data that needs to be distilled into
    meaningful metrics. This module provides a consistent way to define these
    metrics, automatically handle their units, and determine if they meet
    predefined success criteria, making it easy to generate summary reports.

Quick start:
    1. Define a concrete KPI class by inheriting from `BaseKPI` and implementing
       the `compute` method.
    2. Instantiate the KPI with a name, improvement direction, and base unit.
    3. Call `compute_and_check(result)` to populate the KPI value from scenario results.
    4. Use `pretty()` to get a human-readable string of the result.

Example:
    >>> from algomancy_scenario.keyperformanceindicator import BaseKPI, ImprovementDirection
    >>> from algomancy_utils.unit import QUANTITIES, BaseMeasurement
    >>>
    >>> class ThroughputKPI(BaseKPI):
    ...     def compute(self, result):
    ...         # Logic to extract throughput from result
    ...         return 1250.5
    ...
    >>> time = QUANTITIES["time"]
    >>> # Expect at least 1000 items per second
    >>> kpi = ThroughputKPI(
    ...     "System Throughput",
    ...     ImprovementDirection.AT_LEAST,
    ...     BaseMeasurement(time["s"]),
    ...     threshold=1000.0
    ... )
    >>> kpi.compute_and_check(some_result_object)
    >>> print(kpi.pretty())
    ✓
    >>> print(kpi.details())
    1.25 ks
"""


class ImprovementDirection(StrEnum):
    """
    Defines the direction of improvement or success criteria for a KPI.

    Members:

    - ``HIGHER``: The KPI is better when its value is higher (e.g., Accuracy).
    - ``LOWER``: The KPI is better when its value is lower (e.g., Latency).
    - ``AT_LEAST``: A binary success criterion; successful if value >= threshold.
    - ``AT_MOST``: A binary success criterion; successful if value <= threshold.
    """

    HIGHER = auto()
    LOWER = auto()
    AT_LEAST = auto()
    AT_MOST = auto()


class KpiError(Exception):
    """
    Exception raised for errors during KPI computation or validation.

    Args:
        message: Explanation of the error.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class BaseKPI(ABC):
    """
    Abstract base class for all Key Performance Indicators.

    A `BaseKPI` encapsulates the logic for computing a metric from scenario
    results and formatting it for display. It supports both continuous tracking
    and binary success/failure checks via thresholds.

    Args:
        name: The human-readable name of the KPI.
        better_when: The `ImprovementDirection` for this KPI.
        base_measurement: The `BaseMeasurement` defining the unit and
            formatting preferences.
        threshold: An optional numeric threshold for binary KPIs. Required if
            `better_when` is `AT_LEAST` or `AT_MOST`.

    Notes:
        - Subclasses MUST implement the `compute` method.
        - The `value` of the KPI is typically set via `compute_and_check`.
    """

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
        self._threshold = (
            Measurement(base_measurement, threshold) if threshold else None
        )

    def __str__(self):
        """
        Returns a pretty-printed string representation of the KPI.
        """
        return self.pretty()

    @property
    def measurement(self) -> Measurement:
        """
        Returns the underlying `Measurement` object for the KPI value.
        """
        return self._measurement

    @property
    def name(self) -> str:
        """
        Returns the name of the KPI.
        """
        return self._name

    @property
    def better_when(self) -> ImprovementDirection:
        """
        Returns the improvement direction of the KPI.
        """
        return self._better_when

    @property
    def value(self) -> float | None:
        """
        Returns the current numeric value of the KPI, or `None` if not yet computed.
        """
        return self._measurement.value

    @property
    def is_binary_kpi(self) -> bool:
        """
        Returns `True` if the KPI has a binary success/failure criterion.

        A KPI is binary if its `better_when` is `AT_LEAST` or `AT_MOST`.
        """
        return self._better_when in [
            ImprovementDirection.AT_MOST,
            ImprovementDirection.AT_LEAST,
        ]

    @property
    def success(self) -> bool:
        """
        Returns `True` if the KPI meets its threshold criteria.

        Returns:
            Boolean indicating success.

        Raises:
            ValueError: If the KPI is not binary or if no threshold is defined.
        """
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
        """
        Sets the numeric value of the KPI.
        """
        self._measurement.value = value

    def get_threshold_str(self, unit: Unit | None = None) -> str:
        """
        Returns a formatted string of the KPI's threshold.

        Args:
            unit: Optional unit to scale the threshold to before formatting.

        Returns:
            Formatted threshold string.
        """
        if unit:
            return str(self._threshold.scale_to_unit(unit))
        else:
            return self._threshold.pretty()

    def pretty(self, unit: Unit | None = None) -> str:
        """
        Returns a human-friendly string of the KPI result.

        For binary KPIs, returns "✓" or "✗". For continuous KPIs, returns
        the value with its unit.

        Args:
            unit: Optional unit to scale the value to.

        Returns:
            A string representation of the KPI state or value.
        """
        if self.is_binary_kpi:
            return "✓" if self.success else "✗"
        return self.details(unit)

    def get_pretty_unit(self) -> Unit:
        """
        Returns the unit that would be used for pretty-printing the current value.
        """
        return self._measurement.scale().unit

    def details(self, unit: Unit | None = None) -> str | None:
        """
        Returns a human-friendly string of the numeric KPI value and unit.

        Unlike `pretty()`, this always returns the numeric value even for
        binary KPIs.

        Args:
            unit: Optional unit to scale the value to.

        Returns:
            Formatted string of the value and unit.
        """
        if unit:
            return str(self._measurement.scale_to_unit(unit))
        else:
            return self._measurement.pretty()

    @abstractmethod
    def compute(self, result: BASE_RESULT_BOUND) -> float:
        """
        Abstract method to compute the KPI value from scenario results.

        Args:
            result: The scenario result data.

        Returns:
            The computed numeric value.
        """
        raise NotImplementedError("Abstract method")

    def compute_and_check(self, result: BASE_RESULT_BOUND) -> None:
        """
        Computes the KPI value and updates the internal state.

        This method calls `compute(result)`, validates that the returned value
        is numeric, and updates the KPI's `value`.

        Args:
            result: The scenario result data.

        Raises:
            KpiError: If computation fails or returns a non-numeric value.
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
        """
        Returns a dictionary representation of the KPI for serialization.
        """
        return {
            "name": self.name,
            "better_when": self.better_when.name,
            "basis": self._measurement.base_measurement,
            "value": self.value,
            "threshold": self._threshold,
        }


BASE_KPI = TypeVar("BASE_KPI", bound=BaseKPI)
