from algomancy_utils.baseparameterset import EmptyParameters
from typing import Dict, Any, List, Type, Generic

from algomancy_utils.logger import Logger
from .basealgorithm import ALGORITHM


class AlgorithmFactory(Generic[ALGORITHM]):
    """
    Creates algorithm objects
    """

    def __init__(self, templates: Dict[str, Type[ALGORITHM]], logger: Logger = None):
        self._templates: Dict[str, Type[ALGORITHM]] = templates
        self._logger = logger

    @property
    def available_algorithms(self) -> List[str]:
        return [str(key) for key in self._templates.keys()]

    @property
    def templates(self) -> Dict[str, Type[ALGORITHM]]:
        return self._templates

    def create(self, input_name: str, input_params: Dict[str, Any]) -> ALGORITHM:
        """

        :param input_name:
        :param input_params:
        :raises AssertionError: Either algorithm template is not found or parameter validation fails.
        :return:
        """
        template: Type[ALGORITHM] = (
            self._templates[input_name] if input_name in self._templates else None
        )
        assert template, f"Algorithm template '{input_name}' not found."

        algo_params = template.initialize_parameters()
        algo_params.set_validated_values(input_params)

        return template(algo_params)

    def get_parameters(self, algo_name: str):
        template: Type[ALGORITHM] = (
            self._templates[algo_name] if algo_name in self._templates else None
        )
        assert template, f"Algorithm template '{algo_name}' not found."

        algo_params = template.initialize_parameters()

        data_params = EmptyParameters()

        return algo_params, data_params
