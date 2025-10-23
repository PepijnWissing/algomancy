import random

from algomancy.scenarioengine import (
    KpiType,
    ImprovementDirection,
    KpiTemplate,
    ScenarioResult,
)


def average_delay_calculation(result: ScenarioResult) -> float:
    return 1000 * (1 + 0.5 * random.random())  # placeholder


delay_template = KpiTemplate(
    name="Average Delay",
    type=KpiType.TIME,
    better_when=ImprovementDirection.LOWER,
    callback=average_delay_calculation,
)
