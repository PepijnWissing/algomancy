from algomancy_data import DataSource
from algomancy_scenario import BaseAlgorithm, BaseParameterSet, ScenarioResult


class InstantParams(BaseParameterSet):
    def __init__(self, name: str = "Instant") -> None:
        super().__init__(name=name)

    def validate(self):
        pass


class InstantAlgorithm(BaseAlgorithm):
    """Completes within milliseconds and never calls set_progress explicitly.

    Exercises the 'completed before first poll' path in the status endpoint.
    """

    def __init__(self, params: InstantParams) -> None:
        super().__init__("Instant", params)

    @staticmethod
    def initialize_parameters() -> InstantParams:
        return InstantParams()

    def run(self, data: DataSource) -> ScenarioResult:
        return ScenarioResult(data_id=data.id)
