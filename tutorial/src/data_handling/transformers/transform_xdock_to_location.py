import pandas as pd
from algomancy_data import Transformer


class TransformXDockToLocation(Transformer):
    def __init__(
        self,
        location_df_name: str,
        logger=None,
    ) -> None:
        super().__init__(name="Location Transformer", logger=logger)
        self.location_df_name = location_df_name
        self.df_name: str = "otherlocations.xdock"
        self.column_mapping = {
            "ID": "id",
            "x": "x",
            "y": "y",
        }

    def transform(self, data: dict[str, pd.DataFrame]) -> None:
        if self._logger:
            self._logger.log("Transforming xdock to locations")

        data_df = data.get(self.df_name, None)
        data_df_locations = data.get(self.location_df_name, None)

        if (data_df is not None) and (data_df_locations is not None):
            normalized = (
                data_df.rename(columns=self.column_mapping)
                .reindex(columns=data_df_locations.columns)
                .astype(data_df_locations.dtypes.to_dict())
            )
            data[self.location_df_name] = pd.concat(
                [data_df_locations, normalized], ignore_index=True
            )
