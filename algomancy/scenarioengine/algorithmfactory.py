from typing import Dict, Any, List

from algomancy.dashboardlogger.logger import Logger
from algomancy.scenarioengine.algorithmtemplate import Algorithm, AlgorithmTemplate


class AlgorithmFactory:
    """
    Creates algorithm objects
    """

    def __init__(self, algo_templates: Dict[str, AlgorithmTemplate], logger: Logger = None):
        self._algo_templates = algo_templates
        self._logger = logger

    @property
    def available_algorithms(self) -> List[str]:
        return [str(key) for key in self._algo_templates.keys()]

    def create(
            self,
            input_name: str,
            input_params: Dict[str, Any]
    ) -> Algorithm:
        """

        :param input_name:
        :param input_params:
        :raises AssertionError: Either algorithm template is not found or parameter validation fails.
        :return:
        """
        template = self._algo_templates[input_name] if input_name in self._algo_templates else []
        assert template, f"Algorithm template '{input_name}' not found."

        algo_params = template.param_type()
        algo_params.set_values(input_params)
        algo_params.validate()

        return Algorithm(template, algo_params)
