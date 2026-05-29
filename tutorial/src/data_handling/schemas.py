from algomancy_data import Schema, DataType, FileExtension, SchemaType


class DCSchema(Schema):
    _FILENAME = "dc"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "ID"
    X = "x"
    Y = "y"

    _DATATYPES = {
        ID: DataType.STRING,
        X: DataType.INTEGER,
        Y: DataType.INTEGER,
    }


class LocationSchema(Schema):
    _FILENAME = "otherlocations"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.MULTI

    ID = "ID"
    X = "x"
    Y = "y"

    _DATATYPES = {
        "customer": {
            ID: DataType.STRING,
            X: DataType.INTEGER,
            Y: DataType.INTEGER,
        },
        "xdock": {
            ID: DataType.STRING,
            X: DataType.INTEGER,
            Y: DataType.INTEGER,
        },
    }


class StoresSchema(Schema):
    _FILENAME = "stores"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "ID"
    X = "x"
    Y = "y"

    _DATATYPES = {
        ID: DataType.STRING,
        X: DataType.INTEGER,
        Y: DataType.INTEGER,
    }


schemas = [
    DCSchema(),
    LocationSchema(),
    StoresSchema(),
]
