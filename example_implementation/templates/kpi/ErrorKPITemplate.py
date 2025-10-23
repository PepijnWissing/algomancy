import random

from algomancy.scenarioengine import (
    KpiType,
    ImprovementDirection,
    KpiTemplate,
    ScenarioResult,
)


def error_rate_calculation(result: ScenarioResult) -> float:
    return 0.1 * (1 + 0.5 * random.random())  # placeholder


error_template = KpiTemplate(
    name="Error Rate",
    type=KpiType.RATIO,
    better_when=ImprovementDirection.LOWER,
    callback=error_rate_calculation,
)
