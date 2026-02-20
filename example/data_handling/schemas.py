from algomancy_data import Schema, FileExtension, DataType
from algomancy_data.schema import SchemaType


class WarehouseLayoutSchema(Schema):
    """Schema class that holds column names for warehouse layout data"""

    _FILENAME = "warehouse_layout"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "slotid"
    X = "x"
    Y = "y"
    ZONE = "zone"

    _DATATYPES = {
        ID: DataType.STRING,
        ZONE: DataType.STRING,
        X: DataType.FLOAT,
        Y: DataType.FLOAT,
    }


class ItemDataSchema(Schema):
    """Schema class that holds column names for item data"""

    _FILENAME = "sku_data"
    _EXTENSION = FileExtension.CSV
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "itemid"
    SKU = "sku"
    DESCRIPTION = "description"
    CATEGORY = "category"
    DAILY_PICKS = "daily_picks"
    VOLUME_CM3 = "volume_cm3"
    WEIGHT_KG = "weight_kg"
    CURRENT_SLOT = "currentslot"
    OPTIMAL_SLOT = "optimalslot"

    _DATATYPES = {
        ID: DataType.STRING,
        SKU: DataType.STRING,
        DESCRIPTION: DataType.STRING,
        CATEGORY: DataType.STRING,
        DAILY_PICKS: DataType.INTEGER,
        VOLUME_CM3: DataType.FLOAT,
        WEIGHT_KG: DataType.FLOAT,
        CURRENT_SLOT: DataType.STRING,
        OPTIMAL_SLOT: DataType.STRING,
    }


class EmployeeDataSchema(Schema):
    """Schema class that holds column names for employee data"""

    _FILENAME = "employees"
    _EXTENSION = FileExtension.JSON
    _SCHEMA_TYPE = SchemaType.SINGLE

    ID = "id"
    name = "name"
    email = "email"
    hire_date = "joined_date"
    last_login = "last_login"
    dates_with_typo = "dates_with_typo"
    is_active = "is_active"
    age = "age"
    department = "attributes.department"
    position = "attributes.position"
    skills = "attributes.skills"

    _DATATYPES = {
        ID: DataType.STRING,
        name: DataType.STRING,
        email: DataType.STRING,
        hire_date: DataType.DATETIME,
        last_login: DataType.DATETIME,
        dates_with_typo: DataType.DATETIME,
        is_active: DataType.BOOLEAN,
        age: DataType.INTEGER,
        department: DataType.STRING,
        position: DataType.STRING,
        skills: DataType.STRING,
    }


class InventorySchema(Schema):
    """Schema class that holds column names for inventory data from inventory.xlsx"""

    _FILENAME = "inventory"
    _EXTENSION = FileExtension.XLSX
    _SCHEMA_TYPE = SchemaType.SINGLE

    BRANCH = "Branch"
    LOCATION_TYPE = "Location \nType P/S"
    LOCATION = "Location"
    ITEM_NUMBER = "Item\nNumber"
    ITEM_DESCRIPTION = "Item\nDescription"
    ITEM_DESCRIPTION_2 = "Item\nDescription\n2"
    LOT_SERIAL_NUMBER = "Lot\nSerial\nNumber"
    IB_SETUP_STATUS = "IB\nSetup\nStatus"
    TECHNICAL_STATUS = "Technical\nStatus"
    STOCKING_TYPE = "Stocking\nType"
    LINE_TYPE = "Line\nType"
    MASTER_PLANNING_FAMILY = "Master\nPlannings\nFamily"
    INVENTORY_COST_SELECTOR = "Inventory\nCost\nSelector"
    GL_CATEGORY = "GL\nCategory"
    UOM_PRIMARY = "UOM\nPrimary"
    UNIT_COST = "Unit\nCost"
    QUANTITY_ON_HAND = "Quantity\non Hand"
    INVENTORY_VALUE = "Inventory\nValue"
    SAFETY_STOCK = "Safety\nStock"
    VALUE_BASED_ON_SAFETY_STOCK = "Value \nBased on \nSafety Stock"

    _DATATYPES = {
        BRANCH: DataType.STRING,
        LOCATION_TYPE: DataType.STRING,
        LOCATION: DataType.STRING,
        ITEM_NUMBER: DataType.STRING,
        ITEM_DESCRIPTION: DataType.STRING,
        ITEM_DESCRIPTION_2: DataType.STRING,
        LOT_SERIAL_NUMBER: DataType.STRING,
        IB_SETUP_STATUS: DataType.STRING,
        TECHNICAL_STATUS: DataType.STRING,
        STOCKING_TYPE: DataType.STRING,
        LINE_TYPE: DataType.STRING,
        MASTER_PLANNING_FAMILY: DataType.STRING,
        INVENTORY_COST_SELECTOR: DataType.STRING,
        GL_CATEGORY: DataType.STRING,
        UOM_PRIMARY: DataType.STRING,
        UNIT_COST: DataType.FLOAT,
        QUANTITY_ON_HAND: DataType.FLOAT,
        INVENTORY_VALUE: DataType.FLOAT,
        SAFETY_STOCK: DataType.FLOAT,
        VALUE_BASED_ON_SAFETY_STOCK: DataType.FLOAT,
    }


class LocationSchema(Schema):
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
    WarehouseLayoutSchema,
    ItemDataSchema,
    InventorySchema,
    EmployeeDataSchema,
    LocationSchema,
]
