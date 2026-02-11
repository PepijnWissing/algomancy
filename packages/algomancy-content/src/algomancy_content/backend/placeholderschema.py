from typing import Dict

from algomancy_data import (
    Schema,
    DataType,
    FileExtension,
)
from algomancy_data.schema import SchemaType


class PlaceholderSchema(Schema):
    """Schema class that holds column names for placeholder data"""

    _FILENAME = "placeholder_data"
    _EXTENSION = FileExtension.CSV
    _SCHEMA = SchemaType.SINGLE

    @property
    def _defined_datatypes(self) -> Dict[str, DataType]:
        return {
            "id": DataType.INTEGER,
            "name": DataType.STRING,
            "age": DataType.INTEGER,
            "city": DataType.STRING,
            "department": DataType.STRING,
            "salary": DataType.INTEGER,
            "hire_date": DataType.DATETIME,
            "performance_score": DataType.FLOAT,
        }
