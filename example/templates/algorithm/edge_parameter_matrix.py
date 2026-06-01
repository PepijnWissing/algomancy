"""ParameterMatrixAlgorithm — one class exercising every supported parameter type.

This is the canonical reference for parameter-type edge coverage, consolidating
what was previously scattered across batchingalgorithm.py.

Note: IntervalParameter is excluded because its default value (a datetime tuple)
is not JSON-serializable, which breaks BaseAlgorithm.__init__. This is a known
framework issue tracked separately.
"""

from algomancy_utils.baseparameterset import (
    MultiEnumParameter,
    StringParameter,
    TimeParameter,
)

from algomancy_data import DataSource
from algomancy_scenario import (
    BaseAlgorithm,
    BaseParameterSet,
    BooleanParameter,
    EnumParameter,
    FloatParameter,
    IntegerParameter,
    ScenarioResult,
)


class ParameterMatrixParams(BaseParameterSet):
    """One instance of every JSON-serializable parameter type in the framework."""

    def __init__(self, name: str = "Parameter Matrix") -> None:
        super().__init__(name=name)
        self.add_parameters(
            [
                IntegerParameter(
                    name="int_param", minvalue=0, maxvalue=1000, default=42
                ),
                FloatParameter(name="float_param", minvalue=0.0, default=3.14),
                StringParameter(name="string_param", default="hello"),
                BooleanParameter(name="bool_param", default=True),
                EnumParameter(
                    name="enum_param",
                    choices=["option_a", "option_b", "option_c"],
                ),
                MultiEnumParameter(
                    name="multi_enum_param",
                    choices=["x", "y", "z"],
                ),
                TimeParameter(name="time_param"),
            ]
        )

    def validate(self):
        if self._parameters["int_param"].value < 0:
            from algomancy_utils.baseparameterset import ParameterError

            raise ParameterError("int_param must be non-negative")


class ParameterMatrixAlgorithm(BaseAlgorithm):
    """Algorithm that exercises every parameter type — for GUI / API coverage testing."""

    def __init__(self, params: ParameterMatrixParams) -> None:
        super().__init__("Parameter Matrix", params)

    @staticmethod
    def initialize_parameters() -> ParameterMatrixParams:
        return ParameterMatrixParams()

    def run(self, data: DataSource) -> ScenarioResult:
        self.set_progress(100)
        return ScenarioResult(data_id=data.id)
