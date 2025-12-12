from typing import Dict

from algomancy_data import (
    Schema,
    DataType,
    SingleInputFileConfiguration,
    FileExtension,
)


class PlaceholderSchema(Schema):
    """Schema class that holds column names for placeholder data"""

    @property
    def datatypes(self) -> Dict[str, DataType]:
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


placeholder_input_config = SingleInputFileConfiguration(
    extension=FileExtension.CSV,
    file_name="placeholder_data",
    file_schema=PlaceholderSchema(),
)
