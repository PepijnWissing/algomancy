from typing import Any, Dict

from algomancy_utils import Logger
from .comparepageconfig import ComparePageConfig
from .featureconfig import FeatureConfig
from .pageconfig import PageConfig
from .serverconfig import ServerConfig
from .stylingconfig import StylingConfig
from algomancy_scenario.core_configuration import CoreConfig


class AppConfig:
    """
    Central configuration object for the Algomancy dashboard.

    This class composes various configuration groups for organizing
    dashboard settings by domain: core functionality, server, paths,
    pages, styling, and features.

    Args:
        core_config: Core configuration (data, scenarios, algorithms).
            If None, will be created from individual parameters.
        server_config: Server and deployment settings.
        path_config: File system paths.
        page_config: Page implementations and UI behavior.
        compare_page_config: Compare page specific settings.
        styling_config: Styling and UI customization.
        feature_config: Feature flags and optional functionality.

    Example:
        Using sub-configurations:

        >>> from algomancy_gui.configuration.appconfig import AppConfig
        >>> from algomancy_gui.configuration.serverconfig import ServerConfig
        >>> from algomancy_gui.configuration.comparepageconfig import ComparePageConfig
        >>> config = AppConfig(
        ...     core_config=CoreConfig(
        ...         etl_factory=ExampleETLFactory,
        ...         kpi_templates=kpi_templates,
        ...         algo_templates=algorithm_templates,
        ...     ),
        ...     server_config=ServerConfig(port=9000),
        ...     compare_page_config=ComparePageConfig(
        ...         default_open=["side-by-side", "kpis"]
        ...     ),
        ... )
        >>> config.server.port
        9000
        >>> config.core.etl_factory
        <ExampleETLFactory>
    """

    def __init__(
        self,
        # Sub-configuration objects
        core_config: CoreConfig | None = None,
        server_config: ServerConfig | None = None,
        # path_config: PathConfig | None = None,
        page_config: PageConfig | None = None,
        compare_page_config: ComparePageConfig | None = None,
        styling_config: StylingConfig | None = None,
        feature_config: FeatureConfig | None = None,
        # Flat parameters for backwards compatibility and convenience
        **kwargs,
    ):
        """
        Initialize AppConfig with sub-configs or flat parameters.

        Sub-config objects take precedence over flat kwargs. If a sub-config
        is not provided, it will be created from relevant kwargs.
        """
        # Initialize core configuration
        if core_config is not None:
            self.core = core_config
        else:
            # Extract core config parameters from kwargs
            core_params = self._extract_kwargs(kwargs, CoreConfig.__init__)
            self.core = CoreConfig(**core_params)

        # Initialize GUI sub-configurations
        if server_config:
            self.server = server_config
        else:
            logger = Logger()
            logger.warning(
                "DeprecatedWarning: Falling back to configuration via AppConfig keywords. "
                "Use ServerConfig instead."
            )
            self.server = ServerConfig(**self._extract_dc_kwargs(kwargs, ServerConfig))

        if page_config:
            self.pages = page_config
        else:
            logger = Logger()
            logger.warning(
                "DeprecatedWarning: Falling back to configuration via AppConfig keywords. "
                "Use PageConfig instead."
            )
            self.pages = PageConfig(**self._extract_dc_kwargs(kwargs, PageConfig))

        if compare_page_config:
            self.compare = compare_page_config
        else:
            logger = Logger()
            logger.warning(
                "DeprecatedWarning: Falling back to configuration via AppConfig keywords. "
                "Use ComparePageConfig instead."
            )
            self.compare = compare_page_config or ComparePageConfig(
                **self._extract_dc_kwargs(kwargs, ComparePageConfig)
            )

        if styling_config:
            self.styling = styling_config
        else:
            logger = Logger()
            logger.warning(
                "DeprecatedWarning: Falling back to configuration via AppConfig keywords. "
                "Use StylingConfig instead."
            )
            self.styling = styling_config or StylingConfig(
                **self._extract_dc_kwargs(kwargs, StylingConfig)
            )

        if feature_config:
            self.features = feature_config
        else:
            logger = Logger()
            logger.warning(
                "DeprecatedWarning: Falling back to configuration via AppConfig keywords. "
                "Use FeatureConfig instead."
            )
            self.features = feature_config or FeatureConfig(
                **self._extract_dc_kwargs(kwargs, FeatureConfig)
            )

    @staticmethod
    def _extract_kwargs(kwargs: dict, func) -> dict:
        """Extract relevant kwargs for a function signature."""
        import inspect

        sig = inspect.signature(func)
        param_names = {p.name for p in sig.parameters.values() if p.name != "self"}
        return {k: v for k, v in kwargs.items() if k in param_names}

    @staticmethod
    def _extract_dc_kwargs(kwargs: dict, dataclass_type) -> dict:
        """Extract relevant kwargs for a dataclass."""
        import dataclasses

        if not dataclasses.is_dataclass(dataclass_type):
            return {}
        field_names = {f.name for f in dataclasses.fields(dataclass_type)}

        # Handle special mappings for backwards compatibility
        mappings = {
            "compare_default_open": "default_open",
            "compare_ordered_list_components": "ordered_components",
        }

        result = {}
        for k, v in kwargs.items():
            # Check direct match
            if k in field_names:
                result[k] = v
            # Check mapped names
            elif k in mappings and mappings[k] in field_names:
                result[mappings[k]] = v

        return result

    def as_dict(self) -> Dict[str, Any]:
        """
        Serialize the configuration to a flat dictionary.

        Converts all sub-configuration attributes into a single dictionary
        representation suitable for JSON serialization, storage, or passing
        to other components like `GuiLauncher.build()` or `SettingsManager`.

        Returns:
            A dictionary containing all configuration parameters as key-value pairs.

        Example:
            >>> config = AppConfig(
            ...     core_config=CoreConfig(title="My Dashboard"),
            ...     server_config=ServerConfig(port=9000),
            ... )
            >>> config_dict = config.as_dict()
            >>> config_dict["port"]
            9000
            >>> config_dict["title"]
            'My Dashboard'
        """
        result = {}

        # Merge all sub-config dictionaries
        result.update(self.core.as_dict())
        result.update(self.server.as_dict())
        result.update(self.pages.as_dict())
        result.update(self.compare.as_dict())
        result.update(self.styling.as_dict())
        result.update(self.features.as_dict())

        return result

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "AppConfig":
        """
        Create an AppConfig instance from a flat dictionary.

        This factory method reconstructs an AppConfig object from a
        dictionary representation, typically one created by `as_dict()`.

        Args:
            config: Dictionary containing configuration parameters.

        Returns:
            A new AppConfig instance initialized with the provided values.

        Example:
            >>> config_dict = {
            ...     "title": "My Dashboard",
            ...     "port": 9000,
            ...     "use_sessions": True,
            ... }
            >>> app_config = AppConfig.from_dict(config_dict)
            >>> app_config.server.port
            9000
        """
        return cls(**config)
