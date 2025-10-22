from dataclasses import dataclass
from enum import StrEnum

from algomancy.dataengine.schema import Schema


class FileExtension(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


@dataclass(frozen=True)
class InputFileConfiguration:
    extension: FileExtension
    file_name: str
    file_schema: Schema

    @property
    def file_name_with_extension(self) -> str:
        return self.file_name + "." + self.extension
