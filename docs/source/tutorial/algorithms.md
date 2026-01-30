(tutorial-algorithms-ref)=

# Defining algorithms

## Nearest Neighbor
1. Create a file nearest_neighbor.py in the directory src/templates/algorithms/
2. An example implementation is:
```python
from typing import List

from algomancy_scenario import (
    ScenarioResult,
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
            candidate_locations = self._remove_visited_locations(reachable_locations, ordered_locations)

            if len(candidate_locations) == 0:
                break

            next_location = min(
                candidate_locations,
                key=lambda next_loc: nm.get_route(current_location.id, next_loc.id).cost
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
            reachable_locations: List[Location],
            visited_locations: List[Location]
    ) -> List[Location]:
        visited_set = set(visited_locations)
        return [
            loc for loc in reachable_locations
            if loc not in visited_set
        ]
```
3. Create __init__.py in the directory src/templates/algorithms/, and fill it with the following:
```python
from templates.algorithm.nearest_neighbor import NearestNeighborAlgorithm

algorithm_templates = {
    "NearestNeighbor": NearestNeighborAlgorithm,
}

```
The dict key is the algorithm name, and the value is the algorithm class.

4. Add the algorithm template(s) to the ETL Factory (TSPETLFactory.py).
```python
# framework configuration via AppConfiguration
    app_cfg = AppConfiguration(
        etl_factory=TSPETLFactory,
        kpi_templates=kpi_templates,
        algo_templates=algorithm_templates,
        input_configs=input_configs,
        data_object_type=DataSource,
        autocreate=False, #this will be the default in next release
        autorun=False, #this will be the default in next release
        host=host,
        port=port,
        data_page="standard",#this will be the default in next release
    )
```
5. Start the application.
6. Load the data
7. Create a new scenario and run the NearestNeighbor algorithm.
8. Verify that no errors occur


## Simulated Annealing
We also implement a simulated annealing algorithm. 
1. Create a file simulated_annealing.py in the directory src/templates/algorithms/
2. We make the algorithm such that the user can define the parameters. This means that the user can
specify the parameter values in a GUI dialog. This is defined below in SimulatedAnnealingParametersSet. 
Do not forget to also define the @property functions to access the parameters in the algorithm.
3. We also implement the algorithm itself, see below:
```python
import math
import random
from typing import List
from algomancy_scenario import BaseAlgorithm, BaseParameterSet
from algomancy_utils.baseparameterset import FloatParameter, IntegerParameter

from data_handling.data_model.data_model import DataModel
from data_handling.data_model.location import Location
from data_handling.data_model.network_manager import NetworkManager
from data_handling.result_model.result_model import ResultModel


class SimulatedAnnealingParameterSet(BaseParameterSet):
    def __init__(
        self,
        name: str = "SimulatingAnnealing",
    ):
        super().__init__(name=name)

        self.add_parameters(
            [
                FloatParameter(name="initial_temperature", value=1000),
                FloatParameter(name="cooling_rate", value=0.995),
                FloatParameter(name="min_temperature", value=1.0),
                IntegerParameter(name="max_iterations", value=10000),
                FloatParameter(name="seed", value=42),
            ]
        )

    @property
    def initial_temperature(self) -> float:
        return self._parameters["initial_temperature"].value

    @property
    def cooling_rate(self) -> float:
        return self._parameters["cooling_rate"].value

    @property
    def min_temperature(self) -> float:
        return self._parameters["min_temperature"].value

    @property
    def max_iterations(self) -> int:
        return self._parameters["max_iterations"].value

    @property
    def seed(self) -> float:
        return self._parameters["seed"].value

    def validate(self):
        pass


class SimulatedAnnealingAlgorithm(BaseAlgorithm):
    def __init__(
        self,
        params: SimulatedAnnealingParameterSet,
    ):
        super().__init__(name="SimulatingAnnealing", params=params)

    @staticmethod
    def initialize_parameters() -> SimulatedAnnealingParameterSet:
        return SimulatedAnnealingParameterSet()

    def run(self, data: DataModel) -> ResultModel:
        nm = data.network_manager

        # initialize tour randomly
        locations = nm.get_locations()
        random.shuffle(locations)
        current_tour = locations
        current_cost = self._tour_cost(current_tour, nm=nm)

        best_tour = current_tour[:]
        best_cost = current_cost

        iteration = 0

        temperature = self.params.initial_temperature

        while temperature > self.params.min_temperature and iteration < self.params.max_iterations:
            self.set_progress(iteration / self.params.max_iterations * 100.0)
            candidate_tour = self._neighbor(current_tour)
            candidate_cost = self._tour_cost(candidate_tour, nm=nm)

            delta = candidate_cost - current_cost

            # accept the candidate if better or with probability exp(-delta / T)
            if delta < 0 or random.random() < math.exp(-delta / temperature):
                current_tour = candidate_tour
                current_cost = candidate_cost

                if current_cost < best_cost:
                    best_tour = current_tour[:]
                    best_cost = current_cost

            # cool down
            temperature *= self.params.cooling_rate
            iteration += 1

        # build ResultModel
        rm = ResultModel(data_id=data.id)
        rm.set_ordered_locations(ordered_locations=best_tour)

        tour = []
        for i in range(len(best_tour) - 1):
            from_location, to_location = best_tour[i], best_tour[i+1]
            tour += [nm.get_route(from_location.id, to_location.id)]

        rm.set_tour(tour=tour)

        return rm

    @staticmethod
    def _tour_cost(tour: List[Location], nm: NetworkManager) -> float:
        """Compute the total cost of the tour."""
        cost = 0.0
        for i in range(len(tour) - 1):
            route = nm.get_route(tour[i].id, tour[i+1].id)
            cost += route.cost
        return cost

    @staticmethod
    def _neighbor(tour: List[Location]) -> List[Location]:
        """Swap two random locations to create a neighboring tour."""
        new_tour = tour[:]
        i, j = random.sample(range(len(new_tour)), 2)
        new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
        return new_tour
```
3. Update __init__.py in the directory src/templates/algorithms/,
```python
from templates.algorithm.nearest_neighbor import NearestNeighborAlgorithm
from templates.algorithm.simulated_annealing import SimulatedAnnealingAlgorithm

algorithm_templates = {
    "NearestNeighbor": NearestNeighborAlgorithm,
    "SimulatingAnnealing": SimulatedAnnealingAlgorithm,
}
```

5. Start the application.
6. Load the data
7. Create a new scenario and run the NearestNeighbor algorithm.
8. Create a new scenario and run the SimulatedAnnealing algorithm.
9. Open the Compare page and select NearestNeighor as left scenario and SimulatedAnnealing as right scenario.
10. In the top right part, enable "Show KPI cards"
11. Verify that the KPI delta is reported on screen.
