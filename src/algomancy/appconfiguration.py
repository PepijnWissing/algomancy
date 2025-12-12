import platform
from typing import Any, Dict, List, Type
import os

from algomancy_data import InputFileConfiguration, BASE_DATA_BOUND
from algomancy_gui.page import (
    HomePage,
    ScenarioPage,
    ComparePage,
    OverviewPage,
    DataPage,
)
from algomancy_scenario import AlgorithmFactory, ALGORITHM, BASE_KPI
from algomancy_content import LibraryManager as library

from algomancy_gui.stylingconfigurator import StylingConfigurator


class AppConfiguration:
    """
    Central configuration object for the Algomancy dashboard.

    Construct with your choices, validation runs on creation. Use `as_dict()`
    to obtain the dictionary expected by `DashLauncher.build()` and
    `SettingsManager`.
    """

    def __init__(
        self,
        # === path specifications ===
        assets_path: str = "assets",
        data_path: str = "data",
        # === data manager configuration ===
        has_persistent_state: bool = False,
        save_type: str | None = "json",
        data_object_type: type[BASE_DATA_BOUND] | None = None,
        # === scenario manager configuration ===
        etl_factory: Any | None = None,
        kpi_templates: Dict[str, Type[BASE_KPI]] | None = None,
        algo_templates: Dict[str, Type[ALGORITHM]] | None = None,
        input_configs: List[InputFileConfiguration] | None = None,
        # === auto start/create features ===
        autocreate: bool | None = None,
        default_algo: str | None = None,
        default_algo_params_values: Dict[str, Any] | None = None,
        autorun: bool | None = None,
        # === content functions ===
        home_page: HomePage | str = "standard",
        data_page: DataPage | str = "placeholder",
        scenario_page: ScenarioPage | str = "placeholder",
        compare_page: ComparePage | str = "placeholder",
        overview_page: OverviewPage | str = "standard",
        # === styling configuration ===
        styling_config: Any | None = StylingConfigurator.get_cqm_config(),
        use_cqm_loader: bool = False,
        # === misc dashboard configurations ===
        title: str = "Algomancy Dashboard",
        host: str | None = None,
        port: int | None = None,
        # === page configurations ===
        compare_default_open: List[str] | None = None,
        compare_ordered_list_components: List[str] | None = None,
        use_data_page_spinner: bool = True,
        use_scenario_page_spinner: bool = True,
        use_compare_page_spinner: bool = True,
        # === authentication ===
        use_authentication: bool = False,
    ):
        # paths
        self.assets_path = assets_path
        self.data_path = data_path

        # data / scenario manager
        self.has_persistent_state = has_persistent_state
        self.save_type = save_type
        self.data_object_type = data_object_type
        self.etl_factory = etl_factory
        self.kpi_templates = kpi_templates
        self.algo_templates = algo_templates
        self.input_configs = input_configs
        self.autocreate = autocreate
        self.default_algo = default_algo
        self.default_algo_params_values = default_algo_params_values
        self.autorun = autorun

        # content + callbacks
        self.home_page = home_page
        self.data_page = data_page
        self.scenario_page = scenario_page
        self.compare_page = compare_page
        self.overview_page = overview_page

        # styling + misc
        self.styling_config = styling_config
        self.use_cqm_loader = use_cqm_loader
        self.title = title
        self.host = host or self._get_default_host()
        self.port = port or 8050

        # settings pages
        self.compare_default_open = compare_default_open or []
        self.compare_ordered_list_components = compare_ordered_list_components or []
        self.show_loading_on_datapage = use_data_page_spinner
        self.show_loading_on_scenariopage = use_scenario_page_spinner
        self.show_loading_on_comparepage = use_compare_page_spinner

        # auth
        self.use_authentication = use_authentication

        # validate immediately
        self._validate()

    # public API
    def as_dict(self) -> Dict[str, Any]:
        return {
            # === path specifications ===
            "assets_path": self.assets_path,
            "data_path": self.data_path,
            # === data manager configuration ===
            "has_persistent_state": self.has_persistent_state,
            "save_type": self.save_type,
            "data_object_type": self.data_object_type,
            # === scenario manager configuration ===
            "etl_factory": self.etl_factory,
            "kpi_templates": self.kpi_templates,
            "algo_templates": self.algo_templates,
            "input_configs": self.input_configs,
            "autocreate": self.autocreate,
            "default_algo": self.default_algo,
            "default_algo_params_values": self.default_algo_params_values,
            "autorun": self.autorun,
            # === content functions ===
            "home_page": self.home_page,
            "data_page": self.data_page,
            "scenario_page": self.scenario_page,
            "compare_page": self.compare_page,
            "overview_page": self.overview_page,
            # === styling configuration ===
            "styling_config": self.styling_config,
            "use_cqm_loader": self.use_cqm_loader,
            # === misc dashboard configurations ===
            "title": self.title,
            "host": self.host,
            "port": self.port,
            # === page configurations ===
            "compare_default_open": self.compare_default_open,
            "compare_ordered_list_components": self.compare_ordered_list_components,
            "show_loading_on_datapage": self.show_loading_on_datapage,
            "show_loading_on_scenariopage": self.show_loading_on_scenariopage,
            "show_loading_on_comparepage": self.show_loading_on_comparepage,
            # === authentication ===
            "use_authentication": self.use_authentication,
        }

    # validation helpers
    def _validate(self) -> None:
        self._validate_paths()
        self._validate_values()
        self._validate_pages()
        self._validate_page_configurations()
        self._validate_algorithm_parameters()

    def _validate_paths(self) -> None:
        if self.assets_path is None or self.assets_path == "":
            raise ValueError("assets_path must be provided")
        if not os.path.isdir(self.assets_path):
            raise ValueError(
                f"assets_path does not exist or is not a directory: {self.assets_path}"
            )

        if self.has_persistent_state:
            if not os.path.isdir(self.data_path):
                raise ValueError(
                    f"data_path does not exist or is not a directory: {self.data_path}"
                )
            if self.data_path is None or self.data_path == "":
                raise ValueError("data_path must be provided")

    def _validate_values(self) -> None:
        # required non-null entries for scenario/data managers
        required_fields = {
            "etl_factory": self.etl_factory,
            "kpi_templates": self.kpi_templates,
            "algo_templates": self.algo_templates,
            "input_configs": self.input_configs,
            "data_object_type": self.data_object_type,
        }
        missing = [k for k, v in required_fields.items() if v is None]
        if missing:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing)}"
            )

        # booleans allowed to be False, but must not be None if specified
        for name, val in {
            "has_persistent_state": self.has_persistent_state,
            "autocreate": self.autocreate,
            "autorun": self.autorun,
            "use_authentication": self.use_authentication,
        }.items():
            if val is None:
                raise ValueError(
                    f"Boolean configuration '{name}' must be set to True or False, not None"
                )

        # save type
        if self.save_type is None:
            raise ValueError("save_type must be set to 'json' or 'parquet'")
        if self.save_type not in {"json", "parquet"}:
            raise ValueError("save_type must be either 'json' or 'parquet'")

        # title
        if not isinstance(self.title, str) or self.title.strip() == "":
            raise ValueError("title must be a non-empty string")

        # host and port (host may be filled elsewhere; allow None)
        if self.port is not None:
            if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
                raise ValueError("port must be an integer between 1 and 65535")

    def _validate_pages(self):
        # fetch pages that were passed as str
        home, data, scenario, compare, overview = library.get_pages(self.as_dict())

        # check home page attributes
        assert hasattr(home, "create_content")
        assert hasattr(
            home, "register_callbacks"
        ), "home_page.register_callbacks must be a function"

        # check data page attributes
        assert hasattr(
            data, "create_content"
        ), "data_page.create_content must be a function"
        assert hasattr(
            data, "register_callbacks"
        ), "data_page.register_callbacks must be a function"

        # check scenario page attributes
        assert hasattr(
            scenario, "create_content"
        ), "scenario_page.create_content must be a function"
        assert hasattr(
            scenario, "register_callbacks"
        ), "scenario_page.register_callbacks must be a function"

        # check compare page attributes
        assert hasattr(compare, "create_side_by_side_content"), (
            "compare_page.create_side_by_side_content " "must be a function"
        )
        assert hasattr(
            compare, "create_compare_section"
        ), "compare_page.create_compare_section must be a function"
        assert hasattr(
            compare, "create_details_section"
        ), "compare_page.create_details_section must be a function"
        assert hasattr(
            compare, "register_callbacks"
        ), "compare_page.register_callbacks must be a function"

        # check overview page attributes
        assert hasattr(
            overview, "create_content"
        ), "overview_page.create_content must be a function"
        assert hasattr(
            overview, "register_callbacks"
        ), "scenario_page.register_callbacks must be a function"

    def _validate_page_configurations(self) -> None:
        # basic type checks for collections
        if not isinstance(self.compare_default_open, list):
            raise ValueError("compare_default_open must be a list of strings")
        if not isinstance(self.compare_ordered_list_components, list):
            raise ValueError(
                "compare_ordered_list_components must be a list of strings"
            )

        # ensure all strings are valid
        admissible_values = ["side-by-side", "kpis", "compare", "details"]
        for component in self.compare_default_open:
            if not isinstance(component, str):
                raise ValueError(
                    f"compare_default_open must be a list of strings, but contains {component}"
                )
            if component not in admissible_values:
                raise ValueError(
                    f"compare_default_open contains invalid component: {component}"
                )

        for component in self.compare_ordered_list_components:
            if not isinstance(component, str):
                raise ValueError(
                    f"compare_ordered_list_components must be a list of strings, but contains {component}"
                )
            if component not in admissible_values:
                raise ValueError(
                    f"compare_ordered_list_components contains invalid component: {component}"
                )

        # ensure all strings are unique
        if len(self.compare_default_open) != len(set(self.compare_default_open)):
            raise ValueError("compare_default_open contains duplicate values")
        if len(self.compare_ordered_list_components) != len(
            set(self.compare_ordered_list_components)
        ):
            raise ValueError(
                "compare_ordered_list_components contains duplicate values"
            )

    def _validate_algorithm_parameters(self) -> None:
        if self.autocreate:
            tmp_factory = AlgorithmFactory(self.algo_templates)
            test_algorithm = tmp_factory.create(
                self.default_algo, self.default_algo_params_values
            )
            assert test_algorithm.healthcheck(), "Failed to create default algorithm"
        else:
            pass

    @staticmethod
    def _get_default_host() -> str:
        if platform.system() == "Windows":
            host = "127.0.0.1"  # default host for windows
        else:
            host = "0.0.0.1"  # default host for linux
        return host

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "AppConfiguration":
        return cls(**config)


# stub_configuration = AppConfiguration(
#     etl_factory=PlaceholderETLFactory,
#     kpi_templates={
#         str(PlaceholderKPI.name): PlaceholderKPI,
#     },
#     algo_templates={
#         str(PlaceholderAlgorithm.name): PlaceholderAlgorithm,
#     },
#     input_configs=[placeholder_input_config],
# )
