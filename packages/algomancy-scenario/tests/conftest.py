import random

import pytest

from algomancy_data import (
    DataSource,
    File,
    ETLFactory,
    CSVSingleExtractor,
    CSVFile,
    DataSourceLoader,
    Loader,
    CleanTransformer,
    ValidationSeverity,
    SchemaValidator,
    ExtractionSuccessVerification,
    ValidationSequence,
    XLSXMultiExtractor,
    XLSXFile,
    XLSXSingleExtractor,
    JSONSingleExtractor,
    JSONFile,
)
from algomancy_data.extractor import ExtractionSequence
from algomancy_data.transformer import TransformationSequence
from algomancy_scenario import ScenarioManager, BaseKPI, ImprovementDirection
from algomancy_utils import Logger, BaseMeasurement, QUANTITIES
from time import sleep

from algomancy_scenario import (
    BaseParameterSet,
    ScenarioResult,
    BaseAlgorithm,
    IntegerParameter,
)

from typing import Dict, TypeVar, cast

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

    def _defined_datatypes(self) -> Dict[str, DataType]:
        return {
            WarehouseLayoutSchema.ID: DataType.STRING,
            WarehouseLayoutSchema.ZONE: DataType.STRING,
            WarehouseLayoutSchema.X: DataType.FLOAT,
            WarehouseLayoutSchema.Y: DataType.FLOAT,
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

    def _defined_datatypes(self) -> Dict[str, DataType]:
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

    def _defined_datatypes(self) -> Dict[str, DataType]:
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

    def _defined_datatypes(self) -> Dict[str, DataType]:
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

    def _defined_datatypes(self) -> Dict[str, Dict[str, DataType]]:
        return {
            "Steden": {
                LocationSchema.COUNTRY: DataType.STRING,
                LocationSchema.CITY: DataType.STRING,
            },
            "Klanten": {
                LocationSchema.ID: DataType.INTEGER,
                LocationSchema.Name: DataType.STRING,
            },
        }


example_schemas = [
    WarehouseLayoutSchema(),
    ItemDataSchema(),
    InventorySchema(),
    EmployeeDataSchema(),
    LocationSchema(),
]

F = TypeVar("F", bound=File)


class ExampleETLFactory(ETLFactory):
    def __init__(self, configs, logger=None):
        super().__init__(configs, logger)

    def create_extraction_sequence(
        self,
        files: Dict[str, F],  # name to path format
    ) -> ExtractionSequence:
        """
        Input:
            files: A dictionary mapping file names to file paths.

        Output:
            An extraction sequence object

        raises:
            ETLConstructionError: If any of the expected files or configurations are missing.
        """
        sequence = ExtractionSequence()

        sequence.add_extractor(
            CSVSingleExtractor(
                file=cast(CSVFile, files["sku_data"]),
                schema=self.get_schema("sku_data"),
                logger=self.logger,
                separator=";",
            )
        )
        sequence.add_extractor(
            CSVSingleExtractor(
                file=cast(CSVFile, files["warehouse_layout"]),
                schema=self.get_schema("warehouse_layout"),
                logger=self.logger,
                separator=";",
            )
        )
        sequence.add_extractor(
            JSONSingleExtractor(
                file=cast(JSONFile, files["employees"]),
                schema=self.get_schema("employees"),
                logger=self.logger,
            )
        )
        sequence.add_extractor(
            XLSXSingleExtractor(
                file=cast(XLSXFile, files["inventory"]),
                schema=self.get_schema("inventory"),
                sheet_name=1,
                logger=self.logger,
            )
        )
        sequence.add_extractor(
            XLSXMultiExtractor(
                file=cast(XLSXFile, files["multisheet"]),
                schema=self.get_schema("multisheet"),
                logger=self.logger,
            )
        )

        return sequence

    def create_validation_sequence(self) -> ValidationSequence:
        vs = ValidationSequence(logger=self.logger)

        vs.add_validator(ExtractionSuccessVerification())

        vs.add_validator(
            SchemaValidator(
                schemas=self.schemas,
                severity=ValidationSeverity.CRITICAL,
            )
        )

        return vs

    def create_transformation_sequence(self) -> TransformationSequence:
        sequence = TransformationSequence()
        sequence.add_transformer(CleanTransformer(self.logger))
        return sequence

    def create_loader(self) -> Loader:
        return DataSourceLoader(self.logger)


class SlowAlgorithmParams(BaseParameterSet):
    def __init__(self, name: str = "Slow") -> None:
        super().__init__(name=name)

        self.add_parameters(
            [IntegerParameter(name="duration", minvalue=1, maxvalue=60)]
        )

    @property
    def duration(self) -> int:
        return int(self["duration"])

    def validate(self):
        pass


class SlowAlgorithm(BaseAlgorithm):
    def __init__(self, params: SlowAlgorithmParams) -> None:
        super().__init__(name="Slow", params=params)

    @staticmethod
    def initialize_parameters() -> SlowAlgorithmParams:
        return SlowAlgorithmParams()

    def run(self, data: DataSource) -> ScenarioResult:
        for i in range(self.params.duration):
            self.set_progress(100 * i / self.params.duration)
            sleep(1)
        self.set_progress(100)
        return ScenarioResult(data_id=data.id)


algorithm_templates = {
    "Slow": SlowAlgorithm,
}


class DelayKPI(BaseKPI):
    def __init__(self):
        super().__init__(
            name="Average Delay",
            better_when=ImprovementDirection.AT_MOST,
            base_measurement=BaseMeasurement(
                QUANTITIES["time"]["s"], min_digits=1, max_digits=3, decimals=1
            ),
            threshold=1200,
        )

    def compute(self, result: ScenarioResult) -> float:
        return 1000 * (1 + 0.5 * random.random())


kpi_templates = {
    "Delay": DelayKPI,
}


@pytest.fixture
def mock_configs():
    # framework configuration
    return {
        "data_path": "packages/algomancy-scenario/tests/data",
        "has_persistent_state": True,
        "save_type": "json",
        "data_object_type": DataSource,  # Plug in your own data object type here
        "etl_factory": ExampleETLFactory,  # Plug in your own ETL factory here
        "schemas": example_schemas,  # Plug in your own input configs here
        "autorun": False,
        "kpi_templates": kpi_templates,
        "algo_templates": algorithm_templates,
    }


@pytest.fixture
def quiet_logger():
    logger = Logger()
    logger.toggle_print_to_console(False)
    return logger


@pytest.fixture
def mock_scenario_manager_no_data(mock_configs, quiet_logger: Logger):
    sm: ScenarioManager = ScenarioManager(
        etl_factory=mock_configs["etl_factory"],
        kpi_templates=mock_configs["kpi_templates"],
        algo_templates=mock_configs["algo_templates"],
        data_folder=mock_configs["data_path"],
        schemas=mock_configs["schemas"],
        has_persistent_state=mock_configs["has_persistent_state"],
        save_type=mock_configs["save_type"],
        data_object_type=mock_configs["data_object_type"],
        logger=quiet_logger,
    )
    return sm


@pytest.fixture
def mock_scenario_manager_with_data(mock_configs, quiet_logger: Logger):
    sm: ScenarioManager = ScenarioManager(
        etl_factory=mock_configs["etl_factory"],
        kpi_templates=mock_configs["kpi_templates"],
        algo_templates=mock_configs["algo_templates"],
        data_folder=mock_configs["data_path"],
        schemas=mock_configs["schemas"],
        has_persistent_state=mock_configs["has_persistent_state"],
        save_type=mock_configs["save_type"],
        data_object_type=mock_configs["data_object_type"],
        logger=quiet_logger,
    )

    sm.debug_load_data("example_data")

    return sm
