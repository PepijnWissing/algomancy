from algomancy_data import Column, DataType, FileExtension, Schema
from algomancy_data.schema import SchemaType


class WarehouseLayoutSchema(Schema):
    """Schema for warehouse layout data."""

    _FILENAME = "warehouse_layout"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column("slotid", dtype=DataType.STRING, primary_key=True)
    X = Column("x", dtype=DataType.FLOAT)
    Y = Column("y", dtype=DataType.FLOAT)
    ZONE = Column("zone", dtype=DataType.STRING)


class ItemDataSchema(Schema):
    """Schema for item / SKU data."""

    _FILENAME = "sku_data"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column("itemid", dtype=DataType.STRING, primary_key=True)
    SKU = Column("sku", dtype=DataType.STRING)
    DESCRIPTION = Column("description", dtype=DataType.STRING)
    CATEGORY = Column("category", dtype=DataType.STRING)
    DAILY_PICKS = Column("daily_picks", dtype=DataType.INTEGER)
    VOLUME_CM3 = Column("volume_cm3", dtype=DataType.FLOAT)
    WEIGHT_KG = Column("weight_kg", dtype=DataType.FLOAT)
    CURRENT_SLOT = Column("currentslot", dtype=DataType.STRING)
    OPTIMAL_SLOT = Column("optimalslot", dtype=DataType.STRING, optional=True)


example_schemas = [
    WarehouseLayoutSchema(),
    ItemDataSchema(),
]
