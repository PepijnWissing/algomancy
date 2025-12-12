from algomancy_scenario.basealgorithmparameters import TimeParameter
from algomancy_scenario.basealgorithmparameters import IntervalParameter
from algomancy_scenario.basealgorithmparameters import MultiEnumParameter
from time import sleep

from algomancy_data import DataSource
from algomancy_scenario import (
    BaseAlgorithmParameters,
    IntegerParameter,
    EnumParameter,
    BooleanParameter,
    BaseAlgorithm,
    ScenarioResult,
)


class BatchingAlgorithmParameters(BaseAlgorithmParameters):
    def __init__(
        self,
        name: str = "Batching",
    ):
        super().__init__(name=name)

        self.add_parameters(
            [
                IntegerParameter(name="batch_size", minvalue=1),
                EnumParameter(
                    name="search_direction", choices=["depth first", "breadth first"]
                ),
                BooleanParameter(name="use_cache"),
                MultiEnumParameter(
                    "multi_test", choices=["option 1", "option 2", "option 3"]
                ),
                TimeParameter("time_test"),
                IntervalParameter(
                    "interval_test",
                ),
            ]
        )

    @property
    def batch_size(self) -> int:
        return self["batch_size"]

    @property
    def search_direction(self):
        return self["search_direction"]

    @property
    def use_cache(self):
        return self["use_cache"]

    def validate(self):
        pass


class BatchingAlgorithm(BaseAlgorithm):
    def __init__(self, params: BatchingAlgorithmParameters):
        super().__init__("Batching", params)

    @staticmethod
    def initialize_parameters() -> BatchingAlgorithmParameters:
        return BatchingAlgorithmParameters()

    def run(self, data: DataSource) -> ScenarioResult:
        sleep(self.params.batch_size)
        self.set_progress(100)
        return ScenarioResult(data_id=data.id)


# def batching_algorithm(
#     data: DataSource,
#     parameters: BatchingAlgorithmParameters,
#     set_progress: Callable[[float], None],
# ) -> ScenarioResult:
#     sleep(parameters.batch_size)
#     set_progress(1)
#     return ScenarioResult(data_id=data.id)  # placeholder
#
#
# batching_algorithm_template = AlgorithmTemplate(
#     name="Batching",
#     param_type=BatchingAlgorithmParameters,
#     main_method_template=batching_algorithm,
# )
