import random

from algomancy.scenarioengine import (
    KpiType,
    ImprovementDirection,
    KpiTemplate,
    ScenarioResult,
)


def utilization_calculation(result: ScenarioResult) -> float:
    return 50 * (1 + 0.5 * random.random())  # placeholder


utilization_template = KpiTemplate(
    name="Utilization",
    type=KpiType.PERCENT,
    better_when=ImprovementDirection.HIGHER,
    callback=utilization_calculation,
)
