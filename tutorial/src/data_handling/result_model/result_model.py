import json
from datetime import datetime
from typing import List

from algomancy_scenario import ScenarioResult

from data_handling.data_model.location import Location
from data_handling.data_model.route import Route


class ResultModel(ScenarioResult):
    def __init__(
        self,
        data_id: str,
        tour: List[Route] | None = None,
        ordered_locations: List[Location] | None = None,
    ):
        super().__init__(data_id)
        self._tour = tour
        self._ordered_locations = ordered_locations

    def set_tour(self, tour: List[Route]):
        self._tour = tour

    def set_ordered_locations(self, ordered_locations: List[Location]):
        self._ordered_locations = ordered_locations

    @property
    def tour(self):
        return self._tour

    @property
    def ordered_locations(self):
        return self._ordered_locations

    def to_json(self) -> str:
        return json.dumps(
            {
                "data_id": self.data_id,
                "completed_at": self.completed_at.isoformat(),
                "tour": [
                    {"from_id": r.from_id, "to_id": r.to_id, "cost": r.cost}
                    for r in (self._tour or [])
                ],
                "ordered_locations": [
                    {"id": loc.id, "x": loc.x, "y": loc.y}
                    for loc in (self._ordered_locations or [])
                ],
            }
        )

    @classmethod
    def from_json(cls, json_string: str) -> "ResultModel":
        payload = json.loads(json_string)
        tour = [
            Route(from_id=r["from_id"], to_id=r["to_id"], cost=r["cost"])
            for r in payload.get("tour", [])
        ]
        locations = [
            Location(id=loc["id"], x=loc["x"], y=loc["y"])
            for loc in payload.get("ordered_locations", [])
        ]
        inst = cls(
            data_id=payload["data_id"],
            tour=tour,
            ordered_locations=locations,
        )
        completed_at = payload.get("completed_at")
        if completed_at:
            inst.completed_at = datetime.fromisoformat(completed_at)
        return inst
