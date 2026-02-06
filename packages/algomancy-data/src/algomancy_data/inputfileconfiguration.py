"""Input file configuration types used by ETL factories.

Defines lightweight dataclasses that declare the expected files for a dataset
and their schemas. These configurations guide extractors and schema lookup in
``ETLFactory`` implementations.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import List, Dict
from abc import ABC

from .schema import Schema


class FileExtension(StrEnum):
    """Supported file extensions for input files."""

    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


@dataclass(frozen=True)
class InputFileConfiguration(ABC):
    """Base configuration for a logical input file.

    Attributes:
        extension: Expected file extension.
        file_name: Logical file name without extension.
    """

    extension: FileExtension
    file_name: str

    @property
    def file_name_with_extension(self) -> str:
        return self.file_name + "." + self.extension


@dataclass(frozen=True)
class SingleInputFileConfiguration(InputFileConfiguration):
    """Configuration for a single-sheet/single-entity file with one schema."""

    file_schema: Schema


@dataclass(frozen=True)
class MultiInputFileConfiguration(InputFileConfiguration):
    """Configuration for a multi-entity file with multiple schemas.

    Typical use is an Excel workbook with several sheets, each having its own
    schema.
    """

    file_schemas: Dict[str, Schema]

    @property
    def sub_names(self) -> List[str]:
        return list(self.file_schemas.keys())
