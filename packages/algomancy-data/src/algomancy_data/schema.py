"""Schema primitives for defining structured tabular data.

This module provides a simple ``Schema`` abstraction that declares column
names and their expected dtypes via the ``datatypes`` mapping. It also
contains helper utilities to introspect schema "data members" and validate
that all declared fields have a specified ``DataType``.
"""

import inspect
from abc import ABC
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


class classproperty(property):
    """
    A decorator that creates a property accessible from both class and instances.

    When accessed from the class, passes the class to the decorated method.
    When accessed from an instance, passes the instance to the decorated method.
    """

    def __get__(self, instance, owner):
        # If accessed from an instance, pass the instance
        if instance is not None:
            return self.fget(instance)
        # If accessed from the class, pass the class
        return self.fget(owner)


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
    _DATATYPES: Dict[str, DataType] | Dict[str, Dict[str, DataType]] | str = (
        "default_datatypes"
    )

    def __init__(self, subschema_key: str | None = None) -> None:
        self._subschema_key = subschema_key

    @classproperty
    def file_name(cls) -> str:
        """Return the file name of the schema."""
        if cls._FILENAME == "default_filename":
            raise NotImplementedError("_FILENAME must be overridden by subclasses")

        return cls._FILENAME

    @classproperty
    def extension(cls) -> FileExtension:
        """Return the file extension of the schema."""
        if cls._EXTENSION == "default_extension":
            raise NotImplementedError("_EXTENSION must be overridden by subclasses")

        if isinstance(cls._EXTENSION, FileExtension):
            return cls._EXTENSION
        elif isinstance(cls._EXTENSION, str):
            return FileExtension(cls._EXTENSION)
        else:
            raise TypeError(f"Invalid extension type: {type(cls._EXTENSION)}")

    @classproperty
    def schema_type(cls) -> SchemaType:
        """Return the schema type of the schema."""
        if cls._SCHEMA_TYPE == "default_schema_type":
            raise NotImplementedError("_SCHEMA_TYPE must be overridden by subclasses")

        if isinstance(cls._SCHEMA_TYPE, SchemaType):
            return cls._SCHEMA_TYPE
        elif isinstance(cls._SCHEMA_TYPE, str):
            return SchemaType(cls._SCHEMA_TYPE)
        else:
            raise TypeError(f"Invalid schema type: {type(cls._SCHEMA_TYPE)}")

    @classproperty
    def file_name_with_extension(cls) -> str:
        return cls._FILENAME + "." + cls._EXTENSION

    @classproperty
    def datatypes(cls_or_self) -> Dict[str, DataType]:
        # Check implementation
        if cls_or_self._DATATYPES == "default_datatypes":
            raise NotImplementedError("_DATATYPES must be overridden by subclasses")

        if cls_or_self.has_subschema_specified:
            dtypes = cls_or_self._DATATYPES[cls_or_self._subschema_key]  # noqa
        elif cls_or_self.is_single():
            dtypes = cls_or_self._DATATYPES
        else:
            raise ValueError(
                "Method is only available for schemas that are single or specified"
            )

        cls_or_self._validate_datatypes(dtypes)

        return dtypes

    @classmethod
    def _validate_datatypes(cls, dtypes: dict[str, DataType]) -> None:
        # for single schema type: the return value must be Dict[str,DataType]
        dtypes: Dict[str, DataType]
        for field, dtype in dtypes.items():
            assert isinstance(field, str), (
                f"Field name must be a string, got {type(field)}"
            )
            assert isinstance(dtype, DataType), (
                f"Datatype for field '{field}' must be a DataType, got {type(dtype)}"
            )

    @classproperty
    def datatype_groups(cls) -> Dict[str, Dict[str, DataType]]:
        if not cls.is_multi():
            raise ValueError("Method is only available for multi schemas")

        # grab from implementation
        if cls._DATATYPES == "default_datatypes":
            raise NotImplementedError("_DATATYPES must be overridden by subclasses")

        dtypes = cls._DATATYPES

        # for multi-schema type: the return value must be Dict[str,Dict[str,DataType]]
        dtypes: Dict[str, Dict[str, DataType]]
        for schema_name, schema_datatypes in dtypes.items():
            assert isinstance(schema_name, str), (
                f"Schema name must be a string, got {type(schema_name)}"
            )
            cls._validate_datatypes(schema_datatypes)

        # return
        return dtypes

    @classproperty
    def sub_names(cls) -> List[str]:
        """Return the names of sub-schemas for multi-schema types."""
        if cls.schema_type == SchemaType.SINGLE:
            raise ValueError("Single-schema types do not have sub-schemas")
        elif cls.schema_type == SchemaType.MULTI:
            return list(cls.datatype_groups.keys())

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

    @classmethod
    def is_multi(cls) -> bool:
        """Check if the schema is a multi-schema type."""
        return cls.schema_type == SchemaType.MULTI

    @classproperty
    def has_subschema_specified(cls_or_self) -> bool:
        """
        Check if this schema class/instance has a specific subschema selected.

        For classes: Always returns False (no subschema can be specified at class level).
        For instances of MULTI schemas: Returns True if a subschema key is set.
        For instances of SINGLE schemas: Always returns False.

        Returns:
            bool: True if this is a MULTI schema instance with subschema key set.

        """
        # Check if it's an instance (has _subschema_key attribute from __init__)
        if isinstance(cls_or_self, Schema):
            return cls_or_self.is_multi() and cls_or_self._subschema_key is not None
        # It's a class - subschema can't be specified at class level
        return False

    @classmethod
    def is_single(cls) -> bool:
        """Check if the schema is a single-schema type."""
        return cls.schema_type == SchemaType.SINGLE

    @classmethod
    def get_subschema(cls, key: str) -> "Schema":
        """
        Create an instance representing a subset of a multi-schema.

        For MULTI schemas, this returns an instance that behaves as a SINGLE
        schema containing only the columns for the specified sheet/sub-name.

        Args:
            key: The name of the sub-schema (e.g., sheet name in XLSX)

        Returns:
            A Schema instance with datatypes filtered to the specified subset.

        Raises:
            ValueError: If called on a SINGLE schema or if key is invalid.
        """
        if not cls.is_multi():
            raise ValueError("get_subschema() is only available for MULTI schemas")

        if key not in cls.sub_names:
            raise ValueError(
                f"Key '{key}' does not define a subschema. Available: {cls.sub_names}"
            )

        return cls(subschema_key=key)
