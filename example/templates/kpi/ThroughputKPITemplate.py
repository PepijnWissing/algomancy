import random

from src.algomancy import (
    ImprovementDirection,
    ScenarioResult,
)
from algomancy.scenarioengine import BaseKPI
from algomancy.scenarioengine import QUANTITIES, BaseMeasurement


class ThroughputKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            "Throughput",
            ImprovementDirection.HIGHER,
            BaseMeasurement(
                QUANTITIES["mass"]["kg"], min_digits=1, max_digits=3, decimals=2
            ),
        )

    def compute(self, result: ScenarioResult) -> float:
        return 100 * (1 + 0.5 * random.random())
