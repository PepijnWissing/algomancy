(tutorial-pages-ref)=
# Pages
Now that the backend is complete, we can create the GUI elements. 
We build our own implementation of the Scenarios page, the Compare page and the Overview page.
Algomancy uses Plotly Dash for the GUI, and in this tutorial we will make use of components in the [Dash Core Components](https://dash.plotly.com/dash-core-components) and the [Dash Bootstrap Components](https://www.dash-bootstrap-components.com/) libraries. 

## Scenarios Page
In the scenarios pages, we will show basic information about the scenario. Additionally, if the algorithm has run, we will show some result statistics and visualize the TSP route.  
1. Create a file `page_scenarios.py `in the directory `src/pages/`
2. Create the class TSPScenarioPage which inherits from the BaseScenarioPage, and implements the static methods `register_callbacks` and `create_content`, using the code below:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `page_scenarios.py`
:linenos:

from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from algomancy_content.pages.page import BaseScenarioPage
from algomancy_scenario import Scenario, ScenarioStatus

class TSPScenarioPage(BaseScenarioPage):
    @staticmethod
    def register_callbacks():
    pass


    @staticmethod
    def create_content(scenario: Scenario) -> html.Div:
    pass
```
:::

3. We will create several visualization components which we want to use on different pages. For this, create a file `components.py` in the directory `src/pages/`.
4. In this file, we create two components: a table with information about a scenario and a table with results:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `components.py`
:linenos:

from dash import html
import dash_bootstrap_components as dbc
from algomancy_gui.scenario_page.scenario_badge import status_badge
from typing import List, Dict


def scenario_table(scenario) -> html.Div:
    """
    Render a summary table with high-level scenario metadata.

    Inputs / assumptions:
    - scenario has the following attributes:
        - id
        - tag
        - status
        - algorithm_description
        - input_data_key
    - Missing attributes are rendered as an em dash ("—")

    Output:
    - html.Div containing a Bootstrap card with a metadata table
    """
    rows = [
        html.Tr([html.Th("ID"), html.Td(str(getattr(scenario, "id", "—")))]),
        html.Tr([html.Th("Tag"), html.Td(getattr(scenario, "tag", "—") or "—")]),
        html.Tr([
            html.Th("Status"),
            html.Td(
                status_badge(getattr(scenario, "status", "—"))
            )
        ]),
        html.Tr([html.Th("Algorithm"),
                 html.Td(getattr(scenario, "algorithm_description", "—") or "—")]),
        html.Tr([html.Th("Dataset"),
                 html.Td(getattr(scenario, "input_data_key", "—") or "—")]),
    ]

    return html.Div(dbc.Card(
        [
            dbc.CardHeader("Selected Scenario"),
            dbc.CardBody(
                dbc.Table(
                    [html.Tbody(rows)],
                )
            ),
        ]
    ))

def result_table(scenario) -> html.Div:
    """
    Render a KPI summary table for a completed scenario.

    Inputs / assumptions:
    - scenario.result contains:
        - ordered_locations (list)
        - tour (list)
    - scenario.kpis contains:
        - "Total_costs" with attribute `.value`
    - Missing data is rendered as zero or em dash

    Output:
    - html.Div containing a Bootstrap card with result KPIs
    """
    ordered_locations = getattr(getattr(scenario, "result", None), "ordered_locations", []) or []
    tour = getattr(getattr(scenario, "result", None), "tour", []) or []

    # KPI calculations (as provided)
    total_cost = round(getattr(scenario.kpis.get("Total_costs", None), "value", 0.0), 1) if getattr(scenario, "kpis", None) else 0.0
    number_of_routes = len(tour)
    avg_cost = round(total_cost / number_of_routes, 1) if number_of_routes > 0 else 0.0

    rows = [
        html.Tr([html.Th("Total cost"), html.Td(f"{total_cost}")]),
        html.Tr([html.Th("Number of locations"), html.Td(f"{len(ordered_locations)}")]),
        html.Tr([html.Th("Number of route segments"), html.Td(f"{number_of_routes}")]),
        html.Tr([html.Th("Average cost per segment"), html.Td(f"{avg_cost}")]),
    ]

    return html.Div(
        dbc.Card(
            [
                dbc.CardHeader("Result Summary"),
                dbc.CardBody(
                    dbc.Table(
                        [html.Tbody(rows)]
                    )
                ),
            ]
        )
    )
```
:::

Note that we re-used Algomancy's `status_badge` component. 

5. In `page_scenarios.py`, import these components and use them in the `create_content` function as follows:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `page_scenarios.py`
:linenos:
:lineno-start: 12
@staticmethod
def create_content(scenario: Scenario) -> html.Div:
    # Case 1 – Scenario not ready
    if scenario.status != ScenarioStatus.COMPLETE:
        unavailable_page = dbc.Container([dbc.Row(
            [
                dbc.Col(scenario_table(scenario)),
                dbc.Col(html.Div([
                    dbc.Alert("Scenario results are not available yet. Please run the scenario or refresh "
                              "the page once the computation is complete.",
                              color="info")
                ],
                    style={"paddingTop": "4px"})
                )
            ]
        )
        ])
        return html.Div(unavailable_page)

    # Case 2 – Scenario finished: extract results
    ordered_locations = scenario.result.ordered_locations
    tour = scenario.result.tour

    locations_payload = [
        {"id": loc.id, "x": float(loc.x), "y": float(loc.y)}
        for loc in ordered_locations
    ]
    tour_payload = [
        {
            "from_id": r.from_id,
            "to_id": r.to_id,
            "route_id": r.route_id,
            "cost": float(getattr(r, "cost", 0.0)),
        }
        for r in tour
    ]

    # Construct page
    result_page = dbc.Container([
        dbc.Row(
            [
                dbc.Col(
                    # Scenario info
                    scenario_table(scenario)
                    ),
                dbc.Col(
                    # Key statistics
                    result_table(scenario)
                ))
            ])
    ])
    return html.Div(result_page)
