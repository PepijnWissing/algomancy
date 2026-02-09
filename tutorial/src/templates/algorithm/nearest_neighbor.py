from typing import List

from algomancy_scenario import (
    BaseAlgorithm,
    BaseParameterSet,
)

from data_handling.data_model.data_model import DataModel
from data_handling.data_model.location import Location
from data_handling.result_model.result_model import ResultModel


class NearestNeighborParameterSet(BaseParameterSet):
    def __init__(
        self,
        name: str = "NearestNeighbor",
    ):
        super().__init__(name=name)

    def validate(self):
        pass


class NearestNeighborAlgorithm(BaseAlgorithm):
    def __init__(
        self,
        params: NearestNeighborParameterSet,
    ):
        super().__init__(name="NearestNeighbor", params=params)

    @staticmethod
    def initialize_parameters() -> NearestNeighborParameterSet:
        return NearestNeighborParameterSet()

    def run(self, data: DataModel) -> ResultModel:
        nm = data.network_manager

        # sort locations on ID
        locations = nm.get_locations()
        locations.sort(key=lambda loc: loc.id)

        current_location = locations[0]
        ordered_locations = [current_location]
        tour = []

        while len(ordered_locations) < len(locations):
            reachable_locations = nm.get_reachable_locations(current_location.id)
            candidate_locations = self._remove_visited_locations(
                reachable_locations, ordered_locations
            )

            if len(candidate_locations) == 0:
                break

            next_location = min(
                candidate_locations,
                key=lambda next_loc: nm.get_route(
                    current_location.id, next_loc.id
                ).cost,
            )
            ordered_locations += [next_location]
            tour += [nm.get_route(current_location.id, next_location.id)]
            current_location = next_location

        rm = ResultModel(data_id=data.id)
        rm.set_ordered_locations(ordered_locations=ordered_locations)
        rm.set_tour(tour=tour)
        return rm

    @staticmethod
    def _remove_visited_locations(
        reachable_locations: List[Location], visited_locations: List[Location]
    ) -> List[Location]:
        visited_set = set(visited_locations)
        return [loc for loc in reachable_locations if loc not in visited_set]
