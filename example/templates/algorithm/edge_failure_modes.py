import time

from algomancy_data import DataSource
from algomancy_scenario import (
    BaseAlgorithm,
    BaseParameterSet,
    EnumParameter,
    ScenarioResult,
)

_MODES = [
    "raise_value_error",
    "raise_runtime",
    "return_none",
    "key_error_in_kpi",
    "infinite_loop_capped",
]


class FailureModeParams(BaseParameterSet):
    def __init__(self, name: str = "Failure Modes") -> None:
        super().__init__(name=name)
        self.add_parameters(
            [
                EnumParameter(name="mode", choices=_MODES),
            ]
        )

    @property
    def mode(self) -> str:
        return self._parameters["mode"].value

    def validate(self):
        pass


class _BadKpiResult(ScenarioResult):
    """Used by key_error_in_kpi mode: triggers a KeyError when KPIs access it."""

    def to_dict(self):
        base = super().to_dict()
        base["trigger_key_error"] = True
        return base


class FailureModesAlgorithm(BaseAlgorithm):
    """Exercises all documented failure modes for error-surfacing tests.

    Modes:
    - raise_value_error: raises ValueError immediately
    - raise_runtime: raises RuntimeError immediately
    - return_none: returns None instead of ScenarioResult (invalid)
    - key_error_in_kpi: returns a special result that causes KPIs to raise KeyError
    - infinite_loop_capped: loops for 5 s then returns normally (simulates a slow/hung algo)
    """

    def __init__(self, params: FailureModeParams) -> None:
        super().__init__("Failure Modes", params)

    @staticmethod
    def initialize_parameters() -> FailureModeParams:
        return FailureModeParams()

    def run(self, data: DataSource) -> ScenarioResult:
        mode = self.params.mode

        if mode == "raise_value_error":
            raise ValueError("Intentional ValueError from FailureModesAlgorithm")

        if mode == "raise_runtime":
            raise RuntimeError("Intentional RuntimeError from FailureModesAlgorithm")

        if mode == "return_none":
            return None  # type: ignore[return-value]

        if mode == "key_error_in_kpi":
            self.set_progress(100)
            return _BadKpiResult(data_id=data.id)

        if mode == "infinite_loop_capped":
            deadline = time.monotonic() + 5
            i = 0
            while time.monotonic() < deadline:
                i += 1
            self.set_progress(100)
            return ScenarioResult(data_id=data.id)

        raise ValueError(f"Unknown mode: {mode}")