```
:::

In the just created page, we check if the scenario has already run. If yes, we show the results. If not, we show a
notification to the user.

6. Next, we want to add a visualization of the resulting route to the page. In the file `components.py`, add the following import statement:
```{code-block} python
import plotly.graph_objects as go
```
and add the following function:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `components.py`
:linenos:
:lineno-start: 94
def route_visualization(ordered_locations: List[Dict], tour: List[Dict]):
    """
    Create a Plotly figure visualizing a TSP route.

    Inputs / assumptions:
    - ordered_locations: list of dicts with keys:
        - "id", "x", "y"
    - tour: list of dicts with keys:
        - "from_id", "to_id", "route_id", "cost"
    - Location IDs referenced in tour exist in ordered_locations
      (missing IDs should be handled or skipped by the caller)

    Output:
    - plotly.graph_objects.Figure showing route segments and locations
    """
    # Lookup table for coordinates
    loc_lookup = {loc['id']: (loc['x'], loc['y']) for loc in ordered_locations}

    # Location coordinates for convenience
    xs = [loc['x'] for loc in ordered_locations]
    ys = [loc['y'] for loc in ordered_locations]

    # Data bounds
    if not xs or not ys:
        x_min = y_min = 0.0
        x_max = y_max = 1.0
    else:
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

    x_span = max(1e-9, x_max - x_min)
    y_span = max(1e-9, y_max - y_min)

    # Create figure
    fig = go.Figure()
    LINE_COLOR = "#0074D9"
    
    # Plot route segments one by one
    for route in tour:
        try:
            x0, y0 = loc_lookup[route["from_id"]]
            x1, y1 = loc_lookup[route["to_id"]]
        except KeyError:
            continue

        # Draw segment
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(width=3, color=LINE_COLOR),
                showlegend=False,
            )
        )

        # Plot edge labels at midpoint of line
        xm = (x0 + x1) / 2.0
        ym = (y0 + y1) / 2.0

        fig.add_annotation(
            x=xm,
            y=ym,
            text=f"{route['route_id']}<br>Cost: {route['cost']:.1f}",
            showarrow=False,
            font=dict(size=11, color="#222"),
            align="center",
            xanchor="center",
            yanchor="middle",
            bgcolor="rgba(255,255,255,0.65)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1,
            borderpad=3,
        )

    # Scatter plot Locations
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(size=9, color="#111111"),
            text=[loc['id'] for loc in ordered_locations],
            hovertemplate="<b>Location:</b> %{text}<extra></extra>",
            showlegend=False,
        )
    )

    # Layout styling
    fig.update_layout(
        xaxis_title="X",
        yaxis_title="Y",
        hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)",  # transparent background
        plot_bgcolor="rgba(0,0,0,0)"  # transparent plotting area
    )

    # Tight axes with small padding
    x_pad = 0.05 * x_span
    y_pad = 0.05 * y_span
    fig.update_xaxes(range=[x_min - x_pad, x_max + x_pad], zeroline=True, showgrid=True)
    fig.update_yaxes(range=[y_min - y_pad, y_max + y_pad], zeroline=True, showgrid=True)

    return fig
```
:::
7. In `page_scenarios.py` we want to give the user the option to toggle the visualization on/off. Import the `route_visualization` function from `components.py` and edit the `create_content` 
function such that it looks as follows:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `page_scenarios.py`
:linenos:
:lineno-start: 12
def create_content(scenario: Scenario) -> html.Div:
    """
    Create the main content of the scenario page.

    Renders basic scenario metadata and either a notification (if the scenario is not complete) or result statistics
    and visualization controls.

    Inputs / assumptions:
    - scenario has attributes:
        - status
        - result.ordered_locations
        - result.tour
        - kpis (optional)
    - ScenarioStatus.COMPLETE indicates a finished scenario

    Output:
    - html.Div containing the full page layout for the scenario
    """
    # Case 1 – Scenario not ready
    if scenario.status != ScenarioStatus.COMPLETE:
        unavailable_page = dbc.Container([dbc.Row(
            [
                dbc.Col(scenario_table(scenario)),
                dbc.Col(html.Div([
                    dbc.Alert("Scenario results are not available yet. Please run the scenario or refresh "
                              "the page once the computation is complete.",
                              color="info")
                ],
                    style={"paddingTop": "4px"})
                )
            ]
        )
        ])
        return html.Div(unavailable_page)

    # Case 2 – Scenario finished: extract results
    ordered_locations = scenario.result.ordered_locations
    tour = scenario.result.tour

    locations_payload = [
        {"id": loc.id, "x": float(loc.x), "y": float(loc.y)}
        for loc in ordered_locations
    ]
    tour_payload = [
        {
            "from_id": r.from_id,
            "to_id": r.to_id,
            "route_id": r.route_id,
            "cost": float(getattr(r, "cost", 0.0)),
        }
        for r in tour
    ]

    # Construct page
    result_page = dbc.Container([
        dbc.Row(
            [
                dbc.Col(scenario_table(scenario)),
                dbc.Col(html.Div([
                    # Key statistics
                    result_table(scenario),

                    # Toggle visualization on/off
                    dbc.Checklist(
                        id="show-route",
                        options=[{"label": " Show visualization", "value": "show"}],
                        value=["show"],  # default: visible
                        switch=True,
                        style={"marginTop": "8px", "marginBottom": "8px"},
                    )
                ]))
            ]),
        dbc.Row(
            [
                html.Div([
                    html.Hr(),
                    dcc.Store(
                        id='locations_store', data=locations_payload
                    ),
                    dcc.Store(
                        id='tour_store', data=tour_payload
                    ),
                    html.Div(id="route-container")
                ]
                )
            ]
        )
    ])
    return html.Div(result_page)
