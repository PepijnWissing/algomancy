(tutorial-results-ref)=
# Results
We need to create a class to store out results.

1. Create the directory result_model in src/data_handling/
2. Create the file result_model.py in the directory src/data_handling/result_model. 
This result model stores the tour (= a list of routes), but also a sorted list of locations.
```python
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
```
