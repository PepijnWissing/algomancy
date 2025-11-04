import random

from algomancy.scenarioengine import (
    KpiType,
    ImprovementDirection,
    KpiTemplate,
    ScenarioResult,
)
from algomancy.scenarioengine.unit import QUANTITIES, BaseMeasurement


def create_throughput_template():
    def throughput_calculation(result: ScenarioResult) -> float:
        return 100 * (1 + 0.5 * random.random())  # placeholder

    mass = QUANTITIES["mass"]
    mass_kg = BaseMeasurement(mass["kg"], min_digits=1, max_digits=3, decimals=2)

    return KpiTemplate(
        name="Throughput",
        type=KpiType.NUMERIC,
        better_when=ImprovementDirection.HIGHER,
        callback=throughput_calculation,
        measurement_base=mass_kg,
    )


throughput_template = create_throughput_template()