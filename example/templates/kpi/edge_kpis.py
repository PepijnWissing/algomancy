"""Edge-case KPIs for error-surfacing and boundary-condition tests.

These KPIs are registered alongside the production ones so that any scenario
running with them exercises serialisation, comparison, and display edge paths.
"""

from algomancy_scenario import BaseKPI, ImprovementDirection, ScenarioResult
from algomancy_utils import QUANTITIES, BaseMeasurement


def _count_measurement() -> BaseMeasurement:
    return BaseMeasurement(
        QUANTITIES["count"][""], min_digits=1, max_digits=6, decimals=2
    )


class NaNKPI(BaseKPI):
    """Returns float('nan') — exercises JSON serialisation and comparison sorting."""

    def __init__(self) -> None:
        super().__init__(
            name="NaN KPI",
            better_when=ImprovementDirection.LOWER,
            base_measurement=_count_measurement(),
        )

    def compute(self, result: ScenarioResult) -> float:
        return float("nan")


class InfKPI(BaseKPI):
    """Returns float('inf') — exercises upper-bound display logic."""

    def __init__(self) -> None:
        super().__init__(
            name="Inf KPI",
            better_when=ImprovementDirection.LOWER,
            base_measurement=_count_measurement(),
        )

    def compute(self, result: ScenarioResult) -> float:
        return float("inf")


class NegativeKPI(BaseKPI):
    """Returns a negative value for a HIGHER-better KPI — exercises sign handling."""

    def __init__(self) -> None:
        super().__init__(
            name="Negative KPI",
            better_when=ImprovementDirection.HIGHER,
            base_measurement=_count_measurement(),
        )

    def compute(self, result: ScenarioResult) -> float:
        return -42.0


class ZeroAtThresholdKPI(BaseKPI):
    """Threshold AT_MOST=1e-6; returns exactly 0 — tests boundary inclusivity.

    Note: threshold=0.0 would be treated as falsy by the framework (known bug),
    so we use 1e-6 as an effectively-zero threshold.
    """

    THRESHOLD = 1e-6

    def __init__(self) -> None:
        super().__init__(
            name="Zero-at-threshold KPI",
            better_when=ImprovementDirection.AT_MOST,
            base_measurement=_count_measurement(),
            threshold=ZeroAtThresholdKPI.THRESHOLD,
        )

    def compute(self, result: ScenarioResult) -> float:
        return 0.0


class RaisingKPI(BaseKPI):
    """Raises in compute() — verifies that other KPIs still run when one fails."""

    def __init__(self) -> None:
        super().__init__(
            name="Raising KPI",
            better_when=ImprovementDirection.LOWER,
            base_measurement=_count_measurement(),
        )

    def compute(self, result: ScenarioResult) -> float:
        raise RuntimeError("Intentional error from RaisingKPI")
