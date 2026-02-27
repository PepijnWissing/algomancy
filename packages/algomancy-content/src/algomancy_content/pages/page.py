"""
Base page classes for building Algomancy content pages.

This module provides abstract base classes that define the interface for different
types of pages in the Algomancy application. Each page is responsible for rendering
a specific section of the user interface, and thus requires a specific set of methods
and attributes to function correctly. Some of the central logic (e.g., creating and
selecting a scenario) is handled by Algomancy, but the user is required to specify
the way that a scenario is visualized.


All page classes inherit from BasePage and must implement the required abstract methods
to define their content and behavior. These classes are designed to be subclassed by
custom implementations that provide specific content and callback functionality.
"""

from abc import ABC, abstractmethod
from typing import List
from dash import html

from algomancy_data import BASE_DATA_BOUND
from algomancy_scenario import Scenario


class BasePage(ABC):
    """
    Abstract base class for all page types in the Algomancy application.

    This class defines the minimal interface that all page classes must implement.
    Pages are responsible for registering their own callbacks with the Dash application
    to handle user interactions and dynamic content updates.

    All concrete page implementations must inherit from this class (or one of its
    subclasses) and implement the required abstract methods.

    Example:
        >>> class CustomPage(BasePage):
        ...     @staticmethod
        ...     def register_callbacks():
        ...         # Register Dash callbacks for this page
        ...         @app.callback(...)
        ...         def update_content():
        ...             pass
    """

    @staticmethod
    @abstractmethod
    def register_callbacks() -> None:
        """
        Register Dash callbacks for this page.

        This method should be implemented to register all callbacks required for
        the page's interactive functionality. Callbacks are registered with the
        Dash application instance to handle user inputs, update displays, and
        manage page state.

        Raises:
            NotImplementedError: Abstract method must be implemented

        Note:
            If your page does not require any additional callbacks, you can implement
            the `register_callbacks` method as a pass statement. Not offering any
            implementation will cause the app to fail during callback registration.

        Example:
            >>> @staticmethod
            >>> def register_callbacks():
            ...     @app.callback(
            ...         Output('output-div', 'children'),
            ...         Input('input-button', 'n_clicks')
            ...     )
            ...     def update_output(n_clicks):
            ...         return f"Button clicked {n_clicks} times"
        """
        raise NotImplementedError("Abstract method")


class BaseHomePage(BasePage, ABC):
    """
    Abstract base class for home pages in the Algomancy application.

    Home pages typically serve as the landing page or dashboard of the application,
    providing an overview or entry point to the application's main features. This
    class extends BasePage with a method to create static content that doesn't
    depend on specific data or scenarios.

    Concrete implementations must provide both the content creation method and
    callback registration inherited from BasePage.

    Example:
        >>> class MyHomePage(BaseHomePage):
        ...     @staticmethod
        ...     def create_content():
        ...         return html.Div([
        ...             html.H1("Welcome to Algomancy"),
        ...             html.P("Select a scenario to begin.")
        ...         ])
        ...
        ...     @staticmethod
        ...     def register_callbacks():
        ...         # Register any interactive callbacks
        ...         pass
    """

    @staticmethod
    @abstractmethod
    def create_content() -> html.Div:
        """
        Create the content for the home page.

        This method should return a Dash HTML component tree that represents
        the visual content of the home page. The content is typically static
        or does not depend on external data sources.

        Returns:
            html.Div: A Dash Div component containing the home page layout and content.

        Raises:
            NotImplementedError: Abstract method must be implemented

        Example:
            >>> @staticmethod
            >>> def create_content():
            ...     return html.Div([
            ...         html.H1("Dashboard", className="header"),
            ...         html.Div([
            ...             html.Button("Get Started", id="start-button"),
            ...             html.Div(id="output")
            ...         ], className="content")
            ...     ])
        """
        raise NotImplementedError("Abstract method")


