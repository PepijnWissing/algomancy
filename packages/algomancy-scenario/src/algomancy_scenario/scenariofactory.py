from typing import Dict, List, Optional, Tuple, Type

from algomancy_utils.logger import Logger
from algomancy_utils.baseparameterset import BaseParameterSet
from algomancy_data import DataManager

from .algorithmfactory import AlgorithmFactory
from .basealgorithm import ALGORITHM
from .keyperformanceindicator import BASE_KPI
from .kpifactory import KpiFactory
from .scenario import Scenario


class ScenarioFactory:
    """
    Creates scenarios, builds algorithms and KPIs, and performs parameter validation.
    """

    def __init__(
        self,
        kpis: Dict[str, Type[BASE_KPI]],
        algorithms: Dict[str, Type[ALGORITHM]],
        data_manager: DataManager,
        logger: Logger | None = None,
    ):
        self.logger = logger
        self._kpi_factory = KpiFactory(kpis)
        self._algorithm_factory = AlgorithmFactory(algorithms, logger)
        self._data_manager = data_manager

    @property
    def available_algorithms(self) -> List[str]:
        return self._algorithm_factory.available_algorithms

    @property
    def available_kpis(self) -> List[str]:
        return self._kpi_factory.available_kpis

    @property
    def algorithms(self) -> Dict[str, Type[ALGORITHM]]:
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
        data_params: Optional[dict] = None,
    ) -> Scenario:
        if algo_params is None:
            algo_params = {}
        if data_params is None:
            data_params = {}

        assert algo_name in self.available_algorithms, (
            f"Algorithm '{algo_name}' not found."
        )
        assert dataset_key in self._data_manager.get_data_keys(), (
            f"Data '{dataset_key}' not found."
        )

        algorithm = self._algorithm_factory.create(
            input_name=algo_name,
            input_params=algo_params,
        )

        kpi_dict = self._kpi_factory.create_all()

        input_data = self._data_manager.get_data(dataset_key)
        data_param_set = input_data.initialize_data_parameters()
        if data_params:
            data_param_set.set_validated_values(data_params)

        scenario = Scenario(
            tag=tag,
            input_data=input_data,
            kpis=kpi_dict,
            algorithm=algorithm,
            data_params=data_param_set,
        )
        self.log(f"Scenario '{scenario.tag}' created.")
        return scenario

    def get_associated_parameters(
        self, algo_name: str, dataset_key: Optional[str] = None
    ) -> Tuple[BaseParameterSet, BaseParameterSet]:
        """Return the (algo_params, data_params) templates for a scenario.

        The algo params template comes from the algorithm class; the data
        params template comes from the selected data source's
        ``initialize_data_parameters``. ``dataset_key`` is optional only so
        callers that don't yet know the dataset can still introspect the algo
        side — the data side falls back to ``EmptyParameters``.
        """
        algo_params = self._algorithm_factory.get_parameters(algo_name)
        if (
            dataset_key is not None
            and dataset_key in self._data_manager.get_data_keys()
        ):
            data_params = self._data_manager.get_data(
                dataset_key
            ).initialize_data_parameters()
        else:
            from algomancy_utils.baseparameterset import EmptyParameters

            data_params = EmptyParameters()
        return algo_params, data_params
