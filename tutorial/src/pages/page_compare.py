from algomancy_scenario import Scenario
from algomancy_content.pages.page import BaseComparePage
from dash import html
import dash_bootstrap_components as dbc
from pages.components import result_table


class TSPComparePage(BaseComparePage):
    @staticmethod
    def create_side_by_side_content(scenario: Scenario, side: str) -> html.Div:
        """
        Create the per-scenario content for the compare page.

        Inputs / assumptions:
        - scenario is a Scenario instance
        - side indicates whether this is the left or right comparison side
          (not used directly in this implementation)

        Output:
        - html.Div containing a result summary table for the scenario
        """
        results = result_table(scenario)
        return html.Div(dbc.Container([results]))

    @staticmethod
    def create_compare_section(left: Scenario, right: Scenario) -> html.Div:
        """
        Create a comparison summary between two completed scenarios.

        Computes simple similarities and differences between scenario results,
        including overlapping route segments and the most expensive route used.

        Inputs / assumptions:
        - left and right are Scenario instances with existing tours
        - Route IDs uniquely identify comparable route segments

        Output:
        - html.Div containing textual comparison metrics
        """
        tour_left = getattr(getattr(left, "result", None), "tour", []) or []
        tour_right = getattr(getattr(right, "result", None), "tour", []) or []

        common_route_ids = {r.route_id for r in tour_left} & {r.route_id for r in tour_right}
        number_of_common_routes = len(common_route_ids)

        # Most expensive route segment used:
        all_routes = tour_left + tour_right
        if all_routes:
            highest = max(all_routes, key=lambda r: r.cost)
            highest_cost_id = highest.route_id
            highest_cost = highest.cost
        else:
            highest_cost_id = ''
            highest_cost = 0

        # Determine where highest cost occurs
        left_ids = {r.route_id for r in tour_left}
        right_ids = {r.route_id for r in tour_right}

        used_in = (
            "both" if (highest_cost_id in left_ids and highest_cost_id in right_ids)
            else "left only" if (highest_cost_id in left_ids)
            else "right only"
        )

        return html.Div([
            html.Div(f"Number of common route segments: {number_of_common_routes}"),
            html.Div(f"Highest cost route is {highest_cost_id} at ${highest_cost:.1f}, used in {used_in}")
        ],
            style={"marginTop": "12px", "marginBottom": "12px"},
        )


    @staticmethod
    def create_details_section(left: Scenario, right: Scenario) -> html.Div:
        """
        Create a simple details section displaying identifiers of both scenarios.

        Inputs / assumptions:
        - left and right are Scenario instances
        - Each scenario exposes an 'id' attribute

        Output:
        - html.Div containing basic scenario identification details
        """
        return html.Div([
            html.Div(f"Left scenario id: {left.id}"),
            html.Div(f"Right scenario id: {right.id}"),
        ],
            style={"marginTop": "12px", "marginBottom": "12px"},
        )

    @staticmethod
    def register_callbacks() -> None:
        return None