class BaseDataPage(BasePage, ABC):
    """
    Abstract base class for data-focused pages in the Algomancy application.

    Data pages display and interact with data objects that conform to the BASE_DATA_BOUND
    type. These pages are designed to visualize, analyze, or manipulate data sets
    independently of specific scenarios.

    The data parameter can be any type that satisfies the BASE_DATA_BOUND constraint,
    allowing for flexible data handling while maintaining type safety.

    Concrete implementations must provide both the content creation method with
    data parameter and callback registration inherited from BasePage.

    Example:
        >>> class DataVisualizationPage(BaseDataPage):
        ...     @staticmethod
        ...     def create_content(data):
        ...         return html.Div([
        ...             html.H2("Data Analysis"),
        ...             html.Table([
        ...                 html.Tr([html.Td(str(item)) for item in data])
        ...             ]),
        ...             dcc.Graph(figure=create_figure_from_data(data))
        ...         ])
        ...
        ...     @staticmethod
        ...     def register_callbacks():
        ...         @app.callback(...)
        ...         def update_graph():
        ...             pass
    """

    @staticmethod
    @abstractmethod
    def create_content(data: BASE_DATA_BOUND) -> html.Div:
        """
        Create the content for the data page based on the provided data.

        This method receives a data object and should return a Dash HTML component
        tree that visualizes or presents the data in a meaningful way. The data
        parameter is type-bounded by BASE_DATA_BOUND, ensuring compatibility with
        the Algomancy data framework.

        Args:
            data: The data object to display on this page. Must conform to the
                BASE_DATA_BOUND type constraint.

        Returns:
            html.Div: A Dash Div component containing the data page layout and content.

        Raises:
            NotImplementedError: Abstract method must be implemented

        Example:
            >>> @staticmethod
            >>> def create_content(data):
            ...     return html.Div([
            ...         html.H3(f"Data Summary: {len(data)} items"),
            ...         html.Pre(json.dumps(data.to_dict(), indent=2)),
            ...         html.Button("Export Data", id="export-btn")
            ...     ])
        """
        raise NotImplementedError("Abstract method")


class BaseScenarioPage(BasePage, ABC):
    """
    Abstract base class for scenario-focused pages in the Algomancy application.

    Scenario pages display and interact with individual Scenario objects, providing
    views for scenario configuration, execution results, analysis, or other
    scenario-specific functionality. These pages are central to the Algomancy
    workflow, allowing users to work with different simulation or analysis scenarios.

    Concrete implementations must provide both the content creation method with
    scenario parameter and callback registration inherited from BasePage.

    Example:
        >>> class ScenarioDetailPage(BaseScenarioPage):
        ...     @staticmethod
        ...     def create_content(scenario):
        ...         return html.Div([
        ...             html.H2(f"Scenario: {scenario.name}"),
        ...             html.P(f"Status: {scenario.status}"),
        ...             html.Div([
        ...                 html.Label("Parameters:"),
        ...                 html.Pre(json.dumps(scenario.parameters, indent=2))
        ...             ]),
        ...             html.Button("Run Scenario", id="run-btn")
        ...         ])
        ...
        ...     @staticmethod
        ...     def register_callbacks():
        ...         @app.callback(...)
        ...         def run_scenario():
        ...             pass
    """

    @staticmethod
    @abstractmethod
    def create_content(scenario: Scenario) -> html.Div:
        """
        Create the content for the scenario page based on the provided scenario.

        This method receives a Scenario object and should return a Dash HTML component
        tree that displays scenario information, controls, and results. The content
        can include scenario parameters, execution status, visualizations of results,
        or any other scenario-relevant information.

        Args:
            scenario: The Scenario object to display on this page, containing
                configuration, state, and results data.

        Returns:
            html.Div: A Dash Div component containing the scenario page layout and content.

        Raises:
            NotImplementedError: Abstract method must be implemented

        Example:
            >>> @staticmethod
            >>> def create_content(scenario):
            ...     return html.Div([
            ...         html.H3(scenario.name, className="scenario-title"),
            ...         html.Div([
            ...             html.Span("Created: ", className="label"),
            ...             html.Span(scenario.created_date)
            ...         ]),
            ...         dcc.Graph(id="scenario-results", figure=scenario.get_figure()),
            ...         html.Button("Edit", id="edit-scenario-btn")
            ...     ])
        """
        raise NotImplementedError("Abstract method")


