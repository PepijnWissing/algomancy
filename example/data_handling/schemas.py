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


class EmployeeDataSchema(Schema):
    """Schema for employee data."""

    _FILENAME = "employees"
    _EXTENSION = FileExtension.JSON
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = Column("id", dtype=DataType.STRING, primary_key=True)
    NAME = Column("name", dtype=DataType.STRING)
    EMAIL = Column("email", dtype=DataType.STRING, unique=True)
    HIRE_DATE = Column("joined_date", dtype=DataType.DATETIME)
    LAST_LOGIN = Column("last_login", dtype=DataType.DATETIME, nullable=True)
    DATES_WITH_TYPO = Column("dates_with_typo", dtype=DataType.DATETIME, optional=True)
    IS_ACTIVE = Column("is_active", dtype=DataType.BOOLEAN)
    AGE = Column("age", dtype=DataType.INTEGER)
    DEPARTMENT = Column("attributes.department", dtype=DataType.STRING)
    POSITION = Column("attributes.position", dtype=DataType.STRING)
    SKILLS = Column("attributes.skills", dtype=DataType.STRING)


class InventorySchema(Schema):
    """Schema for inventory data (inventory.xlsx)."""

    _FILENAME = "inventory"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.SINGLE

    BRANCH = Column("Branch", dtype=DataType.STRING, primary_key=True)
    LOCATION_TYPE = Column("Location \nType P/S", dtype=DataType.STRING)
    LOCATION = Column("Location", dtype=DataType.STRING, primary_key=True)
    ITEM_NUMBER = Column("Item\nNumber", dtype=DataType.STRING, primary_key=True)
    ITEM_DESCRIPTION = Column("Item\nDescription", dtype=DataType.STRING)
    ITEM_DESCRIPTION_2 = Column(
        "Item\nDescription\n2", dtype=DataType.STRING, optional=True
    )
    LOT_SERIAL_NUMBER = Column(
        "Lot\nSerial\nNumber", dtype=DataType.STRING, optional=True
    )
    IB_SETUP_STATUS = Column("IB\nSetup\nStatus", dtype=DataType.STRING)
    TECHNICAL_STATUS = Column("Technical\nStatus", dtype=DataType.STRING)
    STOCKING_TYPE = Column("Stocking\nType", dtype=DataType.STRING)
    LINE_TYPE = Column("Line\nType", dtype=DataType.STRING)
    MASTER_PLANNING_FAMILY = Column("Master\nPlannings\nFamily", dtype=DataType.STRING)
    INVENTORY_COST_SELECTOR = Column("Inventory\nCost\nSelector", dtype=DataType.STRING)
    GL_CATEGORY = Column("GL\nCategory", dtype=DataType.STRING)
    UOM_PRIMARY = Column("UOM\nPrimary", dtype=DataType.STRING)
    UNIT_COST = Column("Unit\nCost", dtype=DataType.FLOAT)
    QUANTITY_ON_HAND = Column("Quantity\non Hand", dtype=DataType.FLOAT)
    INVENTORY_VALUE = Column("Inventory\nValue", dtype=DataType.FLOAT)
    SAFETY_STOCK = Column("Safety\nStock", dtype=DataType.FLOAT, nullable=True)
    VALUE_BASED_ON_SAFETY_STOCK = Column(
        "Value \nBased on \nSafety Stock", dtype=DataType.FLOAT, optional=True
    )


class LocationSchema(Schema):
    """Multi-sheet schema for location data (multisheet.xlsx)."""

    _FILENAME = "multisheet"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.MULTI

    # steden
    COUNTRY = "Country"
    CITY = "City"

    # klanten
    ID = "ID"
    Name = "Naam"

    _DATATYPES = {
        "Steden": {
            COUNTRY: DataType.STRING,
            CITY: DataType.STRING,
        },
        "Klanten": {
            ID: DataType.INTEGER,
            Name: DataType.STRING,
        },
    }


example_schemas = [
    WarehouseLayoutSchema(),
    ItemDataSchema(),
    InventorySchema,
    EmployeeDataSchema,
    LocationSchema,
]
