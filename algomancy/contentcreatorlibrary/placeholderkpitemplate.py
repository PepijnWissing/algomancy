import random

from algomancy.scenarioengine import (
    ImprovementDirection,
    KpiTemplate,
    ScenarioResult,
)
from algomancy.scenarioengine.unit import QUANTITIES


def placeholder_calculation_function(result: ScenarioResult) -> float:
    return 1000 * (1 + 0.5 * random.random())  # placeholder


mass_kg = QUANTITIES["mass"]["kg"]

placeholder_kpi_template = KpiTemplate(
    name="Placeholder KPI",
    better_when=ImprovementDirection.LOWER,
    callback=placeholder_calculation_function,
    measurement_base=mass_kg,
)
