from algomancy_scenario import BaseKPI, ImprovementDirection
from algomancy_utils import BaseMeasurement, QUANTITIES

from data_handling.result_model.result_model import ResultModel


class TotalCostsKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            "Total_costs",
            ImprovementDirection.HIGHER,
            BaseMeasurement(
                QUANTITIES["money"]["$"], min_digits=1, max_digits=3, decimals=2
            ),
        )

    def compute(self, result: ResultModel) -> float:
        total_costs = 0.0

        if result.tour is not None:
            for route in result.tour:
                total_costs += route.cost

        return total_costs
