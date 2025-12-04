"""
scenario.py - Scenario Management

This module defines the Scenario class and related enums for managing simulation scenarios.
It provides functionality for creating, processing, and analyzing scenarios with different
algorithms and parameters.
"""

import uuid
from enum import StrEnum, auto
from typing import Dict, Generic

from algomancy.dashboardlogger import Logger
from algomancy.dataengine import BASE_DATA_BOUND
from .basealgorithm import ALGORITHM
from .keyperformanceindicator import BASE_KPI


class ScenarioStatus(StrEnum):
    """
    Constants representing the possible states of a scenario.
    """

    CREATED = auto()
    QUEUED = auto()
    PROCESSING = auto()
    COMPLETE = auto()
    FAILED = auto()


class Scenario(Generic[BASE_KPI]):
    """
    Represents a scenario with input data, algorithm, and results.

    A scenario encapsulates the input data, processing algorithm, parameters,
    and results of a simulation or analysis run.
    """

    def __init__(
        self,
        tag: str,
        input_data: BASE_DATA_BOUND,
        kpis: Dict[str, BASE_KPI],
        algorithm: ALGORITHM,
        provided_id: str = None,
    ):
        """
        Initializes a new Scenario with the specified parameters.

        Args:
            tag (str): A user-defined label for the scenario
            input_data (BASE_DATA_BOUND): The data source to use for the scenario. Derived from BaseDataSource.
            kpis: (Dict[str, KPI]): A dictionary of KPIs to compute for the scenario
            algorithm (str): The algorithm to use for processing
            provided_id (str): An optional unique identifier for the scenario. If not provided, a UUID will be generated.
        """
        self.id = provided_id if provided_id else str(uuid.uuid4())
        self.tag = tag  # user-defined label
        self._input_data = input_data  # includes raw or preprocessed data
        self._kpis = kpis
        self._algorithm = algorithm

        self.status = ScenarioStatus.CREATED
        self.result = None

    def __str__(self):
        return f"Scenario: {self.tag} ({str(self._algorithm)}"

    @property
    def input_data_key(self) -> str:
        return self._input_data.name

    @property
    def data_source(self) -> BASE_DATA_BOUND:
        return self._input_data

    @property
    def algorithm_description(self) -> str:
        return self._algorithm.description

    @property
    def kpis(self) -> Dict[str, BASE_KPI]:
        return self._kpis

    @property
    def progress(self) -> float:
        return self._algorithm.get_progress

    def set_queued(self):
        self.status = ScenarioStatus.QUEUED

    def process(self, logger: Logger = None):
        """
        Processes the scenario using the specified algorithm.

        This method runs the algorithm in the background, updates the scenario status,
        and computes KPIs based on the results.

        Exceptions during processing are caught, and the scenario status is set to FAILED.
        """
        if not (
            self.status == ScenarioStatus.CREATED
            or self.status == ScenarioStatus.QUEUED
        ):
            return

        self.status = ScenarioStatus.PROCESSING
        try:
            self.result = self._algorithm.run(self._input_data)
            self.compute_kpis()
            self.status = ScenarioStatus.COMPLETE
        except Exception as e:
            self.status = ScenarioStatus.FAILED
            if logger:
                logger.error(f"Scenario '{self.tag}' failed to process: {str(e)}")
            self.result = {"error": str(e)}

    def cancel(self, logger: Logger = None):
        if logger:
            logger.warning(f"Not Yet Implemented: Scenario {self.tag} cancel")
        pass

    def refresh(self, logger: Logger = None):
        self.status = ScenarioStatus.CREATED
        self.result = None
        if logger:
            logger.log(f"Refreshed scenario {self.tag}")

    def compute_kpis(self):
        """
        Calculates key performance indicators (KPIs) for the given scenario.

        Raises:
            ValueError: If there is no result available for the scenario.
            KpiError: If one or more KPI calculations fail.
        """
        if not self.result:
            raise ValueError("Scenario result is not available")

        for kpi in self._kpis.values():
            kpi.compute_and_check(self.result)

    def to_dict(self) -> dict:
        """
        Converts the attributes of the instance into a dictionary representation.

        This method creates a dictionary containing the key attributes of the instance by
        converting them into a serializable format. Attributes that have a `to_dict` method
        are recursively processed. If some attributes do not exist or cannot be accessed,
        they may return `None`.

        Returns:
            dict: A dictionary representation of the instance's attributes.
        """
        return {
            "id": self.id,
            "tag": self.tag,
            "input_data_id": self._input_data.id
            if hasattr(self._input_data, "id")
            else None,
            "kpis": {
                k: v.to_dict() if hasattr(v, "to_dict") else v
                for k, v in self._kpis.items()
            },
            "algorithm": self._algorithm.to_dict()
            if hasattr(self._algorithm, "to_dict")
            else self._algorithm,
            "status": self.status,
            "result": self.result.to_dict()
            if hasattr(self.result, "to_dict")
            else self.result,
        }

    def is_completed(self) -> bool:
        return self.status == ScenarioStatus.COMPLETE