class BaseComparePage(BasePage, ABC):
    """
    Abstract base class for comparison pages in the Algomancy application.

    Comparison pages enable side-by-side analysis of two scenarios, allowing users
    to compare parameters, results, and other attributes. This class defines three
    distinct content sections:

    1. Side-by-side content: Individual scenario views displayed in parallel
    2. Compare section: Consolidated comparison view of both scenarios
    3. Details section: Detailed analysis and differences between scenarios

    This multi-section approach provides flexible comparison interfaces that can
    highlight differences, similarities, and relative performance between scenarios.

    Concrete implementations must provide all three content creation methods plus
    callback registration inherited from BasePage.

    Example:
        >>> class ScenarioComparePage(BaseComparePage):
        ...     @staticmethod
        ...     def create_side_by_side_content(scenario, side):
        ...         return html.Div([
        ...             html.H4(f"{side.upper()}: {scenario.name}"),
        ...             html.P(f"Result: {scenario.result}")
        ...         ], className=f"compare-{side}")
        ...
        ...     @staticmethod
        ...     def create_compare_section(left, right):
        ...         return html.Div([
        ...             html.H3("Comparison"),
        ...             html.Table([
        ...                 html.Tr([html.Td("Left"), html.Td(left.name)]),
        ...                 html.Tr([html.Td("Right"), html.Td(right.name)])
        ...             ])
        ...         ])
        ...
        ...     @staticmethod
        ...     def create_details_section(left, right):
        ...         return html.Div([
        ...             html.H3("Detailed Analysis"),
        ...             html.P(f"Difference: {abs(left.result - right.result)}")
        ...         ])
        ...
        ...     @staticmethod
        ...     def register_callbacks():
        ...         pass
    """

    @staticmethod
    @abstractmethod
    def create_side_by_side_content(scenario: Scenario, side: str) -> html.Div:
        """
        Create content for one side of the side-by-side comparison view.

        This method generates the content for displaying a single scenario in the
        side-by-side comparison layout. The same method is called twice (once for
        each scenario) with the 'side' parameter indicating which side of the
        comparison is being rendered (typically "left" or "right").

        Args:
            scenario: The Scenario object to display on this side of the comparison.
            side: A string identifier indicating which side of the comparison this is,
                typically "left" or "right". Can be used for styling or layout purposes.

        Returns:
            html.Div: A Dash Div component containing the scenario content for one
                side of the comparison.

        Raises:
            NotImplementedError: Abstract method must be implemented

        Example:
            >>> @staticmethod
            >>> def create_side_by_side_content(scenario, side):
            ...     border_class = "left-border" if side == "left" else "right-border"
            ...     return html.Div([
            ...         html.H4(scenario.name, className="scenario-header"),
            ...         html.Div([
            ...             html.P(f"Status: {scenario.status}"),
            ...             dcc.Graph(figure=scenario.get_figure())
            ...         ])
            ...     ], className=f"compare-panel {border_class}")
        """
        raise NotImplementedError("Abstract method")

    @staticmethod
    @abstractmethod
    def create_compare_section(left: Scenario, right: Scenario) -> html.Div:
        """
        Create a consolidated comparison section for both scenarios.

        This method generates content that directly compares the two scenarios,
        typically highlighting key differences, similarities, or relative metrics.
        It provides a unified view of both scenarios for easy comparison.

        Args:
            left: The Scenario object displayed on the left side of the comparison.
            right: The Scenario object displayed on the right side of the comparison.

        Returns:
            html.Div: A Dash Div component containing the comparison content.

        Raises:
            NotImplementedError: Abstract method must be implemented

        Example:
            >>> @staticmethod
            >>> def create_compare_section(left, right):
            ...     return html.Div([
            ...         html.H3("Quick Comparison"),
            ...         html.Table([
            ...             html.Tr([
            ...                 html.Th("Metric"),
            ...                 html.Th(left.name),
            ...                 html.Th(right.name)
            ...             ]),
            ...             html.Tr([
            ...                 html.Td("Performance"),
            ...                 html.Td(f"{left.performance:.2f}"),
            ...                 html.Td(f"{right.performance:.2f}")
            ...             ])
            ...         ], className="comparison-table")
            ...     ])
        """
        raise NotImplementedError("Abstract method")

    @staticmethod
    @abstractmethod
    def create_details_section(left: Scenario, right: Scenario) -> html.Div:
        """
        Create a detailed analysis section comparing both scenarios.

        This method generates in-depth comparison content, potentially including
        statistical analysis, detailed parameter differences, or comprehensive
        result comparisons. It provides deeper insights beyond the quick comparison
        section.

        Args:
            left: The Scenario object displayed on the left side of the comparison.
            right: The Scenario object displayed on the right side of the comparison.

        Returns:
            html.Div: A Dash Div component containing the detailed comparison content.

        Raises:
            NotImplementedError: Abstract method must be implemented

        Example:
            >>> @staticmethod
            >>> def create_details_section(left, right):
            ...     diff = calculate_differences(left, right)
            ...     return html.Div([
            ...         html.H3("Detailed Analysis"),
            ...         html.Div([
            ...             html.H5("Parameter Differences"),
            ...             html.Ul([
            ...                 html.Li(f"{key}: {diff[key]}")
            ...                 for key in diff.keys()
            ...             ])
            ...         ]),
            ...         html.Div([
            ...             html.H5("Statistical Comparison"),
            ...             dcc.Graph(figure=create_comparison_chart(left, right))
            ...         ])
            ...     ], className="details-section")
        """
        raise NotImplementedError("Abstract method")


