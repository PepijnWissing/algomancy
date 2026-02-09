import pandas as pd
from algomancy_data import Transformer


class TransformLocationToRoutes(Transformer):
    def __init__(
        self,
        location_df_name: str,
        routes_df_name: str,
        logger=None,
    ) -> None:
        super().__init__(name="Transform location to routes", logger=logger)
        self._location_df_name = location_df_name
        self._routes_df_name = routes_df_name

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log("Transforming locations to routes")

        locations = data.get(self._location_df_name, None)

        # Cartesian product with itself
        routes = locations.merge(locations, how="cross", suffixes=("_from", "_to"))

        # Optionally, remove routes where start and end are the same
        routes = routes[routes["id_from"] != routes["id_to"]]

        # calculate the euclidean distance between from and to coordinates
        routes["distance"] = routes.apply(
            lambda row: (
                (row["x_from"] - row["x_to"]) ** 2 + (row["y_from"] - row["y_to"]) ** 2
            )
            ** 0.5,
            axis=1,
        )

        # calculate the route cost
        routes["cost"] = routes["distance"] * 1.0

        # register routes on data dict
        data[self._routes_df_name] = routes