```
:::

8. We have now created an on/off toggle for the visualization, but it is not responsive yet. We must implement the `register_callbacks()` function to listen to the `route-container` toggle:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `page_scenarios.py`
:linenos:
:lineno-start: 10
@staticmethod
def register_callbacks():
    """
    Conditionally render the route visualization based on user input.

    Inputs / assumptions:
    - values: list of selected values from the 'show-route' checklist
    - ordered_locations: data from dcc.Store, passed to route_visualization
    - tour: data from dcc.Store, passed to route_visualization

    Output:
    - html.Div with a message if hidden, or
    - dcc.Graph containing the route visualization
    """
    @callback(
        Output("route-container", "children"),
        Input("show-route", "value"),
        State("locations_store", "data"),
        State("tour_store", "data"),
    )
    def render_route(values, ordered_locations, tour):
        show = "show" in (values or [])
        if not show:
            return html.Div("Visualization is hidden.", style={"opacity": 0.7, "fontStyle": "italic"})
        return dcc.Graph(id="route", figure=route_visualization(ordered_locations, tour),
                         style={"height": "58vh"})
```
:::

9. Lastly, we must change the app configuration to use our newly created page. In `main.py` import the TSPScenarioPage 
class using `from pages.page_scenarios import TSPScenarioPage`, and in the AppConfiguration instance initialization 
use the argument `scenario_page=TSPScenarioPage()`.
10. Start the application, load the data and create a new scenario on the Scenarios page. 
Verify that you see the page that has just been created.

