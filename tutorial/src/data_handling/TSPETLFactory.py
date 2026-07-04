from typing import Dict, Optional, TypeVar, cast

from algomancy_data import (
    File,
    CSVFile,
    XLSXFile,
    ETLFactory,
    Schema,
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
from algomancy_utils import Logger

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
    @classmethod
    def create_extraction_sequence(
        cls,
        files: Dict[str, F] | None = None,
        schemas: Dict[str, Schema] | None = None,
        logger: Optional[Logger] = None,
    ) -> ExtractionSequence:
        sequence = ExtractionSequence()

        sequence.add_extractor(
            CSVSingleExtractor(
                file=cast(CSVFile, files["stores"]),
                schema=schemas["stores"],
                logger=logger,
                separator=",",
            )
        )
        sequence.add_extractor(
            XLSXSingleExtractor(
                file=cast(XLSXFile, files["dc"]),
                schema=schemas["dc"],
                sheet_name=0,
                logger=logger,
            )
        )
        sequence.add_extractor(
            XLSXMultiExtractor(
                file=cast(XLSXFile, files["otherlocations"]),
                schema=schemas["otherlocations"],
                logger=logger,
            )
        )

        return sequence

    @classmethod
    def create_validation_sequence(
        cls,
        schemas: Dict[str, Schema],
        logger: Optional[Logger] = None,
    ) -> ValidationSequence:
        vs = ValidationSequence(logger=logger)

        vs.add_validator(ExtractionSuccessVerification())

        vs.add_validator(
            SchemaValidator(
                schemas=list(schemas.values()),
                severity=ValidationSeverity.CRITICAL,
            )
        )

        return vs

    @classmethod
    def create_transformation_sequence(
        cls,
        schemas: Optional[Dict[str, Schema]] = None,
        logger: Optional[Logger] = None,
    ) -> TransformationSequence:
        sequence = TransformationSequence()
        location_df_name = "transform_locations"
        routes_df_name = "transform_routes"
        sequence.add_transformer(
            TransformCreateLocations(location_df_name=location_df_name, logger=logger)
        )
        sequence.add_transformer(
            TransformCustomerToLocation(
                location_df_name=location_df_name, logger=logger
            )
        )
        sequence.add_transformer(
            TransformXDockToLocation(location_df_name=location_df_name, logger=logger)
        )
        sequence.add_transformer(
            TransformStoresToLocation(location_df_name=location_df_name, logger=logger)
        )
        sequence.add_transformer(
            TransformDCToLocation(location_df_name=location_df_name, logger=logger)
        )
        sequence.add_transformer(
            TransformLocationToRoutes(
                location_df_name=location_df_name,
                routes_df_name=routes_df_name,
                logger=logger,
            )
        )
        return sequence

    @classmethod
    def create_loader(
        cls,
        logger: Optional[Logger] = None,
    ) -> Loader:
        return DataModelLoader(logger)
