from algomancy_gui.managergetters import get_manager
from algomancy_gui.sessionmanager import SessionManager
from algomancy_gui.settingsmanager import SettingsManager
import dash_bootstrap_components as dbc
from dash import html, get_app, dcc
from typing import Dict

from algomancy_scenario import ScenarioManager
from algomancy_utils.baseparameterset import (
    TypedParameter,
    ParameterType,
    BaseParameterSet,
)
from algomancy_gui.componentids import (
    ALGO_PARAMS_ENTRY_CARD,
    ALGO_PARAMS_ENTRY_TAB,
    ALGO_PARAMS_UPLOAD_TAB,
    ALGO_PARAMS_WINDOW_ID,
    ALGO_PARAM_INPUT,
    ALGO_PARAM_DATE_INPUT,
    ALGO_PARAM_INTERVAL_INPUT,
)


def prettify_label(key):
    # Converts 'batch_size' -> 'Batch Size'
    return key.replace("_", " ").title()


def create_parameter_input_component(param: TypedParameter, param_name: str):
    typ = param.parameter_type
    match typ:
        case ParameterType.STRING:
            return dbc.Input(
                id={"type": ALGO_PARAM_INPUT, "param": param_name}, type="text"
            )
        case ParameterType.INTEGER:
            return dbc.Input(
                id={"type": ALGO_PARAM_INPUT, "param": param_name}, type="number"
            )
        case ParameterType.FLOAT:
            return dbc.Input(
                id={"type": ALGO_PARAM_INPUT, "param": param_name}, type="number"
            )
        case ParameterType.BOOLEAN:
            return dbc.Checklist(
                options=[{"label": "On", "value": True}],
                id={"type": ALGO_PARAM_INPUT, "param": param_name},
                switch=True,
            )
        case ParameterType.ENUM:
            return dcc.Dropdown(
                id={"type": ALGO_PARAM_INPUT, "param": param_name},
                options=[
                    {"label": prettify_label(opt), "value": opt}
                    for opt in param.choices
                ],
            )
        case ParameterType.MULTI_ENUM:
            return dcc.Dropdown(
                id={"type": ALGO_PARAM_INPUT, "param": param_name},
                options=[
                    {"label": prettify_label(opt), "value": opt}
                    for opt in param.choices
                ],
                multi=True,
            )
        case ParameterType.TIME:
            return dcc.DatePickerSingle(
                id={"type": ALGO_PARAM_DATE_INPUT, "param": param_name},
                date=param.default,
            )
        case ParameterType.INTERVAL:
            return dcc.DatePickerRange(
                id={"type": ALGO_PARAM_INTERVAL_INPUT, "param": param_name},
                start_date=param.default_start,
                end_date=param.default_end,
            )
        case _:
            raise ValueError(f"Unsupported parameter type: {typ}")


def create_input_group(param_dict: Dict[str, TypedParameter]):
    """
    Given a dictionary of parameter names and Python types,
    returns a list of input groups, each with a neat label and input.
    """
    form_groups = []
    for param_name, param in param_dict.items():
        label = prettify_label(param_name)

        html_id = f"{ALGO_PARAM_INPUT}-{param_name}"

        component = create_parameter_input_component(param, param_name)

        form_groups.append(
            html.Div(
                [
                    dbc.Label(label, html_for=html_id, className="d-block"),
                    html.Div(
                        component,
                        className="",
                        style={"display": "block", "width": "100%"},
                    ),
                ],
                className="mb-3",
            )
        )

    return form_groups


def create_algo_parameters_entry_card_body(template_name: str) -> dbc.CardBody:
    session_manager: SessionManager | ScenarioManager = get_manager(get_app().server)
    algo_params: BaseParameterSet = session_manager.get_algorithm_parameters(
        template_name
    )
    assert algo_params.has_inputs(), "No parameters found for algorithm template."
    input_group = create_input_group(algo_params.get_parameters())

    return dbc.CardBody(
        input_group,
        style={
            "maxHeight": "60vh",  # or e.g. "420px"
            "overflowY": "auto",
            "overflowX": "hidden",
        },
    )


def create_algo_parameters_window() -> dbc.Collapse:
    tabs = []

    param_entry_card = dbc.Card(id=ALGO_PARAMS_ENTRY_CARD, class_name="mt-3")
    tabs.append(
        dbc.Tab(param_entry_card, label="Fill in", tab_id=ALGO_PARAMS_ENTRY_TAB)
    )

    settings: SettingsManager = get_app().server.settings
    if settings.allow_param_upload_by_file:
        param_upload_card = dbc.Card(
            dbc.CardBody(html.Strong("TO DO: file uploader.")), class_name="mt-3"
        )
        tabs.append(
            dbc.Tab(param_upload_card, label="Upload", tab_id=ALGO_PARAMS_UPLOAD_TAB)
        )

    window = dbc.Collapse(
        children=[dbc.Tabs(tabs)],
        id=ALGO_PARAMS_WINDOW_ID,
        is_open=False,
    )

    return window
