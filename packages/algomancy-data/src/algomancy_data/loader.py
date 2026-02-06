"""Loader interfaces for materializing data objects.

This module defines the abstract ``Loader`` contract and a concrete
``DataSourceLoader`` implementation that turns a mapping of pandas
DataFrames into a ``DataSource`` while preserving validation messages.
"""

from abc import ABC, abstractmethod
from typing import List, Dict

import pandas as pd

from .validator import ValidationMessage
from .datasource import DataClassification, DataSource, BASE_DATA_BOUND


class Loader(ABC):
    """Abstract interface for loading transformed data into a destination."""

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
        """Create the destination object from transformed data.

        Args:
            name: Logical name of the dataset/destination.
            data: Mapping from table name to pandas DataFrame.
            validation_messages: Messages collected during validation.
            ds_type: Classification of the destination data.

        Returns:
            BASE_DATA_BOUND: A destination object containing the data.
        """
        raise NotImplementedError


class DataSourceLoader(Loader):
    """Loader that builds and populates a ``DataSource``."""

    def load(
        self,
        name: str,
        data: dict[str, pd.DataFrame],
        validation_messages: List[ValidationMessage],
        ds_type: DataClassification = DataClassification.MASTER_DATA,
    ) -> DataSource:
        """Instantiate a ``DataSource`` and populate it with tables.

        Args:
            name: Name of the resulting data source.
            data: Mapping of table names to DataFrames.
            validation_messages: Messages collected during validation.
            ds_type: Data classification for the data source.

        Returns:
            DataSource: The populated data source.
        """
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
