import random

from algomancy.scenarioengine import (
    KpiType,
    ImprovementDirection,
    KpiTemplate,
    ScenarioResult,
    UnitOfMeasurement,
)


def throughput_calculation(result: ScenarioResult) -> float:
    return 100 * (1 + 0.5 * random.random())  # placeholder


throughput_template = KpiTemplate(
    name="Throughput",
    type=KpiType.NUMERIC,
    better_when=ImprovementDirection.HIGHER,
    callback=throughput_calculation,
    UOM=UnitOfMeasurement.KG,
)
