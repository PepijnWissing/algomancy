import queue
import threading
from typing import Optional

from utils.logger import Logger

from .scenario import Scenario


class ScenarioProcessor:
    """
    Manages the processing queue, runs scenarios asynchronously, and tracks status.
    """

    def __init__(self, logger: Logger | None = None):
        self.logger = logger
        self._process_queue: queue.Queue[Scenario | None] = queue.Queue()
        self._worker_thread = threading.Thread(
            target=self._process_scenarios_worker, daemon=True
        )
        self._currently_processing: Optional[Scenario] = None
        self._auto_run_scenarios = False
        self._worker_thread.start()

    # Properties
    @property
    def auto_run_scenarios(self) -> bool:
        return self._auto_run_scenarios

    @auto_run_scenarios.setter
    def auto_run_scenarios(self, value: bool):
        self._auto_run_scenarios = value

    @property
    def currently_processing(self) -> Optional[Scenario]:
        return self._currently_processing

    # Worker
    def _process_scenarios_worker(self):
        while True:
            scenario = self._process_queue.get()
            if scenario is None:
                break

            if self.logger:
                self.logger.log(f"Processing scenario '{scenario.tag}'...")
            self._currently_processing = scenario

            scenario.process(logger=self.logger)

            if self.logger:
                self.logger.log(f"Scenario '{scenario.tag}' completed.")
            self._currently_processing = None
            self._process_queue.task_done()

    # API
    def enqueue(self, scenario: Scenario):
        scenario.set_queued()
        self._process_queue.put(scenario)

    def wait_for_processing(self):
        self._process_queue.join()

    def shutdown(self):
        self._process_queue.put(None)
        self._worker_thread.join()
