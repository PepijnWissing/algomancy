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
from algomancy_scenario import ALGORITHM, BASE_KPI
from algomancy_content import LibraryManager as library

from algomancy_gui.stylingconfigurator import StylingConfigurator
from algomancy_scenario.core_configuration import CoreConfiguration


class AppConfiguration(CoreConfiguration):
    """
    Central configuration object for the Algomancy dashboard.

    Construct with your choices, validation runs on creation. Use `as_dict()`
    to obtain the dictionary expected by `DashLauncher.build()` and
    `SettingsManager`.
    """

    def __init__(
        self,
        # === path specifications ===
        assets_path: str = "assets",  # gui
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
        home_page: HomePage | str = "standard",  # gui
        data_page: DataPage | str = "placeholder",  # gui
        scenario_page: ScenarioPage | str = "placeholder",  # gui
        compare_page: ComparePage | str = "placeholder",  # gui
        overview_page: OverviewPage | str = "standard",  # gui
        # === styling configuration ===
        styling_config: Any | None = StylingConfigurator.get_cqm_config(),  # gui
        use_cqm_loader: bool = False,  # gui
        # === misc dashboard configurations ===
        title: str = "Algomancy Dashboard",
        host: str | None = None,  # gui/api
        port: int | None = None,  # gui/api
        # === page configurations ===
        compare_default_open: List[str] | None = None,  # gui
        compare_ordered_list_components: List[str] | None = None,  # gui
        use_data_page_spinner: bool = True,  # gui
        use_scenario_page_spinner: bool = True,  # gui
        use_compare_page_spinner: bool = True,  # gui
        allow_parameter_upload_from_file: bool = False,  # gui
        # === authentication ===
        use_authentication: bool = False,  # gui
    ):
        # initialize core part
        super().__init__(
            data_path=data_path,
            has_persistent_state=has_persistent_state,
            save_type=save_type,
            data_object_type=data_object_type,
            etl_factory=etl_factory,
            kpi_templates=kpi_templates,
            algo_templates=algo_templates,
            input_configs=input_configs,
            autocreate=autocreate,
            default_algo=default_algo,
            default_algo_params_values=default_algo_params_values,
            autorun=autorun,
            title=title,
        )

        # paths (GUI)
        self.assets_path = assets_path

        # content + callbacks
        self.home_page = home_page
        self.data_page = data_page
        self.scenario_page = scenario_page
        self.compare_page = compare_page
        self.overview_page = overview_page

        # styling + misc
        self.styling_config = styling_config
        self.use_cqm_loader = use_cqm_loader
        self.host = host or self._get_default_host()
        self.port = port or 8050

        # settings pages
        self.compare_default_open = compare_default_open or []
        self.compare_ordered_list_components = compare_ordered_list_components or []
        self.show_loading_on_datapage = use_data_page_spinner
        self.show_loading_on_scenariopage = use_scenario_page_spinner
        self.show_loading_on_comparepage = use_compare_page_spinner
        self.allow_parameter_upload_from_file = allow_parameter_upload_from_file

        # auth
        self.use_authentication = use_authentication

        # validate GUI-specific pieces immediately (core validated in super())
        self._validate_gui()

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
            "allow_param_upload_by_file": self.allow_parameter_upload_from_file,
            # === authentication ===
            "use_authentication": self.use_authentication,
        }

    # validation helpers (GUI layer)
    def _validate_gui(self) -> None:
        self._validate_paths_gui()
        self._validate_values_gui()
        self._validate_pages()
        self._validate_page_configurations()

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

    def _validate_paths_gui(self) -> None:
        if self.assets_path is None or self.assets_path == "":
            raise ValueError("assets_path must be provided")
        if not os.path.isdir(self.assets_path):
            raise ValueError(
                f"assets_path does not exist or is not a directory: {self.assets_path}"
            )

    def _validate_values_gui(self) -> None:
        # booleans allowed to be False, but must not be None if specified
        if self.use_authentication is None:
            raise ValueError(
                "Boolean configuration 'use_authentication' must be set to True or False, not None"
            )

        # host and port (host may be filled elsewhere; allow None)
        if self.port is not None:
            if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
                raise ValueError("port must be an integer between 1 and 65535")

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
