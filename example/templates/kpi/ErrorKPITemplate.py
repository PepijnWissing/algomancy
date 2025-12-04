import random

from src.algomancy import (
    ImprovementDirection,
    ScenarioResult,
)
from algomancy.scenarioengine import BaseKPI
from algomancy.scenarioengine import QUANTITIES, BaseMeasurement


# def create_error_template():
#     def error_rate_calculation(result: ScenarioResult) -> float:
#         return 0.1 * (1 + 0.5 * random.random())  # placeholder
#
#     default = QUANTITIES["default"]
#     default_unit = BaseMeasurement(default["unit"], min_digits=1, max_digits=3, decimals=1)
#
#     return KpiTemplate(
#         name="Error Rate",
#         better_when=ImprovementDirection.LOWER,
#         callback=error_rate_calculation,
#         measurement_base=default_unit,
#     )
#
#
# error_template = create_error_template()


class ErrorKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            "Error Rate",
            ImprovementDirection.LOWER,
            BaseMeasurement(QUANTITIES["default"]["unit"], min_digits=1, max_digits=3, decimals=1)
        )

    def compute(self, result: ScenarioResult) -> float:
        return 0.1 * (1 + 0.5 * random.random())
