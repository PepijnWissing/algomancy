import random

from algomancy.scenarioengine import (
    KpiType,
    ImprovementDirection,
    KpiTemplate,
    ScenarioResult,
)
from algomancy.scenarioengine.unit import QUANTITIES, BaseMeasurement


def create_delay_template():
    def average_delay_calculation(result: ScenarioResult) -> float:
        return 1000 * (1 + 0.5 * random.random())  # placeholder

    time = QUANTITIES["time"]
    time_s = BaseMeasurement(time["s"], min_digits=1, max_digits=3, decimals=1)

    return KpiTemplate(
        name="Average Delay",
        type=KpiType.TIME,
        better_when=ImprovementDirection.LOWER,
        callback=average_delay_calculation,
        measurement_base=time_s,
    )


delay_template = create_delay_template()
