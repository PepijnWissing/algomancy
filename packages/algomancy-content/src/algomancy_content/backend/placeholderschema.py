from algomancy_data import (
    Schema,
    DataType,
    FileExtension,
)
from algomancy_data.schema import SchemaType


class PlaceholderSchema(Schema):
    """Schema class to be used as a placeholder"""

    _FILENAME = "placeholder_data"
    _EXTENSION = FileExtension.CSV
    _SCHEMA = SchemaType.SINGLE

    _DATATYPES = {
        "id": DataType.INTEGER,
        "name": DataType.STRING,
        "age": DataType.INTEGER,
        "city": DataType.STRING,
        "department": DataType.STRING,
        "salary": DataType.INTEGER,
        "hire_date": DataType.DATETIME,
        "performance_score": DataType.FLOAT,
    }
