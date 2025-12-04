"""
A module for representing and managing data sources. It defines an abstract
base class for data sources as well as concrete implementations with
serialization and deserialization functionality.
"""

import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum, auto
from typing import List, TypeVar

import pandas as pd

from algomancy.dataengine.validator import ValidationMessage


class DataClassification(StrEnum):
    MASTER_DATA = auto()
    DERIVED_DATA = auto()
    DUMMY_DATA = auto()


class BaseDataSource(ABC):
    """
    Base class for data sources.

    This class serves as a base for defining different types of data sources. It provides basic
    attributes and methods to handle data source IDs, creation timestamps, names, and
    validation messages. It also defines abstract methods that should be implemented by
    derived classes to handle data serialization and derivation.

    Attributes:
        validation_messages (List[ValidationMessage] | None): List of validation messages for the data source.
    """

    def __init__(
        self,
        ds_type: DataClassification,
        name: str = None,
        validation_messages: List[ValidationMessage] = None,
        ds_id: str | None = None,
        creation_datetime: datetime | None = None,
    ) -> None:
        self._ds_type = ds_type
        self._id: str = ds_id if ds_id else str(uuid.uuid4())
        self._creation_datetime = (
            creation_datetime if creation_datetime else datetime.now()
        )
        self.validation_messages = validation_messages
        if not name and ds_type == DataClassification.MASTER_DATA:
            self._name = "Master Data"
        elif not name and ds_type == DataClassification.DERIVED_DATA:
            raise ValueError("Name is required for derived data")
        else:
            self._name = name

    def __eq__(self, other):
        return self.id == other.id

    @property
    def name(self) -> str:
        return self._name

    def _set_name(self, new_name):
        self._name = new_name

    @property
    def id(self):
        return self._id

    @property
    def creation_datetime(self):
        return self._creation_datetime

    def is_master_data(self):
        return self._ds_type == DataClassification.MASTER_DATA

    def set_to_master_data(self):
        self._ds_type = DataClassification.MASTER_DATA

    def derive(self, new_data_key: str):
        """
        Creates a derived object with a given new key.

        This method generates a duplicate of the current object with the same data
        and sets a new key for it, effectively creating a derived object with a
        different identifier.

        Args:
            new_data_key (str): The new key to assign to the derived object.

        Returns:
            Type of the calling class: A new instance of the same class with the
            derived data and updated key.
        """
        new_data = type(self).from_json(self.to_json())
        new_data._set_name(new_data_key)
        return new_data

    @abstractmethod
    def to_json(self) -> str:
        raise NotImplementedError("Abstract method")

    @classmethod
    @abstractmethod
    def from_json(cls, json_string: str) -> "BaseDataSource":
        raise NotImplementedError("Abstract method")

    def debug_mutate(self):
        raise NotImplementedError("Abstract method")


BASE_DATA_BOUND = TypeVar("BASE_DATA_BOUND", bound=BaseDataSource)


# todo: consider excluding from package
class DataSource(BaseDataSource):
    def __init__(
        self,
        ds_type: DataClassification,
        name: str = None,
        validation_messages: List[ValidationMessage] = None,
        ds_id: str | None = None,
        creation_datetime: datetime | None = None,
    ) -> None:
        super().__init__(ds_type, name, validation_messages, ds_id, creation_datetime)
        self.tables: dict[str, pd.DataFrame] = {}

    def to_json(self) -> str:
        """
        Serializes the DataSource object to JSON format.
        This is useful for creating human-readable downloadable content in a Dash app.

        Returns:
            str: The serialized DataSource as JSON string
        """
        # Create a dictionary to hold all data
        data_dict = {
            # Metadata
            "metadata": {
                "id": self.id,
                "name": self._name,
                "type": str(self._ds_type),
                "creation_datetime": str(self.creation_datetime),
                "tables": self.list_tables(),
            },
            # Tables data
            "tables": {},
        }

        # Convert each table to a JSON-compatible representation
        for table_name, df in self.tables.items():
            # Create a copy and handle special values
            df_copy = df.copy()

            # Replace NaT with None for serialization
            for col in df_copy.select_dtypes(include=["datetime64"]):
                df_copy[col] = (
                    df_copy[col].astype(object).where(~df_copy[col].isna(), None)
                )

            # Replace NaN with None for better JSON serialization
            df_copy = df_copy.where(df_copy.notna(), None)

            # Convert DataFrame to records format (list of dictionaries)
            records = df_copy.to_dict(orient="records")

            # Store column types for proper reconstruction
            column_types = {}
            for col in df.columns:
                dtype = str(df[col].dtype)
                column_types[col] = dtype

            data_dict["tables"][table_name] = {
                "data": records,
                "columns": df.columns.tolist(),
                "dtypes": column_types,
                "index": df.index.tolist(),
            }

        # Define a custom JSON encoder to handle special types
        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                if pd.isna(obj):
                    return None
                if isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                if hasattr(obj, "to_json"):
                    return obj.to_json()
                return super().default(obj)

        # Serialize to JSON using the custom encoder
        return json.dumps(data_dict, indent=2, cls=CustomJSONEncoder)

    @classmethod
    def from_json(cls, json_string: str) -> "DataSource":
        """
        Creates a DataSource object from serialized JSON string.

        Args:
            json_string (str): The serialized DataSource as JSON string

        Returns:
            BaseDataSource: A new DataSource object with the loaded data
        """
        # Parse the JSON string
        data_dict = json.loads(json_string)

        # Extract metadata
        metadata = data_dict.get("metadata", {})
        if not metadata:
            raise ValueError("No metadata found in the JSON data")

        # Create DataSource instance
        ds_type = DataClassification(metadata["type"])
        ds = cls(
            ds_type=ds_type,
            name=metadata["name"],
            ds_id=metadata["id"],
            creation_datetime=metadata["creation_datetime"],
        )

        # Process each table
        tables_data = data_dict.get("tables", {})
        for table_name, table_info in tables_data.items():
            # Convert records back to DataFrame
            records = table_info["data"]
            columns = table_info["columns"]
            index = table_info["index"]
            dtypes = table_info.get("dtypes", {})

            # Create the DataFrame
            df = pd.DataFrame(records, columns=columns, index=index)

            # Convert columns back to their original types
            for col, dtype in dtypes.items():
                if col in df.columns:
                    try:
                        if "datetime" in dtype:
                            df[col] = pd.to_datetime(df[col], errors="coerce")
                        elif dtype == "category":
                            df[col] = df[col].astype("category")
                        elif "int" in dtype:
                            # Handle int columns that might have None values
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                            if "int" in dtype and "float" not in dtype:
                                # Only convert to int if it was originally an int
                                df[col] = (
                                    df[col].fillna(pd.NA).astype("Int64")
                                )  # Pandas nullable integer type
                        else:
                            df[col] = df[col].astype(dtype)
                    except (ValueError, TypeError):
                        # If conversion fails, keep as is
                        pass

            # Add the table to the DataSource
            ds.add_table(table_name, df)

        return ds

    def add_table(self, name: str, df: pd.DataFrame, logger=None):
        if logger:
            logger.log(f"Adding table '{name}' to DataSource")
        self.tables[name] = df

    def get_table(self, name: str) -> pd.DataFrame:
        return self.tables[name]

    def list_tables(self):
        return list(self.tables.keys())
