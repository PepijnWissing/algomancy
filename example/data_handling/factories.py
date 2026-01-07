from typing import Dict, TypeVar, cast

from algomancy_data import (
    File,
    CSVFile,
    JSONFile,
    XLSXFile,
    ETLFactory,
    ValidationSequence,
    ExtractionSuccessVerification,
    InputConfigurationValidator,
    ValidationSeverity,
    Loader,
    DataSourceLoader,
)
from algomancy_data.extractor import (
    ExtractionSequence,
    CSVSingleExtractor,
    JSONSingleExtractor,
    XLSXSingleExtractor,
    XLSXMultiExtractor,
)
from algomancy_data.transformer import TransformationSequence, CleanTransformer

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
                schema=self.get_schemas("sku_data"),
                logger=self.logger,
                separator=";",
            )
        )
        sequence.add_extractor(
            CSVSingleExtractor(
                file=cast(CSVFile, files["warehouse_layout"]),
                schema=self.get_schemas("warehouse_layout"),
                logger=self.logger,
                separator=";",
            )
        )
        sequence.add_extractor(
            JSONSingleExtractor(
                file=cast(JSONFile, files["employees"]),
                schema=self.get_schemas("employees"),
                logger=self.logger,
            )
        )
        sequence.add_extractor(
            XLSXSingleExtractor(
                file=cast(XLSXFile, files["inventory"]),
                schema=self.get_schemas("inventory"),
                sheet_name=1,
                logger=self.logger,
            )
        )
        sequence.add_extractor(
            XLSXMultiExtractor(
                file=cast(XLSXFile, files["multisheet"]),
                schemas=self.get_schemas("multisheet"),
                logger=self.logger,
            )
        )

        return sequence

    def create_validation_sequence(self) -> ValidationSequence:
        vs = ValidationSequence(logger=self.logger)

        vs.add_validator(ExtractionSuccessVerification())

        vs.add_validator(
            InputConfigurationValidator(
                configs=self.input_configurations,
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
