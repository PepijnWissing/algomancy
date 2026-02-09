import pandas as pd
from algomancy_data import Transformer


class TransformCreateLocations(Transformer):
    def __init__(self, location_df_name: str, logger=None) -> None:
        super().__init__(name="Create location df transformer", logger=logger)
        self.location_df_name = location_df_name

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log("Create location df in transform")

        if data.get(self.location_df_name, None) is None:
            data[self.location_df_name] = pd.DataFrame(columns=["id", "x", "y"])
