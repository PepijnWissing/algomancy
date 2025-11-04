import random

from algomancy.scenarioengine import (
    KpiType,
    ImprovementDirection,
    KpiTemplate,
    ScenarioResult,
)
from algomancy.scenarioengine.unit import QUANTITIES, BaseMeasurement


def create_utilization_template():
    def utilization_calculation(result: ScenarioResult) -> float:
        return 50 * (1 + 0.5 * random.random())  # placeholder

    percent = QUANTITIES["percentage"]
    percent_percent = BaseMeasurement(percent["%"], min_digits=1, max_digits=3, decimals=1)

    return KpiTemplate(
        name="Utilization",
        type=KpiType.PERCENT,
        better_when=ImprovementDirection.HIGHER,
        callback=utilization_calculation,
        measurement_base=percent_percent,
    )


utilization_template = create_utilization_template()