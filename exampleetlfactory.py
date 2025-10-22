from typing import List, Dict, TypeVar, cast

import algomancy.dataengine as de

F = TypeVar("F", bound=de.File)


class ExampleETLFactory(de.ETLFactory):
    def __init__(self, configs, logger=None):
        super().__init__(configs, logger)

    def create_extractors(
        self,
        files: Dict[str, F],  # name to path format
    ) -> Dict[str, de.Extractor]:
        """
        Input:
            files: A dictionary mapping file names to file paths.

        Output:
            A dictionary mapping file names to Extractor objects.

        raises:
            ETLConstructionError: If any of the expected files or configurations are missing.
        """
        # declare expected names
        sku_data = "sku_data"
        warehouse_layout = "warehouse_layout"
        employee = "employees"
        inventory = "inventory"

        expected_files = {
            warehouse_layout,
            sku_data,
            employee,
            inventory,
        }

        missing_files = set(files.keys()) - expected_files
        if len(missing_files) > 0:
            raise de.ETLConstructionError(f"Missing files: {missing_files}")

        schemas = {cfg.file_name: cfg.file_schema for cfg in self.input_configurations}
        missing_schemas = set(schemas.keys()) - expected_files
        if len(missing_schemas) > 0:
            raise de.ETLConstructionError(f"Missing configurations: {missing_schemas}")

        extractors = {
            sku_data: de.CSVSingleExtractor(
                file=cast(de.CSVFile, files[sku_data]),
                schema=schemas[sku_data],
                logger=self.logger,
                separator=";",
            ),
            warehouse_layout: de.CSVSingleExtractor(
                file=cast(de.CSVFile, files[warehouse_layout]),
                schema=schemas[warehouse_layout],
                logger=self.logger,
                separator=";",
            ),
            employee: de.JSONSingleExtractor(
                file=cast(de.JSONFile, files[employee]),
                schema=schemas[employee],
                logger=self.logger,
            ),
            inventory: de.XLSXSingleExtractor(
                file=cast(de.XLSXFile, files[inventory]),
                schema=schemas[inventory],
                sheet_name=1,
                logger=self.logger,
            ),
        }

        return extractors

    def create_validation_sequence(self) -> de.ValidationSequence:
        vs = de.ValidationSequence(logger=self.logger)

        vs.add_validator(de.ExtractionSuccessVerification())

        vs.add_validator(
            de.InputConfigurationValidator(
                configs=self.input_configurations,
                severity=de.ValidationSeverity.CRITICAL,
            )
        )

        return vs

    def create_transformers(self) -> List[de.Transformer]:
        return [de.CleanTransformer(self.logger)]

    def create_loader(self) -> de.Loader:
        return de.DataSourceLoader(self.logger)