class BaseOverviewPage(BasePage, ABC):
    """
    Abstract base class for overview pages in the Algomancy application.

    Overview pages provide a high-level view of multiple scenarios, enabling users
    to browse, filter, and select scenarios for detailed analysis. These pages
    typically display scenario collections in list, grid, or table formats with
    summary information and navigation controls.

    The overview page serves as a central hub for scenario management, allowing
    users to see the big picture of all scenarios and quickly access specific ones.

    Concrete implementations must provide both the content creation method with
    scenarios list parameter and callback registration inherited from BasePage.

    Example:
        >>> class ScenarioOverviewPage(BaseOverviewPage):
        ...     @staticmethod
        ...     def create_content(scenarios):
        ...         return html.Div([
        ...             html.H2(f"All Scenarios ({len(scenarios)})"),
        ...             html.Div([
        ...                 create_scenario_card(scenario)
        ...                 for scenario in scenarios
        ...             ], className="scenario-grid"),
        ...             html.Button("Create New Scenario", id="new-scenario-btn")
        ...         ])
        ...
        ...     @staticmethod
        ...     def register_callbacks():
        ...         @app.callback(...)
        ...         def filter_scenarios():
        ...             pass
        ...
        ...         @app.callback(...)
        ...         def create_new_scenario():
        ...             pass
    """

    @staticmethod
    @abstractmethod
    def create_content(scenarios: List[Scenario]) -> html.Div:
        """
        Create the content for the overview page displaying multiple scenarios.

        This method receives a list of Scenario objects and should return a Dash HTML
        component tree that presents an overview of all scenarios. The content typically
        includes summary information for each scenario, filtering or sorting controls,
        and navigation elements to access individual scenarios.

        Args:
            scenarios: A list of Scenario objects to display in the overview. The list
                may be empty if no scenarios exist.

        Returns:
            html.Div: A Dash Div component containing the overview page layout and content.

        Raises:
            NotImplementedError: Abstract method must be implemented

        Example:
            >>> @staticmethod
            >>> def create_content(scenarios):
            ...     if not scenarios:
            ...         return html.Div([
            ...             html.H3("No scenarios found"),
            ...             html.P("Create your first scenario to get started.")
            ...         ])
            ...
            ...     return html.Div([
            ...         html.H2("Scenario Overview"),
            ...         html.Div([
            ...             html.Label("Filter:"),
            ...             dcc.Dropdown(
            ...                 id="status-filter",
            ...                 options=[{"label": s, "value": s}
            ...                          for s in ["All", "Active", "Completed"]]
            ...             )
            ...         ]),
            ...         html.Table([
            ...             html.Thead(html.Tr([
            ...                 html.Th("Name"),
            ...                 html.Th("Status"),
            ...                 html.Th("Created"),
            ...                 html.Th("Actions")
            ...             ])),
            ...             html.Tbody([
            ...                 html.Tr([
            ...                     html.Td(html.A(s.name, href=f"/scenario/{s.id}")),
            ...                     html.Td(s.status),
            ...                     html.Td(s.created_date),
            ...                     html.Td(html.Button("View", id=f"view-{s.id}"))
            ...                 ]) for s in scenarios
            ...             ])
            ...         ], className="scenario-table")
            ...     ])
        """
        raise NotImplementedError("Abstract method")
