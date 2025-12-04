import inspect
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Dict


class DataType(StrEnum):
    STRING = "string"
    DATETIME = "datetime64[ns]"
    INTEGER = "int64"
    FLOAT = "float64"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    INTERVAL = "interval"


class Schema(ABC):

    @property
    @abstractmethod
    def datatypes(self) -> Dict[str, DataType]:
        pass

    @classmethod
    def validate(cls):
        """
        Validates that each key in the schema has a specified datatype.
        :raises AssertionError: If a data type is missing
        """
        fields = Schema.get_data_members()
        for field in fields:
            assert field in cls.datatypes.keys()

    @classmethod
    def get_data_members(cls):
        """
        Geef alleen de 'data attributes' van een klasse:
        - Niet built-ins
        - Geen methodes, functies, klassen
        - Geen dunder-namen (dubbele underscores)
        """
        return [
            name
            for name, attr in vars(cls).items()
            if not (name.startswith('__') and name.endswith('__'))
               and not name == 'datatypes'
               and not inspect.isroutine(attr)
               and not inspect.isclass(attr)
               and not inspect.isbuiltin(attr)
               # Optioneel: filter properties/descriptors indien gewenst
               and not inspect.isdatadescriptor(attr)
        ]
