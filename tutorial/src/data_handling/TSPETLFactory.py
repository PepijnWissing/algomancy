from typing import Dict, TypeVar, cast

from algomancy_data import (
    File,
    CSVFile,
    XLSXFile,
    ETLFactory,
    ValidationSequence,
    ExtractionSuccessVerification,
    SchemaValidator,
    ValidationSeverity,
    Loader,
)
from algomancy_data.extractor import (
    ExtractionSequence,
    CSVSingleExtractor,
    XLSXSingleExtractor,
    XLSXMultiExtractor,
)
from algomancy_data.transformer import TransformationSequence

from data_handling.loaders.loader import DataModelLoader
from data_handling.transformers.transform_create_locations import (
    TransformCreateLocations,
)
from data_handling.transformers.transform_customer_to_location import (
    TransformCustomerToLocation,
)
from data_handling.transformers.transform_dc_to_location import TransformDCToLocation
from data_handling.transformers.transform_location_to_routes import (
    TransformLocationToRoutes,
)
from data_handling.transformers.transform_stores_to_location import (
    TransformStoresToLocation,
)
from data_handling.transformers.transform_xdock_to_location import (
    TransformXDockToLocation,
)

F = TypeVar("F", bound=File)


class TSPETLFactory(ETLFactory):
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
                file=cast(CSVFile, files["stores"]),
                schema=self.get_schema("stores"),
                logger=self.logger,
                separator=",",
            )
        )
        sequence.add_extractor(
            XLSXSingleExtractor(
                file=cast(XLSXFile, files["dc"]),
                schema=self.get_schema("dc"),
                sheet_name=0,
                logger=self.logger,
            )
        )
        sequence.add_extractor(
            XLSXMultiExtractor(
                file=cast(XLSXFile, files["otherlocations"]),
                schema=self.get_schema("otherlocations"),
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
        location_df_name = "transform_locations"
        routes_df_name = "transform_routes"
        sequence.add_transformer(
            TransformCreateLocations(
                location_df_name=location_df_name, logger=self.logger
            )
        )
        sequence.add_transformer(
            TransformCustomerToLocation(
                location_df_name=location_df_name, logger=self.logger
            )
        )
        sequence.add_transformer(
            TransformXDockToLocation(
                location_df_name=location_df_name, logger=self.logger
            )
        )
        sequence.add_transformer(
            TransformStoresToLocation(
                location_df_name=location_df_name, logger=self.logger
            )
        )
        sequence.add_transformer(
            TransformDCToLocation(location_df_name=location_df_name, logger=self.logger)
        )
        sequence.add_transformer(
            TransformLocationToRoutes(
                location_df_name=location_df_name,
                routes_df_name=routes_df_name,
                logger=self.logger,
            )
        )
        return sequence

    def create_loader(self) -> Loader:
        return DataModelLoader(self.logger)
