"""Schema primitives for defining structured tabular data.

This module provides a simple ``Schema`` abstraction that declares column
names and their expected dtypes via the ``datatypes`` mapping. It also
contains helper utilities to introspect schema "data members" and validate
that all declared fields have a specified ``DataType``.
"""

import inspect
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Dict, List


class DataType(StrEnum):
    """Enumeration of supported logical data types for schema fields."""

    STRING = "string"
    DATETIME = "datetime64[ns]"
    INTEGER = "int64"
    FLOAT = "float64"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    INTERVAL = "interval"


class FileExtension(StrEnum):
    """Supported file extensions for input files."""

    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class SchemaType(StrEnum):
    """Enumeration of supported schema types."""

    SINGLE = "single"
    MULTI = "multi"


class Schema(ABC):
    """Abstract base class for table schemas.

    Implementations typically declare attributes for the expected columns and
    provide a ``datatypes`` mapping that assigns a ``DataType`` to each field.
    """

    _FILENAME: str = "default_filename"  # expected to be overridden by subclasses
    _EXTENSION: FileExtension | str = (
        "default_extension"  # expected to be overridden by subclasses
    )
    _SCHEMA_TYPE: SchemaType | str = (
        "default_schema_type"  # expected to be overridden by subclasses
    )

    def __init__(self, subschema_key: str | None = None) -> None:
        self._subschema_key = subschema_key

    @property
    def file_name(self) -> str:
        """Return the file name of the schema."""
        if self._FILENAME == "default_filename":
            raise NotImplementedError("_FILENAME must be overridden by subclasses")

        return self._FILENAME

    @property
    def extension(self) -> FileExtension:
        """Return the file extension of the schema."""
        if self._EXTENSION == "default_extension":
            raise NotImplementedError("_EXTENSION must be overridden by subclasses")

        if isinstance(self._EXTENSION, FileExtension):
            return self._EXTENSION
        elif isinstance(self._EXTENSION, str):
            return FileExtension(self._EXTENSION)
        else:
            raise TypeError(f"Invalid extension type: {type(self._EXTENSION)}")

    @property
    def schema_type(self) -> SchemaType:
        """Return the schema type of the schema."""
        if self._SCHEMA_TYPE == "default_schema_type":
            raise NotImplementedError("_SCHEMA_TYPE must be overridden by subclasses")

        if isinstance(self._SCHEMA_TYPE, SchemaType):
            return self._SCHEMA_TYPE
        elif isinstance(self._SCHEMA_TYPE, str):
            return SchemaType(self._SCHEMA_TYPE)
        else:
            raise TypeError(f"Invalid schema type: {type(self._SCHEMA_TYPE)}")

    @property
    def file_name_with_extension(self) -> str:
        return self._FILENAME + "." + self._EXTENSION

    @abstractmethod
    def _defined_datatypes(
        self,
    ) -> Dict[str, DataType] | Dict[str, Dict[str, DataType]]:
        raise NotImplementedError("Abstract method")

    @property
    def datatypes(self) -> Dict[str, DataType]:
        if self.is_multi() and self._subschema_key is not None:
            dtypes = self._defined_datatypes()[self._subschema_key]  # noqa
        elif self.is_single():
            dtypes = self._defined_datatypes()
        else:
            raise ValueError("Method is only available for single schemas")

        # for single schema type: the return value must be Dict[str,DataType]
        dtypes: Dict[str, DataType]
        for field, dtype in dtypes.items():
            assert isinstance(field, str), (
                f"Field name must be a string, got {type(field)}"
            )
            assert isinstance(dtype, DataType), (
                f"Datatype for field '{field}' must be a DataType, got {type(dtype)}"
            )

        # return
        return dtypes

    @property
    def datatype_groups(self) -> Dict[str, Dict[str, DataType]]:
        if not self.is_multi():
            raise ValueError("Method is only available for multi schemas")

        # grab from implementation
        dtypes = self._defined_datatypes()

        # for multi-schema type: the return value must be Dict[str,Dict[str,DataType]]
        dtypes: Dict[str, Dict[str, DataType]]
        for schema_name, schema_datatypes in dtypes.items():
            assert isinstance(schema_name, str), (
                f"Schema name must be a string, got {type(schema_name)}"
            )
            for field, dtype in schema_datatypes.items():
                assert isinstance(field, str), (
                    f"Field name must be a string, got {type(field)}"
                )
                assert isinstance(dtype, DataType), (
                    f"Datatype for field '{field}' must be a DataType, "
                    f"got {type(dtype)}"
                )

        # return
        return dtypes

    @property
    def sub_names(self) -> List[str]:
        """Return the names of sub-schemas for multi-schema types."""
        if self.schema_type == SchemaType.SINGLE:
            raise ValueError("Single-schema types do not have sub-schemas")
        elif self.schema_type == SchemaType.MULTI:
            return list(self.datatype_groups.keys())

        raise ValueError("Invalid schema type")

    @classmethod
    def validate(cls):
        """
        Validate that each declared field has an associated data type.

        Raises:
            AssertionError: If a field is missing from the ``datatypes`` mapping.
        """
        fields = Schema.get_data_members()
        for field in fields:
            assert field in cls.datatypes.keys()

    @classmethod
    def get_data_members(cls):
        """Return only the data attributes of the class.

        Excludes built-ins, methods/functions, classes, dunder names and
        known non-field attributes like ``datatypes``.
        """
        return [
            name
            for name, attr in vars(cls).items()
            if not (name.startswith("__") and name.endswith("__"))
            and not name == "datatypes"
            and not inspect.isroutine(attr)
            and not inspect.isclass(attr)
            and not inspect.isbuiltin(attr)
            # Optioneel: filter properties/descriptors indien gewenst
            and not inspect.isdatadescriptor(attr)
        ]

    def is_multi(self) -> bool:
        """Check if the schema is a multi-schema type."""
        return self.schema_type == SchemaType.MULTI

    def is_single(self) -> bool:
        """Check if the schema is a single-schema type."""
        return self.schema_type == SchemaType.SINGLE

    def generate_subschema(self, key):
        """Retrieve the subschema for the current schema type."""
        if not self.is_multi():
            raise ValueError("Cannot retrieve subschema for non-multi schema")

        assert key in self.sub_names, f"Key {key} does not define a subschema"

        return type(self)(subschema_key=key)
