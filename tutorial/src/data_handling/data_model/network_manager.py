from typing import List
from src.data_handling.data_model.location import Location
from src.data_handling.data_model.route import Route


class NetworkManager:
    def __init__(self):
        self._locations: dict[str, Location] = {}
        self._routes: dict[tuple[str, str], Route] = {}
        self._reachable_locations_from_location: dict[str, List[Location]] = {}

    def add_location(self, location: Location):
        self._locations[location.id] = location

    def add_route(self, route: Route):
        from_location, to_location = self.get_route_locations(route)
        if from_location is not None and to_location is not None:
            self._routes[(from_location.id, to_location.id)] = route
            if (
                self._reachable_locations_from_location.get(from_location.id, None)
                is None
            ):
                self._reachable_locations_from_location[from_location.id] = [
                    to_location
                ]
            else:
                self._reachable_locations_from_location[from_location.id] += [
                    to_location
                ]

    def get_locations(self) -> list[Location]:
        return list(self._locations.values())

    def get_location(self, location_id: str) -> Location:
        return self._locations[location_id]

    def get_route_locations(self, route: Route) -> tuple[Location, Location]:
        return self.get_location(route.from_id), self.get_location(route.to_id)

    def get_routes(self) -> list[Route]:
        return list(self._routes.values())

    def get_route(self, from_location_id: str, to_location_id: str) -> Route:
        return self._routes[(from_location_id, to_location_id)]

    def get_reachable_locations(self, location_id: str) -> List[Location]:
        return self._reachable_locations_from_location[location_id]
