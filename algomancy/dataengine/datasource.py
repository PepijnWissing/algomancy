import io
import json
import uuid
from datetime import datetime
from enum import StrEnum, auto
from typing import List

import pandas as pd

from algomancy.dataengine.validator import ValidationMessage


class DataSourceType(StrEnum):
    MASTER_DATA= auto()
    DERIVED_DATA = auto()
    DUMMY_DATA = auto()


class DataSource:

    def __init__(self,
                 ds_type: DataSourceType,
                 name: str = None,
                 validation_messages: List[ValidationMessage] = None,
                 ds_id: str | None = None,
                 creation_datetime: datetime | None = None
                 ) -> None:
        self.tables: dict[str, pd.DataFrame] = {}
        self._ds_type = ds_type
        self._id: str = ds_id if ds_id else str(uuid.uuid4())
        self._creation_datetime = creation_datetime if creation_datetime else datetime.now()
        self.validation_messages = validation_messages
        if not name and ds_type == DataSourceType.MASTER_DATA:
            self._name = "Master Data"
        elif not name and ds_type == DataSourceType.DERIVED_DATA:
            raise ValueError("Name is required for derived data")
        else:
            self._name = name

    def __eq__(self, other):
        return self.id == other.id

    # -- should be overwritten by derived classes
    def to_ai_ctx(self):
        return {
            key: df.head() for key, df in self.tables.items()
        }

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def creation_datetime(self):
        return self._creation_datetime

    def is_master_data(self):
        return self._ds_type == DataSourceType.MASTER_DATA

    def set_to_master_data(self):
        self._ds_type = DataSourceType.MASTER_DATA

    def add_table(self, name: str, df: pd.DataFrame, logger=None):
        if logger:
            logger._log(f"Adding table '{name}' to DataSource")
        self.tables[name] = df

    def get_table(self, name: str) -> pd.DataFrame:
        return self.tables[name]

    def list_tables(self):
        return list(self.tables.keys())

    def copy_contents_from(self, ds_to_copy: 'DataSource') -> None:
        for name, df in ds_to_copy.tables.items():
            self.add_table(name, df.copy())

    # to be overwritten by derived classes
    def to_parquet_bytes(self) -> bytes:
        """
        Serializes the DataSource object to parquet format as bytes.
        This is useful for creating downloadable content in a Dash app.

        Returns:
            bytes: The serialized DataSource as parquet bytes
        """
        # Create a combined DataFrame with a 'table_name' column to identify the source
        combined_data = []

        for table_name, df in self.tables.items():
            # Create a copy of the DataFrame to avoid modifying the original
            temp_df = df.copy()

            # Add table_name as a column
            temp_df['_table_name'] = table_name

            # Add to list for concatenation
            combined_data.append(temp_df)

        if not combined_data:
            # Create an empty DataFrame if there are no tables
            combined_df = pd.DataFrame({'_table_name': [], '_metadata': []})
        else:
            # Concatenate all tables
            combined_df = pd.concat(combined_data, ignore_index=True)

        # Add metadata as a separate row
        metadata = {
            'id': self.id,
            'name': self._name,
            'type': str(self._ds_type),
            'creation_datetime': str(self.creation_datetime),
            'tables': self.list_tables()
        }

        # Create a metadata DataFrame
        metadata_df = pd.DataFrame({
            '_table_name': ['_metadata'],
            '_metadata': [json.dumps(metadata)]
        })

        # Append metadata to the combined DataFrame
        final_df = pd.concat([combined_df, metadata_df], ignore_index=True)

        # Serialize to parquet
        buffer = io.BytesIO()
        final_df.to_parquet(buffer)
        buffer.seek(0)

        return buffer.getvalue()

    # to be overwritten by derived classes
    @classmethod
    def from_parquet_bytes(cls, parquet_bytes: bytes) -> 'DataSource':
        """
        Creates a DataSource object from serialized parquet bytes.

        Args:
            parquet_bytes (bytes): The serialized DataSource as parquet bytes

        Returns:
            DataSource: A new DataSource object with the loaded data
        """
        # Read the parquet bytes into a DataFrame
        buffer = io.BytesIO(parquet_bytes)
        combined_df = pd.read_parquet(buffer)

        # Extract metadata
        metadata_row = combined_df[combined_df['_table_name'] == '_metadata']
        if not metadata_row.empty:
            metadata = json.loads(metadata_row['_metadata'].iloc[0])

            # Remove metadata row
            combined_df = combined_df[combined_df['_table_name'] != '_metadata']

            # Create the DataSource instance
            ds_type = DataSourceType(metadata['type'])
            ds = cls(
                ds_type=ds_type,
                name=metadata['name'],
                ds_id=metadata["id"],
                creation_datetime=metadata["creation_datetime"]
            )

            # Process each table
            for table_name in metadata['tables']:
                table_df = combined_df[combined_df['_table_name'] == table_name].copy()

                # Remove the _table_name column
                table_df = table_df.drop(columns=['_table_name'])

                # Add the table to the DataSource
                ds.add_table(table_name, table_df)

            return ds
        else:
            raise ValueError("No metadata found in the parquet data")

    # to be overwritten by derived classes
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
            'metadata': {
                'id': self.id,
                'name': self._name,
                'type': str(self._ds_type),
                'creation_datetime': str(self.creation_datetime),
                'tables': self.list_tables()
            },
            # Tables data
            'tables': {}
        }

        # Convert each table to a JSON-compatible representation
        for table_name, df in self.tables.items():
            # Create a copy and handle special values
            df_copy = df.copy()

            # Replace NaT with None for serialization
            for col in df_copy.select_dtypes(include=['datetime64']):
                df_copy[col] = df_copy[col].astype(object).where(~df_copy[col].isna(), None)

            # Replace NaN with None for better JSON serialization
            df_copy = df_copy.where(df_copy.notna(), None)

            # Convert DataFrame to records format (list of dictionaries)
            records = df_copy.to_dict(orient='records')

            # Store column types for proper reconstruction
            column_types = {}
            for col in df.columns:
                dtype = str(df[col].dtype)
                column_types[col] = dtype

            data_dict['tables'][table_name] = {
                'data': records,
                'columns': df.columns.tolist(),
                'dtypes': column_types,
                'index': df.index.tolist()
            }

        # Define a custom JSON encoder to handle special types
        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                if pd.isna(obj):
                    return None
                if isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                if hasattr(obj, 'to_json'):
                    return obj.to_json()
                return super().default(obj)

        # Serialize to JSON using the custom encoder
        return json.dumps(data_dict, indent=2, cls=CustomJSONEncoder)

    # to be overwritten by derived classes
    @classmethod
    def from_json(cls, json_string: str) -> 'DataSource':
        """
        Creates a DataSource object from serialized JSON string.

        Args:
            json_string (str): The serialized DataSource as JSON string

        Returns:
            DataSource: A new DataSource object with the loaded data
        """
        # Parse the JSON string
        data_dict = json.loads(json_string)

        # Extract metadata
        metadata = data_dict.get('metadata', {})
        if not metadata:
            raise ValueError("No metadata found in the JSON data")

        # Create DataSource instance
        ds_type = DataSourceType(metadata['type'])
        ds = cls(
            ds_type=ds_type,
            name=metadata['name'],
            ds_id=metadata["id"],
            creation_datetime=metadata["creation_datetime"]
        )

        # Process each table
        tables_data = data_dict.get('tables', {})
        for table_name, table_info in tables_data.items():
            # Convert records back to DataFrame
            records = table_info['data']
            columns = table_info['columns']
            index = table_info['index']
            dtypes = table_info.get('dtypes', {})

            # Create the DataFrame
            df = pd.DataFrame(records, columns=columns, index=index)

            # Convert columns back to their original types
            for col, dtype in dtypes.items():
                if col in df.columns:
                    try:
                        if 'datetime' in dtype:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        elif dtype == 'category':
                            df[col] = df[col].astype('category')
                        elif 'int' in dtype:
                            # Handle int columns that might have None values
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            if 'int' in dtype and 'float' not in dtype:
                                # Only convert to int if it was originally an int
                                df[col] = df[col].fillna(pd.NA).astype('Int64')  # Pandas nullable integer type
                        else:
                            df[col] = df[col].astype(dtype)
                    except (ValueError, TypeError):
                        # If conversion fails, keep as is
                        pass

            # Add the table to the DataSource
            ds.add_table(table_name, df)

        return ds

    def debug_mutate(self):
        raise NotImplementedError("To be overwritten by derived classes")
