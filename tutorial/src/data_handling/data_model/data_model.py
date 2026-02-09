from datetime import datetime
from typing import List

import pandas as pd
from algomancy_data import DataSource, DataClassification, ValidationMessage
from data_handling.data_model.network_manager import NetworkManager


class DataModel(DataSource):
    def __init__(
        self,
        ds_type: DataClassification,
        name: str = None,
        tables: dict[str, pd.DataFrame] | None = None,
        validation_messages: List[ValidationMessage] = None,
        ds_id: str | None = None,
        creation_datetime: datetime | None = None,
    ):
        super().__init__(
            ds_type=ds_type,
            name=name,
            validation_messages=validation_messages,
            ds_id=ds_id,
            creation_datetime=creation_datetime,
        )

        if tables is not None:
            self.tables = tables

        self._network_manager: NetworkManager | None = None

    def set_network_manager(self, network_manager: NetworkManager):
        self._network_manager = network_manager

    @property
    def network_manager(self):
        return self._network_manager
