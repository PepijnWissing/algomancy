import threading
import time

from algomancy_data import DataSource
from algomancy_scenario import (
    BaseAlgorithm,
    BaseParameterSet,
    IntegerParameter,
    ScenarioResult,
)


class LongProgressParams(BaseParameterSet):
    def __init__(self, name: str = "Long Progress") -> None:
        super().__init__(name=name)
        self.add_parameters(
            [
                IntegerParameter(name="seconds", minvalue=1, maxvalue=120, default=10),
            ]
        )

    @property
    def seconds(self) -> int:
        return self._parameters["seconds"].value

    def validate(self):
        pass


class LongProgressAlgorithm(BaseAlgorithm):
    """Long-running algorithm that updates progress once per second.

    Uses a cooperative cancel event so an external thread can interrupt it
    cleanly when the scenario is deleted or the process receives SIGINT.
    """

    def __init__(self, params: LongProgressParams) -> None:
        super().__init__("Long Progress", params)
        self._cancel_event: threading.Event = threading.Event()

    @staticmethod
    def initialize_parameters() -> LongProgressParams:
        return LongProgressParams()

    def cancel(self) -> None:
        self._cancel_event.set()

    def run(self, data: DataSource) -> ScenarioResult:
        p: LongProgressParams = self.params
        total = p.seconds

        for elapsed in range(total):
            if self._cancel_event.is_set():
                break
            time.sleep(1)
            self.set_progress(int(100 * (elapsed + 1) / total))

        return ScenarioResult(data_id=data.id)
