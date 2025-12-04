from typing import Dict, List, Optional, Type

from algomancy.scenarioengine.algorithmfactory import AlgorithmFactory
from algomancy.dashboardlogger import Logger
from algomancy.scenarioengine.basealgorithm import ALGORITHM
from algomancy.scenarioengine.keyperformanceindicator import BASE_KPI
from algomancy.scenarioengine.kpifactory import KpiFactory
from algomancy.scenarioengine.scenario import Scenario
from algomancy.dataengine import DataManager


class ScenarioFactory:
    """
    Creates scenarios, builds algorithms and KPIs, and performs parameter validation.
    """

    def __init__(
        self,
        kpi_templates: Dict[str, Type[BASE_KPI]],
        algo_templates: Dict[str, Type[ALGORITHM]],
        data_manager: DataManager,
        logger: Logger | None = None,
    ):
        self.logger = logger
        self._kpi_factory = KpiFactory(kpi_templates)
        self._algorithm_factory = AlgorithmFactory(algo_templates, logger)
        self._data_manager = data_manager

    @property
    def available_algorithms(self) -> List[str]:
        return self._algorithm_factory.available_algorithms

    @property
    def algo_templates(self) -> Dict[str, Type[ALGORITHM]]:
        return self._algorithm_factory.templates

    def log(self, msg: str):
        if self.logger:
            self.logger.log(msg)

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

        algorithm = self._algorithm_factory.create(
            input_name=algo_name,
            input_params=algo_params,
        )

        kpi_dict = self._kpi_factory.create_all()

        scenario = Scenario(
            tag=tag,
            input_data=self._data_manager.get_data(dataset_key),
            kpis=kpi_dict,
            algorithm=algorithm,
        )
        self.log(f"Scenario '{scenario.tag}' created.")
        return scenario
