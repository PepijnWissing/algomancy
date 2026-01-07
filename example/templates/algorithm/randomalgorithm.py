from time import sleep

from algomancy_data import DataSource
from algomancy_scenario import (
    ScenarioResult,
    BaseAlgorithm,
    BaseParameterSet,
    FloatParameter,
)


class RandomParameterSet(BaseParameterSet):
    def __init__(
        self,
        name: str = "Random",
    ):
        super().__init__(name=name)
        self.add_parameters(
            [FloatParameter(name="variance", minvalue=FloatParameter.EPSILON)]
        )

    @property
    def variance(self) -> float:
        return self._parameters["variance"].value

    def validate(self):
        pass


class RandomAlgorithm(BaseAlgorithm):
    def __init__(
        self,
        params: RandomParameterSet,
    ):
        super().__init__(name="Random", params=params)

    @staticmethod
    def initialize_parameters() -> RandomParameterSet:
        return RandomParameterSet()

    def run(self, data: DataSource) -> ScenarioResult:
        sleep(self.params.variance)

        self.set_progress(100)
        return ScenarioResult(data_id=data.id)
