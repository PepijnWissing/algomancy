from time import sleep

from data_processing import DataSource
from scenario import (
    BaseAlgorithmParameters,
    ScenarioResult,
)
from scenario.basealgorithm import BaseAlgorithm


class PlaceholderParams(BaseAlgorithmParameters):
    def __init__(self, name: str = "As is") -> None:
        super().__init__(name=name)

    def validate(self):
        pass


class AsIsAlgorithm(BaseAlgorithm):
    def __init__(self, params: PlaceholderParams):
        super().__init__("As is", params)

    @staticmethod
    def initialize_parameters() -> PlaceholderParams:
        return PlaceholderParams()

    def run(self, data: DataSource) -> ScenarioResult:
        sleep(0.5)
        self.set_progress(100)
        return ScenarioResult(data_id=data.id)
