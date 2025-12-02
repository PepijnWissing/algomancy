import dash_bootstrap_components as dbc
from dash import html, get_app, dcc
from typing import Dict

from dash_bootstrap_components import CardBody

from algomancy.scenarioengine import ScenarioManager
from algomancy.scenarioengine.basealgorithmparameters import TypedParameter, ParameterType
from algomancy.components.componentids import (
    ALGO_PARAMS_ENTRY_CARD,
    ALGO_PARAMS_ENTRY_TAB,
    ALGO_PARAMS_UPLOAD_TAB,
    ALGO_PARAMS_WINDOW_ID,
    ALGO_PARAM_INPUT,
)


def prettify_label(key):
    # Converts 'batch_size' -> 'Batch Size'
    return key.replace('_', ' ').title()


def create_parameter_input_component(param: TypedParameter, input_id: Dict[str, str]):
    typ = param.parameter_type
    match typ:
        case ParameterType.STRING:
            return dbc.Input(id=input_id, type="text")
        case ParameterType.INTEGER:
            return dbc.Input(id=input_id, type="number")
        case ParameterType.FLOAT:
            return dbc.Input(id=input_id, type="number")
        case ParameterType.BOOLEAN:
            return dbc.Checklist(
                options=[{'label': 'On', 'value': True}],
                id=input_id,
                switch=True
            )
        case ParameterType.ENUM:
            return dcc.Dropdown(
                id=input_id,
                options=[{"label": prettify_label(opt), "value": opt} for opt in param.choices],
            )
        case _:
            raise ValueError(f"Unsupported parameter type: {typ}")


def create_input_group(param_dict: Dict[str, TypedParameter]):
    """
    Given a dictionary of parameter names and Python types,
    returns a list of input groups, each with a neat label and input.
    The id of each input is f"{id_prefix}-{key}".
    """
    form_groups = []
    for param_name, param in param_dict.items():
        label = prettify_label(param_name)

        input_id = {'type': ALGO_PARAM_INPUT, 'param': param_name}
        html_id = f"{ALGO_PARAM_INPUT}-{param_name}"

        component = create_parameter_input_component(param, input_id)

        form_groups.append(
            html.Div([
                dbc.Label(label, html_for=html_id),
                component
            ], className="mb-3")
        )

    return form_groups


def create_algo_parameters_entry_card_body(template_name: str) -> CardBody:
    sm: ScenarioManager = get_app().server.scenario_manager
    algo_params = sm.get_algorithm_parameters(template_name)
    assert algo_params.has_inputs(), "No parameters found for algorithm template."
    input_group = create_input_group(algo_params.get_parameters())

    return dbc.CardBody(
        input_group
    )


def create_algo_parameters_window() -> dbc.Collapse:
    param_entry_card = dbc.Card(
        id=ALGO_PARAMS_ENTRY_CARD,
        class_name="mt-3"
    )

    param_upload_card = dbc.Card(
        dbc.CardBody(
            html.Strong("TO DO: file uploader.")
        ),
        class_name="mt-3"
    )

    window = dbc.Collapse(
        children=[
            dbc.Tabs([
                dbc.Tab(param_entry_card, label="Fill in", tab_id=ALGO_PARAMS_ENTRY_TAB),
                dbc.Tab(param_upload_card, label="Upload", tab_id=ALGO_PARAMS_UPLOAD_TAB),
            ])
        ],
        id=ALGO_PARAMS_WINDOW_ID,
        is_open=False,
    )

    return window
