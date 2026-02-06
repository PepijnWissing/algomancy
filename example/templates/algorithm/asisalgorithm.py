from time import sleep

from algomancy_data import DataSource
from algomancy_scenario import (
    ScenarioResult,
    BaseAlgorithm,
    BaseParameterSet,
)


class AsIsAlgorithmParams(BaseParameterSet):
    def __init__(self, name: str = "As is") -> None:
        super().__init__(name=name)

    def validate(self):
        pass


class AsIsAlgorithm(BaseAlgorithm):
    def __init__(self, params: AsIsAlgorithmParams):
        super().__init__("As is", params)

    @staticmethod
    def initialize_parameters() -> AsIsAlgorithmParams:
        return AsIsAlgorithmParams()

    def run(self, data: DataSource) -> ScenarioResult:
        sleep(0.5)
        self.set_progress(100)
        return ScenarioResult(data_id=data.id)
