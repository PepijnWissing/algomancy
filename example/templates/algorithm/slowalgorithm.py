from time import sleep

from algomancy_data import DataSource
from algomancy_scenario import (
    BaseParameterSet,
    ScenarioResult,
    BaseAlgorithm,
    IntegerParameter,
)


class SlowAlgorithmParams(BaseParameterSet):
    def __init__(self, name: str = "Slow") -> None:
        super().__init__(name=name)

        self.add_parameters(
            [IntegerParameter(name="duration", minvalue=1, maxvalue=60)]
        )

    @property
    def duration(self) -> int:
        return int(self["duration"])

    def validate(self):
        pass


class SlowAlgorithm(BaseAlgorithm):
    def __init__(self, params: SlowAlgorithmParams) -> None:
        super().__init__(name="Slow", params=params)

    @staticmethod
    def initialize_parameters() -> SlowAlgorithmParams:
        return SlowAlgorithmParams()

    def run(self, data: DataSource) -> ScenarioResult:
        for i in range(self.params.duration):
            self.set_progress(100 * i / self.params.duration)
            sleep(1)
        self.set_progress(100)
        return ScenarioResult(data_id=data.id)
