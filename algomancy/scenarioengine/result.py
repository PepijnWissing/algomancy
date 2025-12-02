from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar


class BaseScenarioResult(ABC):
    def __init__(self, data_id: str):
        self.data_id = data_id
        self.completed_at = datetime.now()

    @abstractmethod
    def to_dict(self):
        raise NotImplementedError('Abstract method')


BASE_RESULT_BOUND = TypeVar("BASE_RESULT_BOUND", bound=BaseScenarioResult)


class ScenarioResult(BaseScenarioResult):
    def __init__(self, data_id: str):
        super().__init__(data_id)

    def to_dict(self):
        return {
            "scenario_id": self.data_id,
            "completed_at": self.completed_at,
        }