## Compare Page
On the compare page, we can perform a more detailed comparison between two scenarios. 
On our TSPComparePage we will show the results of two scenarios side by side, and display some similarities/differences.  

1. Create a file `page_compare.py `in the directory `src/pages/`
2. Create the class TSPComparePage which inherits from the BaseComparePage, and implements the static methods
`create_side_by_side_content`, `create_compare_section`, `create_details_section` and `register_callbacks` using the code below:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `page_compare.py`
:linenos:

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
        pass


    @staticmethod
    def create_details_section(left: Scenario, right: Scenario) -> html.Div:
        pass

    @staticmethod
    def register_callbacks() -> None:
        return None
```
:::

Note that for the side-by-side content we have re-used the result table which was also on the scenarios page.
By placing it in the `create_side_by_side_content` it is shown for both selected scenarios side by side.

3. In the `create_compare_section` and `create_details_section` we have access to a `left` and `right` scenario. 
With the following code block we implement a comparison in the compare section and show the scenario IDs in the details section:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `page_compare.py`
:linenos:

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
            style={"marginTop": "8px"},
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
            style={"marginTop": "8px"},
        )
```
:::

4. If desired, you can also add interactivity by adding callbacks to the `register_callbacks` function, in the same way as this was done on the TSP scenarios page.
5. Similar to the TSPScenarioPage, also import the TSPComparePage in `main.py` and provide it as input to the app configuration.

## Overview Page
On the overview page, we have access to all scenarios at the same time. For TSPOverviewPage, we will create a table 
with all scenarios, and show basic info and the resulting total cost for each scenario.

1. Create a file `page_overview.py `in the directory `src/pages/`
2. Create the class TSPOverviewPage which inherits from the BaseOverviewPage, and implements the static methods
`create_content` and `register_callbacks` using the code below:

:::{dropdown} {octicon}`code` Code
:color: info
```{code-block} python
:caption: `page_overview.py`
:linenos:
from algomancy_scenario import Scenario
from algomancy_scenario import ScenarioStatus
from algomancy_content.pages.page import BaseOverviewPage
from algomancy_gui.scenario_page.scenario_badge import status_badge

from typing import List
import dash_bootstrap_components as dbc
from dash import html

class TSPOverviewPage(BaseOverviewPage):
    @staticmethod
    def create_content(scenarios: List[Scenario]) -> html.Div:
        """
        Create an overview table summarizing multiple scenarios.

        Inputs / assumptions:
        - scenarios is a list of Scenario objects
        - Each scenario defines:
            - tag
            - status
            - input_data_key
            - algorithm_description
            - kpis["Total_costs"].value (only if COMPLETE)

        Output:
        - html.Div containing a Bootstrap card with a summary table, or an alert message if no scenarios are provided
        """  
        # Empty-state
        if not scenarios:
            return html.Div(
                dbc.Alert("No scenarios to display.", color="info")
            )

        header = html.Thead(
            html.Tr(
                [
                    html.Th("Scenario"),
                    html.Th("Status"),
                    html.Th("Dataset"),
                    html.Th("Algorithm",
                    html.Th("Total cost"),
                ]
            )
        )

        body_rows = []
        for s in scenarios:
            tag = getattr(s, "tag", None)
            status = getattr(s, "status", "—")
            dataset = getattr(s, "input_data_key", None)
            algo = getattr(s, "algorithm_description", None)

            if (status == ScenarioStatus.COMPLETE) and (getattr(s, "kpis", None)):
                cost = getattr(s.kpis.get("Total_costs", None), "value", 0.0)
                cost_txt = f"{cost:.1f}"
            else:
                cost_txt = "—"

            body_rows.append(
                html.Tr(
                    [
                        html.Td(tag),
                        html.Td(status_badge(status)),
                        html.Td(dataset),
                        html.Td(algo),
                        html.Td(cost_txt),
                    ]
                )
            )

        table = dbc.Table(
            [header, html.Tbody(body_rows)],
        )

        return html.Div(
            dbc.Card(
                [
                    dbc.CardHeader("Scenarios"),
                    dbc.CardBody(table),
                ],
                className="shadow-sm",
            )
        )

    @staticmethod
    def register_callbacks():
        return None
```
:::

2. If desired, you can also add interactivity by adding callbacks to the `register_callbacks` function, in the same way as this was done on the TSP scenarios page.
3. Similar to the previous pages, import the TSPOverviewPage in `main.py` and provide it as input to the app configuration.

The created pages can be further customized to your preferences.