from abc import ABC, abstractmethod
from typing import List, Dict

import pandas as pd

from algomancy.dataengine.validator import ValidationMessage
from algomancy.dataengine.datasource import (
    DataClassification,
    DataSource,
    BASE_DATA_BOUND,
)


class Loader(ABC):
    def __init__(self, logger) -> None:
        self.logger = logger

    @abstractmethod
    def load(
        self,
        name: str,
        data: Dict[str, pd.DataFrame],
        validation_messages: List[ValidationMessage],
        ds_type: DataClassification,  # -- todo remove input argument: ETL'd data should always be master?
    ) -> BASE_DATA_BOUND:
        pass


class DataSourceLoader(Loader):
    def load(
        self,
        name: str,
        data: dict[str, pd.DataFrame],
        validation_messages: List[ValidationMessage],
        ds_type: DataClassification = DataClassification.MASTER_DATA,
    ) -> DataSource:
        datasource = DataSource(
            ds_type=ds_type,
            name=name,
            validation_messages=validation_messages,
        )
        if self.logger:
            self.logger.log("Loading data into DataSource")
        for name, df in data.items():
            datasource.add_table(name, df)
        return datasource
