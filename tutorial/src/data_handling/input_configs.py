from typing import Dict
from algomancy_data import (
    Schema,
    DataType,
    SingleInputFileConfiguration,
    FileExtension,
    MultiInputFileConfiguration,
)


class DCSchema(Schema):
    ID = "ID"
    X = "x"
    Y = "y"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            DCSchema.ID: DataType.STRING,
            DCSchema.X: DataType.INTEGER,
            DCSchema.Y: DataType.INTEGER,
        }


class CustomerSchema(Schema):
    ID = "ID"
    X = "x"
    Y = "y"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            CustomerSchema.ID: DataType.STRING,
            CustomerSchema.X: DataType.INTEGER,
            CustomerSchema.Y: DataType.INTEGER,
        }


class XDockSchema(Schema):
    ID = "ID"
    X = "x"
    Y = "y"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            XDockSchema.ID: DataType.STRING,
            XDockSchema.X: DataType.INTEGER,
            XDockSchema.Y: DataType.INTEGER,
        }


class StoresSchema(Schema):
    ID = "ID"
    X = "x"
    Y = "y"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            StoresSchema.ID: DataType.STRING,
            StoresSchema.X: DataType.INTEGER,
            StoresSchema.Y: DataType.INTEGER,
        }


input_configs = [
    SingleInputFileConfiguration(
        extension=FileExtension.XLSX,
        file_name="dc",
        file_schema=DCSchema(),
    ),
    MultiInputFileConfiguration(
        extension=FileExtension.XLSX,
        file_name="otherlocations",
        file_schemas={
            "customer": CustomerSchema(),
            "xdock": XDockSchema(),
        },
    ),
    SingleInputFileConfiguration(
        extension=FileExtension.CSV,
        file_name="stores",
        file_schema=StoresSchema(),
    ),
]
