from typing import Dict, List, Optional

from algomancy.scenarioengine.algorithmfactory import AlgorithmFactory
from algomancy.dashboardlogger.logger import Logger
from algomancy.scenarioengine.algorithmtemplate import AlgorithmTemplate
from algomancy.scenarioengine.keyperformanceindicator import KpiTemplate, build_kpis
from algomancy.scenarioengine.scenario import Scenario
from algomancy.dataengine.datamanager import DataManager


class ScenarioFactory:
    """
    Creates scenarios, builds algorithms and KPIs, and performs parameter validation.
    """

    def __init__(
        self,
        kpi_templates: List[KpiTemplate],
        algo_templates: Dict[str, AlgorithmTemplate],
        data_manager: DataManager,
        logger: Logger | None = None,
    ):
        self.logger = logger
        self._kpi_templates = kpi_templates
        # self._algo_templates = algo_templates
        self.algorithm_factory = AlgorithmFactory(
            algo_templates=algo_templates, logger=logger
        )
        self._data_manager = data_manager

    def log(self, msg: str):
        if self.logger:
            self.logger.log(msg)

    @property
    def available_algorithms(self) -> List[str]:
        return self.algorithm_factory.available_algorithms

    def create(
        self,
        tag: str,
        dataset_key: str,
        algo_name: str,
        algo_params: Optional[dict] = None,
    ) -> Scenario:
        if algo_params is None:
            algo_params = {}

        assert (
            algo_name in self.available_algorithms
        ), f"Algorithm '{algo_name}' not found."
        assert (
            dataset_key in self._data_manager.get_data_keys()
        ), f"Data '{dataset_key}' not found."

        algorithm = self.algorithm_factory.create(
            input_name=algo_name,
            input_params=algo_params,
        )

        kpi_dict = build_kpis(self._kpi_templates)

        scenario = Scenario(
            tag=tag,
            input_data=self._data_manager.get_data(dataset_key),
            kpis=kpi_dict,
            algorithm=algorithm,
        )
        self.log(f"Scenario '{scenario.tag}' created.")
        return scenario
