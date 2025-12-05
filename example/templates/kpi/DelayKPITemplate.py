import random

from algomancy_scenario import (
    ImprovementDirection,
    ScenarioResult,
    BaseKPI,
)
from algomancy_utils import QUANTITIES, BaseMeasurement


class DelayKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            name="Average Delay",
            better_when=ImprovementDirection.AT_MOST,
            base_measurement=BaseMeasurement(
                QUANTITIES["time"]["s"], min_digits=1, max_digits=3, decimals=1
            ),
            threshold=1200,
        )

    def compute(self, result: ScenarioResult) -> float:
        return 1000 * (1 + 0.5 * random.random())
