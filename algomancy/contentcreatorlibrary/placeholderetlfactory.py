from typing import Dict, List

from algomancy import ETLFactory, ValidationSequence, Extractor, Transformer, Loader, Logger


class PlaceholderLoader(Loader):
    def __init__(self):
        super().__init__(
            Logger(),
        )

    def load(
            self,
            name,
            data,
            validation_messages,
            ds_type
    ):
        return None


class PlaceholderETLFactory(ETLFactory):
    def __init__(self, input_configurations, logger):
        super().__init__(input_configurations, logger)

    def create_extractors(self, files) -> Dict[str, Extractor]:
        return {}

    def create_validation_sequence(self) -> ValidationSequence:
        return ValidationSequence()

    def create_transformers(self) -> List[Transformer]:
        return []

    def create_loader(self) -> Loader:
        return PlaceholderLoader()
