"""Scenario result containers.

``BaseScenarioResult`` mirrors :class:`algomancy_data.datasource.BaseDataSource`:
subclasses MUST implement ``to_json`` / ``from_json`` to participate in
database persistence. Subclasses whose state decomposes into one or more
DataFrames can additionally implement
:class:`algomancy_scenario.persistence.protocols.SqlResultLayout` to land each
DataFrame in a real, externally queryable SQL table.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar


class BaseScenarioResult(ABC):
    def __init__(self, data_id: str):
        self.data_id = data_id
        self.completed_at = datetime.now()

    @abstractmethod
    def to_dict(self) -> dict:
        raise NotImplementedError("Abstract method")

    @abstractmethod
    def to_json(self) -> str:
        """Serialise the full result to a JSON string.

        The output must round-trip through :meth:`from_json`. Used as the
        JSON-blob fallback path by ``SqlScenarioRepository`` when the subclass
        does not implement ``SqlResultLayout``.
        """
        raise NotImplementedError("Abstract method")

    @classmethod
    @abstractmethod
    def from_json(cls, json_string: str) -> "BaseScenarioResult":
        """Reconstruct an instance from the string produced by :meth:`to_json`."""
        raise NotImplementedError("Abstract method")


BASE_RESULT_BOUND = TypeVar("BASE_RESULT_BOUND", bound=BaseScenarioResult)


class ScenarioResult(BaseScenarioResult):
    """Bundled minimal result: carries only ``data_id`` and ``completed_at``."""

    def __init__(self, data_id: str):
        super().__init__(data_id)

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.data_id,
            "completed_at": self.completed_at,
        }

    def to_json(self) -> str:
        return json.dumps(
            {
                "data_id": self.data_id,
                "completed_at": self.completed_at.isoformat(),
            }
        )

    @classmethod
    def from_json(cls, json_string: str) -> "ScenarioResult":
        payload = json.loads(json_string)
        inst = cls(data_id=payload["data_id"])
        completed_at = payload.get("completed_at")
        if completed_at:
            inst.completed_at = datetime.fromisoformat(completed_at)
        return inst
