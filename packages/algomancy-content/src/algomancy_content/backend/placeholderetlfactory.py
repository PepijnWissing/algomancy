from typing import Dict

import algomancy_data as de
from algomancy_data import File
from algomancy_data.extractor import ExtractionSequence
from algomancy_data.transformer import TransformationSequence


class PlaceholderETLFactory(de.ETLFactory):
    def __init__(self, configs, logger=None):
        super().__init__(configs, logger)

    def create_extraction_sequence(self, files: Dict[str, File]) -> ExtractionSequence:
        # return the empty sequence
        return ExtractionSequence(logger=self.logger)

    def create_transformation_sequence(self) -> TransformationSequence:
        # return the empty sequence
        return TransformationSequence(logger=self.logger)

    def create_validation_sequence(self) -> de.ValidationSequence:
        # return the empty sequence
        return de.ValidationSequence(logger=self.logger)

    def create_loader(self) -> de.Loader:
        return de.DataSourceLoader(self.logger)
