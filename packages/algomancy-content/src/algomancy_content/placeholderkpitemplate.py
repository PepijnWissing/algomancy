import random

from scenario import (
    ImprovementDirection,
    BaseKPI,
    ScenarioResult,
)
from utils import QUANTITIES, BaseMeasurement


percent = QUANTITIES["percentage"]
percent_percent = BaseMeasurement(percent["%"], min_digits=1, max_digits=3, decimals=1)


class PlaceholderKPI(BaseKPI):
    def __init__(self):
        super().__init__("Placeholder", ImprovementDirection.HIGHER, percent_percent)

    def compute(self, result: ScenarioResult) -> float:
        return 50 * (1 + 0.5 * random.random())
