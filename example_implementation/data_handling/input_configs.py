from typing import Dict

from algomancy.dataengine import Schema, InputFileConfiguration, FileExtension, DataType
from algomancy.dataengine.inputfileconfiguration import SingleInputFileConfiguration, MultiInputFileConfiguration


class WarehouseLayoutSchema(Schema):
    """Schema class that holds column names for warehouse layout data"""

    ID = "slotid"
    X = "x"
    Y = "y"
    ZONE = "zone"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            WarehouseLayoutSchema.ID: DataType.STRING,
            WarehouseLayoutSchema.ZONE: DataType.STRING,
            WarehouseLayoutSchema.X: DataType.FLOAT,
            WarehouseLayoutSchema.Y: DataType.FLOAT,
        }


class ItemDataSchema(Schema):
    """Schema class that holds column names for item data"""

    ID = "itemid"
    SKU = "sku"
    DESCRIPTION = "description"
    CATEGORY = "category"
    DAILY_PICKS = "daily_picks"
    VOLUME_CM3 = "volume_cm3"
    WEIGHT_KG = "weight_kg"
    CURRENT_SLOT = "currentslot"
    OPTIMAL_SLOT = "optimalslot"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            ItemDataSchema.ID: DataType.STRING,
            ItemDataSchema.SKU: DataType.STRING,
            ItemDataSchema.DESCRIPTION: DataType.STRING,
            ItemDataSchema.CATEGORY: DataType.STRING,
            ItemDataSchema.DAILY_PICKS: DataType.INTEGER,
            ItemDataSchema.VOLUME_CM3: DataType.FLOAT,
            ItemDataSchema.WEIGHT_KG: DataType.FLOAT,
            ItemDataSchema.CURRENT_SLOT: DataType.STRING,
            ItemDataSchema.OPTIMAL_SLOT: DataType.STRING,
        }


class EmployeeDataSchema(Schema):
    """Schema class that holds column names for employee data"""

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

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            EmployeeDataSchema.ID: DataType.STRING,
            EmployeeDataSchema.name: DataType.STRING,
            EmployeeDataSchema.email: DataType.STRING,
            EmployeeDataSchema.hire_date: DataType.DATETIME,
            EmployeeDataSchema.last_login: DataType.DATETIME,
            EmployeeDataSchema.dates_with_typo: DataType.DATETIME,
            EmployeeDataSchema.is_active: DataType.BOOLEAN,
            EmployeeDataSchema.age: DataType.INTEGER,
            EmployeeDataSchema.department: DataType.STRING,
            EmployeeDataSchema.position: DataType.STRING,
            EmployeeDataSchema.skills: DataType.STRING,
        }


class InventorySchema(Schema):
    """Schema class that holds column names for inventory data from inventory.xlsx"""

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

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            InventorySchema.BRANCH: DataType.STRING,
            InventorySchema.LOCATION_TYPE: DataType.STRING,
            InventorySchema.LOCATION: DataType.STRING,
            InventorySchema.ITEM_NUMBER: DataType.STRING,
            InventorySchema.ITEM_DESCRIPTION: DataType.STRING,
            InventorySchema.ITEM_DESCRIPTION_2: DataType.STRING,
            InventorySchema.LOT_SERIAL_NUMBER: DataType.STRING,
            InventorySchema.IB_SETUP_STATUS: DataType.STRING,
            InventorySchema.TECHNICAL_STATUS: DataType.STRING,
            InventorySchema.STOCKING_TYPE: DataType.STRING,
            InventorySchema.LINE_TYPE: DataType.STRING,
            InventorySchema.MASTER_PLANNING_FAMILY: DataType.STRING,
            InventorySchema.INVENTORY_COST_SELECTOR: DataType.STRING,
            InventorySchema.GL_CATEGORY: DataType.STRING,
            InventorySchema.UOM_PRIMARY: DataType.STRING,
            InventorySchema.UNIT_COST: DataType.FLOAT,
            InventorySchema.QUANTITY_ON_HAND: DataType.FLOAT,
            InventorySchema.INVENTORY_VALUE: DataType.FLOAT,
            InventorySchema.SAFETY_STOCK: DataType.FLOAT,
            InventorySchema.VALUE_BASED_ON_SAFETY_STOCK: DataType.FLOAT,
        }


class StedenSchema(Schema):
    COUNTRY = "Country"
    CITY = "City"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            StedenSchema.COUNTRY: DataType.STRING,
            StedenSchema.CITY: DataType.STRING,
        }


class KlantenSchema(Schema):
    ID = 'ID'
    Name = "Naam"

    @property
    def datatypes(self) -> Dict[str, DataType]:
        return {
            KlantenSchema.ID: DataType.INTEGER,
            KlantenSchema.Name: DataType.STRING,
        }


example_input_configs = [
    SingleInputFileConfiguration(
        extension=FileExtension.CSV,
        file_name="warehouse_layout",
        file_schema=WarehouseLayoutSchema(),
    ),
    SingleInputFileConfiguration(
        extension=FileExtension.CSV,
        file_name="sku_data",
        file_schema=ItemDataSchema(),
    ),
    SingleInputFileConfiguration(
        extension=FileExtension.XLSX,
        file_name="inventory",
        file_schema=InventorySchema(),
    ),
    SingleInputFileConfiguration(
        extension=FileExtension.JSON,
        file_name="employees",
        file_schema=EmployeeDataSchema(),
    ),
    MultiInputFileConfiguration(
        extension=FileExtension.XLSX,
        file_name="multisheet",
        file_schemas={
            "Steden": StedenSchema(),
            "Klanten": KlantenSchema(),
        }
    )
]
