"""Schema primitives for defining structured tabular data.

This module provides a simple ``Schema`` abstraction that declares column
names and their expected dtypes via the ``datatypes`` mapping. It also
contains helper utilities to introspect schema "data members" and validate
that all declared fields have a specified ``DataType``.
"""

import inspect
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Dict


class DataType(StrEnum):
    """Enumeration of supported logical data types for schema fields."""

    STRING = "string"
    DATETIME = "datetime64[ns]"
    INTEGER = "int64"
    FLOAT = "float64"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    INTERVAL = "interval"


class Schema(ABC):
    """Abstract base class for table schemas.

    Implementations typically declare attributes for the expected columns and
    provide a ``datatypes`` mapping that assigns a ``DataType`` to each field.
    """

    @property
    @abstractmethod
    def datatypes(self) -> Dict[str, DataType]:
        pass

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
