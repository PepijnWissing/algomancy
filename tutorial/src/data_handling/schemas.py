from typing import Dict
from algomancy_data import Schema, DataType, FileExtension, SchemaType


class DCSchema(Schema):
    _FILENAME = "dc"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "ID"
    X = "x"
    Y = "y"

    def _defined_datatypes(self) -> Dict[str, DataType]:
        return {
            DCSchema.ID: DataType.STRING,
            DCSchema.X: DataType.INTEGER,
            DCSchema.Y: DataType.INTEGER,
        }


class LocationSchema(Schema):
    _FILENAME = "otherlocations"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.MULTI

    ID = "ID"
    X = "x"
    Y = "y"

    def _defined_datatypes(self) -> Dict[str, Dict[str, DataType]]:
        return {
            "customer": {
                LocationSchema.ID: DataType.STRING,
                LocationSchema.X: DataType.INTEGER,
                LocationSchema.Y: DataType.INTEGER,
            },
            "xdock": {
                LocationSchema.ID: DataType.STRING,
                LocationSchema.X: DataType.INTEGER,
                LocationSchema.Y: DataType.INTEGER,
            },
        }


class StoresSchema(Schema):
    _FILENAME = "stores"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "ID"
    X = "x"
    Y = "y"

    def _defined_datatypes(self) -> Dict[str, DataType]:
        return {
            StoresSchema.ID: DataType.STRING,
            StoresSchema.X: DataType.INTEGER,
            StoresSchema.Y: DataType.INTEGER,
        }


schemas = [
    DCSchema(),
    LocationSchema(),
    StoresSchema(),
]
