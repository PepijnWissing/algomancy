import random

from algomancy.scenarioengine import (
    ImprovementDirection,
    ScenarioResult,
)
from algomancy.scenarioengine.keyperformanceindicator import BaseKPI
from algomancy.scenarioengine.unit import QUANTITIES, BaseMeasurement


class DelayKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            name="Average Delay",
            better_when=ImprovementDirection.LOWER,
            base_measurement=BaseMeasurement(QUANTITIES["time"]["s"], min_digits=1, max_digits=3, decimals=1),
        )

    def compute(self, result: ScenarioResult) -> float:
        return 1000 * (1 + 0.5 * random.random())
