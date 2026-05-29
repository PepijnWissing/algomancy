"""Algorithm + KPI discovery endpoints.

Frontends need three things to render the scenario-creation UI:

1. The list of algorithm names available in this session's manager.
2. The parameter shape of a chosen algorithm (types, defaults, bounds, choices).
3. The list of KPI templates the manager will compute for every scenario.

All three are session-scoped because algorithm and KPI templates are bound to
the ScenarioManager. In practice they are identical across sessions today, but
the URL stays consistent with the rest of the API.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from algomancy_scenario import ScenarioManager

from ..dependencies import get_scenario_manager
from ..parameter_describer import describe_parameter_set
from ..schemas import AlgorithmsListResponse, KpisListResponse


router = APIRouter(
    prefix="/sessions/{session_id}",
    tags=["algorithms"],
)


@router.get(
    "/algorithms",
    response_model=AlgorithmsListResponse,
    summary="List available algorithm names",
)
def list_algorithms(
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> AlgorithmsListResponse:
    return AlgorithmsListResponse(algorithms=list(sm.available_algorithms))


@router.get(
    "/algorithms/{algorithm_name}/parameters",
    summary="Describe an algorithm's parameter shape",
    response_model=dict,
)
def get_algorithm_parameters(
    algorithm_name: str,
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> dict:
    if algorithm_name not in sm.available_algorithms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algorithm '{algorithm_name}' not found",
        )
    params = sm.get_algorithm_parameters(algorithm_name)
    return describe_parameter_set(params)


@router.get(
    "/kpis",
    response_model=KpisListResponse,
    summary="List configured KPI template names",
)
def list_kpis(
    sm: ScenarioManager = Depends(get_scenario_manager),
) -> KpisListResponse:
    return KpisListResponse(kpis=list(sm.available_kpis))
