import random

from algomancy.scenarioengine import (
    ImprovementDirection,
    ScenarioResult,
)
from algomancy.scenarioengine.keyperformanceindicator import BaseKPI
from algomancy.scenarioengine.unit import QUANTITIES, BaseMeasurement


class ErrorKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            "Error Rate",
            ImprovementDirection.LOWER,
            BaseMeasurement(
                QUANTITIES["default"]["unit"], min_digits=1, max_digits=3, decimals=1
            ),
        )

    def compute(self, result: ScenarioResult) -> float:
        return 0.1 * (1 + 0.5 * random.random())
