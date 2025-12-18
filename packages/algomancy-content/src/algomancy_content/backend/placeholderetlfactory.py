from typing import Dict, cast

import algomancy_data as de


class PlaceholderETLFactory(de.ETLFactory):
    def __init__(self, configs, logger=None):
        super().__init__(configs, logger)

    def create_extractors(self, files: Dict[str, de.File]) -> Dict[str, de.Extractor]:
        # define file name(s) for convenient access
        placeholder = "placeholder_data"

        # compile a convenient mapping of file names to schemas
        schemas = {cfg.file_name: cfg.file_schema for cfg in self.input_configurations}

        # create an extractor for each file
        extractors = {
            placeholder: de.CSVSingleExtractor(
                file=cast(de.CSVFile, files[placeholder]),
                schema=schemas[placeholder],
                logger=self.logger,
                separator=",",
            )
        }

        # output the extractors
        return extractors

    def create_validation_sequence(self) -> de.ValidationSequence:
        # construct the empty sequence
        vs = de.ValidationSequence(logger=self.logger)

        # add a validator to check for successful extraction
        vs.add_validator(de.ExtractionSuccessVerification())

        # add a validator to check datatypes of the extracted data
        vs.add_validator(
            de.InputConfigurationValidator(
                configs=self.input_configurations,
                severity=de.ValidationSeverity.CRITICAL,
            )
        )

        # output the sequence
        return vs

    def create_transformers(self) -> Dict[str, de.Transformer]:
        return {}

    def create_loader(self) -> de.Loader:
        return de.DataSourceLoader(self.logger)
