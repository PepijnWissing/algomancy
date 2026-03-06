from dataclasses import dataclass
from typing import Dict, Any

from algomancy_content import (
    BaseHomePage,
    BaseDataPage,
    BaseScenarioPage,
    BaseComparePage,
    BaseOverviewPage,
    LibraryManager as library,
)


@dataclass
class PageConfig:
    """Page implementations and UI behavior."""

    home_page: BaseHomePage | str = "standard"
    data_page: BaseDataPage | str = "placeholder"
    scenario_page: BaseScenarioPage | str = "placeholder"
    compare_page: BaseComparePage | str = "placeholder"
    overview_page: BaseOverviewPage | str = "standard"

    def __post_init__(self):
        self._validate()

    def _validate(self) -> None:
        """
        Validate page implementations have required methods.

        Args:
            config_dict: Full configuration dictionary for page resolution.
        """
        # Fetch pages that were passed as str
        home, data, scenario, compare, overview = library.get_pages(self.as_dict())

        # Check home page attributes
        assert hasattr(home, "create_content"), (
            "home_page must have create_content method"
        )
        assert hasattr(home, "register_callbacks"), (
            "home_page must have register_callbacks method"
        )

        # Check data page attributes
        assert hasattr(data, "create_content"), (
            "data_page must have create_content method"
        )
        assert hasattr(data, "register_callbacks"), (
            "data_page must have register_callbacks method"
        )

        # Check scenario page attributes
        assert hasattr(scenario, "create_content"), (
            "scenario_page must have create_content method"
        )
        assert hasattr(scenario, "register_callbacks"), (
            "scenario_page must have register_callbacks method"
        )

        # Check compare page attributes
        assert hasattr(compare, "create_side_by_side_content"), (
            "compare_page must have create_side_by_side_content method"
        )
        assert hasattr(compare, "create_compare_section"), (
            "compare_page must have create_compare_section method"
        )
        assert hasattr(compare, "create_details_section"), (
            "compare_page must have create_details_section method"
        )
        assert hasattr(compare, "register_callbacks"), (
            "compare_page must have register_callbacks method"
        )

        # Check overview page attributes
        assert hasattr(overview, "create_content"), (
            "overview_page must have create_content method"
        )
        assert hasattr(overview, "register_callbacks"), (
            "overview_page must have register_callbacks method"
        )

    def as_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "home_page": self.home_page,
            "data_page": self.data_page,
            "scenario_page": self.scenario_page,
            "compare_page": self.compare_page,
            "overview_page": self.overview_page,
        }
