from typing import List
from algomancy_data import Loader, ValidationMessage, DataClassification
from data_handling.data_model.data_model import DataModel
import pandas as pd
from data_handling.data_model.location import Location
from data_handling.data_model.network_manager import NetworkManager
from data_handling.data_model.route import Route


class DataModelLoader(Loader):
    def load(
        self,
        name: str,
        data: dict[str, pd.DataFrame],
        validation_messages: List[ValidationMessage],
        ds_type: DataClassification = DataClassification.MASTER_DATA,
    ) -> DataModel:
        datamodel = DataModel(
            tables=data,
            ds_type=ds_type,
            name=name,
            validation_messages=validation_messages,
        )
        if self.logger:
            self.logger.log("Loading data into DataModel")

        self.load_network_manager(dm=datamodel)
        self.load_locations(dm=datamodel)
        self.load_routes(dm=datamodel)

        return datamodel

    @staticmethod
    def load_network_manager(dm: DataModel):
        dm.set_network_manager(NetworkManager())

    @staticmethod
    def load_locations(dm: DataModel):
        data_locations = dm.get_table("transform_locations")
        nm = dm.network_manager
        for _, row in data_locations.iterrows():
            nm.add_location(
                location=Location(
                    id=row["id"],
                    x=row["x"],
                    y=row["y"],
                )
            )

    @staticmethod
    def load_routes(dm: DataModel):
        data_routes = dm.get_table("transform_routes")
        nm = dm.network_manager
        for _, row in data_routes.iterrows():
            route = Route(
                from_id=row["id_from"],
                to_id=row["id_to"],
                cost=row["cost"],
            )

            from_location, to_location = nm.get_route_locations(route=route)

            if from_location is None or to_location is None:
                continue

            nm.add_route(route=route)
