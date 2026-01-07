from dataclasses import dataclass
from enum import StrEnum
from typing import List, Dict
from abc import ABC

from .schema import Schema


class FileExtension(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


@dataclass(frozen=True)
class InputFileConfiguration(ABC):
    extension: FileExtension
    file_name: str

    @property
    def file_name_with_extension(self) -> str:
        return self.file_name + "." + self.extension


@dataclass(frozen=True)
class SingleInputFileConfiguration(InputFileConfiguration):
    file_schema: Schema


@dataclass(frozen=True)
class MultiInputFileConfiguration(InputFileConfiguration):
    file_schemas: Dict[str, Schema]

    @property
    def sub_names(self) -> List[str]:
        return list(self.file_schemas.keys())
